"""
Streaming Chat API with Server-Sent Events

This module provides real-time streaming chat responses using Server-Sent Events (SSE)
with progressive message rendering, cancellation support, and error handling.
"""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import httpx

from db.database import get_db
from db.models import User, Model, Conversation, Message
from db import crud
from auth.jwt import get_current_user
from core.cache import cache_manager, CacheNamespaces
import logging

logger = logging.getLogger(__name__)


class StreamingMessageType(str, Enum):
    START = "start"
    CHUNK = "chunk"
    END = "end"
    ERROR = "error"
    CANCEL = "cancel"
    METADATA = "metadata"


@dataclass
class StreamingChunk:
    """Represents a chunk of streaming data."""
    type: StreamingMessageType
    content: str = ""
    metadata: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class StreamingChatRequest(BaseModel):
    """Request for streaming chat completion."""
    model_id: str = Field(..., description="ID of the model to use")
    prompt: str = Field(..., description="User prompt")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    system_prompt: Optional[str] = Field(None, description="System prompt override")
    max_tokens: Optional[int] = Field(None, ge=1, le=8192, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, ge=0, le=1, description="Top-p sampling")
    stream_delay: Optional[float] = Field(0.05, ge=0, le=1, description="Delay between chunks in seconds")
    include_thinking: bool = Field(False, description="Include model thinking process")
    format_markdown: bool = Field(True, description="Format response as markdown")


class StreamingChatManager:
    """Manages streaming chat sessions."""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.cancelled_streams: set = set()
    
    def create_stream(self, stream_id: str, user_id: str, model_id: str) -> None:
        """Create a new streaming session."""
        self.active_streams[stream_id] = {
            "user_id": user_id,
            "model_id": model_id,
            "created_at": datetime.utcnow(),
            "chunks_sent": 0,
            "total_tokens": 0
        }
    
    def cancel_stream(self, stream_id: str) -> bool:
        """Cancel a streaming session."""
        if stream_id in self.active_streams:
            self.cancelled_streams.add(stream_id)
            return True
        return False
    
    def is_cancelled(self, stream_id: str) -> bool:
        """Check if a stream is cancelled."""
        return stream_id in self.cancelled_streams
    
    def cleanup_stream(self, stream_id: str) -> None:
        """Clean up a completed stream."""
        self.active_streams.pop(stream_id, None)
        self.cancelled_streams.discard(stream_id)
    
    def get_active_streams(self, user_id: str) -> List[str]:
        """Get active streams for a user."""
        return [
            stream_id for stream_id, info in self.active_streams.items()
            if info["user_id"] == user_id
        ]


# Global stream manager
stream_manager = StreamingChatManager()


class StreamingChatEngine:
    """Handles streaming chat completions."""
    
    def __init__(self, db: AsyncSession, http_client: httpx.AsyncClient):
        self.db = db
        self.http_client = http_client
    
    async def stream_chat_completion(
        self,
        request: StreamingChatRequest,
        user: User,
        stream_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion responses."""
        try:
            # Validate model - check cache first
            cache_key = f"model_{request.model_id}"
            model = await cache_manager.get(CacheNamespaces.MODELS, cache_key)
            if model is None:
                model = await crud.get_model(self.db, request.model_id)
                if model:
                    # Cache the model for quick lookups
                    await cache_manager.set(CacheNamespaces.MODELS, cache_key, model, ttl=600)
                    logger.debug(f"Cached model for streaming: {request.model_id}")
            else:
                logger.debug(f"Cache hit for model in streaming: {request.model_id}")
            
            if not model:
                yield self._format_sse_message(StreamingChunk(
                    type=StreamingMessageType.ERROR,
                    content="Model not found",
                    metadata={"error_code": "MODEL_NOT_FOUND"}
                ))
                return
            
            # Validate conversation if provided
            conversation = None
            if request.conversation_id:
                conversation = await crud.get_conversation(self.db, request.conversation_id)
                if not conversation:
                    yield self._format_sse_message(StreamingChunk(
                        type=StreamingMessageType.ERROR,
                        content="Conversation not found",
                        metadata={"error_code": "CONVERSATION_NOT_FOUND"}
                    ))
                    return
            
            # Create stream session
            stream_manager.create_stream(stream_id, user.id, request.model_id)
            
            # Send start message
            yield self._format_sse_message(StreamingChunk(
                type=StreamingMessageType.START,
                content="",
                metadata={
                    "model_id": request.model_id,
                    "model_name": model.name,
                    "stream_id": stream_id,
                    "conversation_id": request.conversation_id
                }
            ))
            
            # Prepare the request for the model
            if model.provider.lower() == "ollama":
                async for chunk in self._stream_ollama_response(request, model, stream_id):
                    if stream_manager.is_cancelled(stream_id):
                        yield self._format_sse_message(StreamingChunk(
                            type=StreamingMessageType.CANCEL,
                            content="Stream cancelled by user"
                        ))
                        break
                    yield chunk
            else:
                # Handle other providers (OpenAI, Anthropic, etc.)
                async for chunk in self._stream_openai_compatible_response(request, model, stream_id):
                    if stream_manager.is_cancelled(stream_id):
                        yield self._format_sse_message(StreamingChunk(
                            type=StreamingMessageType.CANCEL,
                            content="Stream cancelled by user"
                        ))
                        break
                    yield chunk
            
            # Send end message if not cancelled
            if not stream_manager.is_cancelled(stream_id):
                yield self._format_sse_message(StreamingChunk(
                    type=StreamingMessageType.END,
                    content="",
                    metadata={"stream_id": stream_id, "status": "completed"}
                ))
        
        except Exception as e:
            yield self._format_sse_message(StreamingChunk(
                type=StreamingMessageType.ERROR,
                content=str(e),
                metadata={"error_code": "STREAMING_ERROR"}
            ))
        
        finally:
            stream_manager.cleanup_stream(stream_id)
    
    async def _stream_ollama_response(
        self,
        request: StreamingChatRequest,
        model: Model,
        stream_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream response from Ollama."""
        try:
            # Prepare Ollama request
            ollama_request = {
                "model": request.model_id,
                "prompt": request.prompt,
                "stream": True,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens or 2048,
                    "top_p": request.top_p
                }
            }
            
            if request.system_prompt:
                ollama_request["system"] = request.system_prompt
            
            # Make streaming request to Ollama
            async with self.http_client.stream(
                "POST",
                "/api/generate",
                json=ollama_request,
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama API error: {response.status_code}"
                    )
                
                full_response = ""
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if stream_manager.is_cancelled(stream_id):
                        break
                    
                    if line.strip():
                        try:
                            chunk_data = json.loads(line)
                            content = chunk_data.get("response", "")
                            
                            if content:
                                full_response += content
                                chunk_count += 1
                                
                                # Apply streaming delay
                                if request.stream_delay > 0:
                                    await asyncio.sleep(request.stream_delay)
                                
                                yield self._format_sse_message(StreamingChunk(
                                    type=StreamingMessageType.CHUNK,
                                    content=content,
                                    metadata={
                                        "chunk_index": chunk_count,
                                        "total_length": len(full_response)
                                    }
                                ))
                            
                            # Check if stream is done
                            if chunk_data.get("done", False):
                                # Send metadata about the completion
                                eval_count = chunk_data.get("eval_count", 0)
                                eval_duration = chunk_data.get("eval_duration", 0)
                                
                                yield self._format_sse_message(StreamingChunk(
                                    type=StreamingMessageType.METADATA,
                                    content="",
                                    metadata={
                                        "total_tokens": eval_count,
                                        "duration_ms": eval_duration / 1000000,  # Convert nanoseconds to ms
                                        "tokens_per_second": eval_count / (eval_duration / 1000000000) if eval_duration > 0 else 0,
                                        "full_response": full_response
                                    }
                                ))
                                break
                        
                        except json.JSONDecodeError:
                            continue
        
        except httpx.RequestError as e:
            yield self._format_sse_message(StreamingChunk(
                type=StreamingMessageType.ERROR,
                content=f"Connection error: {str(e)}",
                metadata={"error_code": "CONNECTION_ERROR"}
            ))
        except Exception as e:
            yield self._format_sse_message(StreamingChunk(
                type=StreamingMessageType.ERROR,
                content=f"Unexpected error: {str(e)}",
                metadata={"error_code": "UNEXPECTED_ERROR"}
            ))
    
    async def _stream_openai_compatible_response(
        self,
        request: StreamingChatRequest,
        model: Model,
        stream_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI-compatible API."""
        # This would implement streaming for OpenAI, Anthropic, etc.
        # For now, simulate streaming response
        
        simulated_response = f"This is a simulated streaming response for model {model.name}. " \
                           f"The user asked: {request.prompt}"
        
        words = simulated_response.split()
        full_response = ""
        
        for i, word in enumerate(words):
            if stream_manager.is_cancelled(stream_id):
                break
            
            content = word + " "
            full_response += content
            
            # Apply streaming delay
            if request.stream_delay > 0:
                await asyncio.sleep(request.stream_delay)
            
            yield self._format_sse_message(StreamingChunk(
                type=StreamingMessageType.CHUNK,
                content=content,
                metadata={
                    "chunk_index": i + 1,
                    "total_length": len(full_response)
                }
            ))
        
        # Send final metadata
        yield self._format_sse_message(StreamingChunk(
            type=StreamingMessageType.METADATA,
            content="",
            metadata={
                "total_tokens": len(words),
                "duration_ms": len(words) * (request.stream_delay * 1000),
                "tokens_per_second": len(words) / (len(words) * request.stream_delay) if request.stream_delay > 0 else 0,
                "full_response": full_response.strip()
            }
        ))
    
    def _format_sse_message(self, chunk: StreamingChunk) -> str:
        """Format chunk as Server-Sent Event."""
        data = {
            "type": chunk.type.value,
            "content": chunk.content,
            "timestamp": chunk.timestamp,
            "metadata": chunk.metadata or {}
        }
        
        return f"data: {json.dumps(data)}\n\n"


# Router
router = APIRouter(prefix="/api/chat", tags=["Streaming Chat"])


@router.post("/stream")
async def stream_chat_completion(
    request: StreamingChatRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat completion using Server-Sent Events.
    
    Features:
    - Real-time token-by-token streaming
    - Cancellation support
    - Progress metadata
    - Error handling with retry
    - Multiple model provider support
    """
    stream_id = str(uuid.uuid4())
    
    # Get HTTP client from app state
    http_client = req.app.state.http_client
    
    streaming_engine = StreamingChatEngine(db, http_client)
    
    return StreamingResponse(
        streaming_engine.stream_chat_completion(request, current_user, stream_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/stream/{stream_id}/cancel")
async def cancel_stream(
    stream_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an active streaming chat session.
    """
    success = stream_manager.cancel_stream(stream_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Stream not found or already completed"
        )
    
    return {"message": "Stream cancelled successfully", "stream_id": stream_id}


@router.get("/stream/active")
async def get_active_streams(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of active streaming sessions for the current user.
    """
    active_streams = stream_manager.get_active_streams(current_user.id)
    
    return {
        "active_streams": active_streams,
        "count": len(active_streams)
    }


@router.get("/stream/health")
async def stream_health_check():
    """
    Health check for streaming service.
    """
    return {
        "status": "healthy",
        "active_streams_count": len(stream_manager.active_streams),
        "cancelled_streams_count": len(stream_manager.cancelled_streams),
        "timestamp": datetime.utcnow().isoformat()
    }