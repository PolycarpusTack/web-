from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import os

from auth.jwt import get_current_user
from db.database import get_db
from db import crud
from db.models import User
from .file_service import (
    upload_file, upload_multiple_files, get_file_contents, 
    delete_file_and_record, get_file_url, ALL_ALLOWED_TYPES, MAX_FILE_SIZE
)

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

# File upload and management endpoints
@router.post("/upload")
async def upload_single_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a single file."""
    try:
        # If conversation_id is provided, verify it exists and user has access
        if conversation_id:
            conversation = await crud.get_conversation(db, conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            # Check if user is part of the conversation
            user_conversations = await crud.get_user_conversations(db, current_user.id)
            if conversation.id not in [c.id for c in user_conversations]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have access to this conversation"
                )
        
        # Set up metadata if provided
        metadata = None
        if description:
            metadata = {"description": description}
        
        # Upload file
        result = await upload_file(
            db=db,
            file=file,
            user_id=current_user.id,
            conversation_id=conversation_id,
            metadata=metadata
        )
        
        # Add URL to result
        result["url"] = get_file_url(result["id"])
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/upload/conversation/{conversation_id}")
async def upload_files_to_conversation(
    conversation_id: str,
    files: List[UploadFile] = File(...),
    message_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload multiple files to a conversation."""
    try:
        # Verify conversation exists and user has access
        conversation = await crud.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check if user is part of the conversation
        user_conversations = await crud.get_user_conversations(db, current_user.id)
        if conversation.id not in [c.id for c in user_conversations]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this conversation"
            )
        
        # If message_id is provided, verify it exists and belongs to the conversation
        if message_id:
            message = await db.get(crud.Message, message_id)
            if not message or message.conversation_id != conversation_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message not found in this conversation"
                )
        
        # Upload files
        results = await upload_multiple_files(
            db=db,
            files=files,
            user_id=current_user.id,
            conversation_id=conversation_id,
            message_id=message_id
        )
        
        # Add URLs to results
        for result in results:
            result["url"] = get_file_url(result["id"])
        
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/")
async def get_user_files(
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get files for the current user, optionally filtered by conversation."""
    try:
        if conversation_id:
            # Check if user has access to the conversation
            conversation = await crud.get_conversation(db, conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            user_conversations = await crud.get_user_conversations(db, current_user.id)
            if conversation.id not in [c.id for c in user_conversations]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have access to this conversation"
                )
            
            # Get files for the conversation
            files = await crud.get_conversation_files(db, conversation_id)
        else:
            # Get all files for the user
            files = await crud.get_user_files(db, current_user.id)
        
        # Format response
        results = []
        for file in files:
            results.append({
                "id": file.id,
                "filename": file.original_filename,
                "content_type": file.content_type,
                "size": file.size,
                "conversation_id": file.conversation_id,
                "created_at": file.created_at.isoformat(),
                "url": get_file_url(file.id),
                "metadata": file.metadata or {}
            })
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving files: {str(e)}"
        )

@router.get("/{file_id}")
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a file by ID."""
    try:
        # Get file record
        file = await crud.get_file(db, file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if user has access to the file
        if file.user_id != current_user.id and not file.is_public:
            # Check if user has access to the conversation
            if file.conversation_id:
                user_conversations = await crud.get_user_conversations(db, current_user.id)
                if file.conversation_id not in [c.id for c in user_conversations]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User does not have access to this file"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have access to this file"
                )
        
        # Check if file exists on disk
        if not os.path.exists(file.path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        # Return file as appropriate response
        return FileResponse(
            file.path,
            filename=file.original_filename,
            media_type=file.content_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving file: {str(e)}"
        )

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a file."""
    try:
        # Get file record
        file = await crud.get_file(db, file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if user has access to delete the file
        if file.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to delete this file"
            )
        
        # Delete file
        success = await delete_file_and_record(file_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
        
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}"
        )

@router.get("/message/{message_id}")
async def get_message_files(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get files attached to a message."""
    try:
        # Get message
        message = await db.get(crud.Message, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Get conversation to check access
        conversation = await crud.get_conversation(db, message.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check if user has access to the conversation
        user_conversations = await crud.get_user_conversations(db, current_user.id)
        if conversation.id not in [c.id for c in user_conversations]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this conversation"
            )
        
        # Get files for the message
        files = await crud.get_message_files(db, message_id)
        
        # Format response
        results = []
        for file in files:
            results.append({
                "id": file.id,
                "filename": file.original_filename,
                "content_type": file.content_type,
                "size": file.size,
                "created_at": file.created_at.isoformat(),
                "url": get_file_url(file.id),
                "metadata": file.metadata or {}
            })
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving message files: {str(e)}"
        )

@router.get("/info")
async def get_file_upload_info():
    """Get information about file upload restrictions."""
    return {
        "allowed_types": ALL_ALLOWED_TYPES,
        "max_file_size": MAX_FILE_SIZE,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
    }