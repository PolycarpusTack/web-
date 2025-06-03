"""
WebSocket Management System

This module provides a comprehensive WebSocket management system for real-time features:
- Connection management with authentication
- Room-based message broadcasting  
- Presence tracking
- Heartbeat/ping-pong for connection health
- Message queuing and retry
- Rate limiting and abuse prevention
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"

class MessageType(Enum):
    # System messages
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    
    # Presence
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    PRESENCE_UPDATE = "presence_update"
    
    # Chat
    MESSAGE = "message"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    
    # Analytics
    ANALYTICS_UPDATE = "analytics_update"
    
    # Conversations
    CONVERSATION_UPDATE = "conversation_update"
    
    # Custom
    CUSTOM = "custom"

@dataclass
class WebSocketMessage:
    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: Optional[str] = None
    room_id: Optional[str] = None

@dataclass
class ConnectionInfo:
    websocket: WebSocket
    user_id: str
    user: User
    connection_id: str
    state: ConnectionState
    connected_at: datetime
    last_ping: Optional[datetime] = None
    last_pong: Optional[datetime] = None
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_count: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)

class RateLimiter:
    def __init__(self, max_messages: int = 100, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.message_times: Dict[str, List[float]] = {}
    
    def is_allowed(self, connection_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        if connection_id not in self.message_times:
            self.message_times[connection_id] = []
        
        # Clean old messages
        self.message_times[connection_id] = [
            msg_time for msg_time in self.message_times[connection_id]
            if msg_time > window_start
        ]
        
        # Check limit
        if len(self.message_times[connection_id]) >= self.max_messages:
            return False
        
        self.message_times[connection_id].append(now)
        return True
    
    def cleanup(self, connection_id: str):
        self.message_times.pop(connection_id, None)

class MessageQueue:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues: Dict[str, List[WebSocketMessage]] = {}
    
    def add_message(self, connection_id: str, message: WebSocketMessage):
        if connection_id not in self.queues:
            self.queues[connection_id] = []
        
        self.queues[connection_id].append(message)
        
        # Limit queue size
        if len(self.queues[connection_id]) > self.max_size:
            self.queues[connection_id].pop(0)
    
    def get_messages(self, connection_id: str) -> List[WebSocketMessage]:
        return self.queues.pop(connection_id, [])
    
    def clear_queue(self, connection_id: str):
        self.queues.pop(connection_id, None)

class WebSocketManager:
    def __init__(self):
        # Active connections
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        
        # Rooms for broadcasting
        self.rooms: Dict[str, Set[str]] = {}  # room_id -> connection_ids
        
        # Message handling
        self.message_queue = MessageQueue()
        self.rate_limiter = RateLimiter()
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        
        # Health monitoring
        self.ping_interval = 30  # seconds
        self.ping_timeout = 10   # seconds
        self._ping_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "rooms_created": 0,
            "errors": 0
        }
    
    async def connect(self, websocket: WebSocket, user: User, metadata: Dict[str, Any] = None) -> str:
        """Establish a new WebSocket connection."""
        try:
            await websocket.accept()
            
            connection_id = str(uuid.uuid4())
            connection_info = ConnectionInfo(
                websocket=websocket,
                user_id=user.id,
                user=user,
                connection_id=connection_id,
                state=ConnectionState.CONNECTED,
                connected_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Store connection
            self.connections[connection_id] = connection_info
            
            # Track user connections
            if user.id not in self.user_connections:
                self.user_connections[user.id] = set()
            self.user_connections[user.id].add(connection_id)
            
            # Update stats
            self.stats["total_connections"] += 1
            
            # Send connection confirmation
            await self._send_message(connection_id, WebSocketMessage(
                type=MessageType.CONNECT,
                data={
                    "connection_id": connection_id,
                    "user_id": user.id,
                    "username": user.username,
                    "connected_at": connection_info.connected_at.isoformat()
                }
            ))
            
            # Start ping task if first connection
            if len(self.connections) == 1 and not self._ping_task:
                self._ping_task = asyncio.create_task(self._ping_loop())
            
            logger.info(f"WebSocket connected: user={user.username}, connection={connection_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            await websocket.close(code=1011, reason="Connection failed")
            raise
    
    async def disconnect(self, connection_id: str, code: int = 1000, reason: str = "Normal closure"):
        """Disconnect a WebSocket connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.state = ConnectionState.DISCONNECTING
        
        try:
            # Leave all rooms
            for room_id in list(connection.rooms):
                await self.leave_room(connection_id, room_id)
            
            # Clean up user connections
            if connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]
            
            # Send disconnect message to other connections
            await self._broadcast_user_presence(connection.user, "left")
            
            # Close WebSocket
            if connection.websocket.client_state.name != "DISCONNECTED":
                await connection.websocket.close(code=code, reason=reason)
            
            # Clean up
            del self.connections[connection_id]
            self.rate_limiter.cleanup(connection_id)
            self.message_queue.clear_queue(connection_id)
            
            logger.info(f"WebSocket disconnected: user={connection.user.username}, connection={connection_id}")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        
        finally:
            # Stop ping task if no connections
            if not self.connections and self._ping_task:
                self._ping_task.cancel()
                self._ping_task = None
    
    async def join_room(self, connection_id: str, room_id: str) -> bool:
        """Add a connection to a room for broadcasting."""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        # Add to room
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
            self.stats["rooms_created"] += 1
        
        self.rooms[room_id].add(connection_id)
        connection.rooms.add(room_id)
        
        # Notify room members
        await self.broadcast_to_room(room_id, WebSocketMessage(
            type=MessageType.USER_JOINED,
            data={
                "user_id": connection.user_id,
                "username": connection.user.username,
                "room_id": room_id
            },
            sender_id=connection.user_id
        ), exclude={connection_id})
        
        logger.debug(f"User {connection.user.username} joined room {room_id}")
        return True
    
    async def leave_room(self, connection_id: str, room_id: str) -> bool:
        """Remove a connection from a room."""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        if room_id in self.rooms:
            self.rooms[room_id].discard(connection_id)
            
            # Remove empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        connection.rooms.discard(room_id)
        
        # Notify room members
        if room_id in self.rooms:
            await self.broadcast_to_room(room_id, WebSocketMessage(
                type=MessageType.USER_LEFT,
                data={
                    "user_id": connection.user_id,
                    "username": connection.user.username,
                    "room_id": room_id
                },
                sender_id=connection.user_id
            ))
        
        logger.debug(f"User {connection.user.username} left room {room_id}")
        return True
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Send a message to all connections of a specific user."""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        for connection_id in list(self.user_connections[user_id]):
            try:
                await self._send_message(connection_id, message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
        
        return sent_count
    
    async def broadcast_to_room(self, room_id: str, message: WebSocketMessage, exclude: Set[str] = None):
        """Broadcast a message to all connections in a room."""
        if room_id not in self.rooms:
            return 0
        
        exclude = exclude or set()
        sent_count = 0
        
        for connection_id in list(self.rooms[room_id]):
            if connection_id not in exclude:
                try:
                    await self._send_message(connection_id, message)
                    sent_count += 1
                except Exception:
                    pass  # Connection will be cleaned up elsewhere
        
        return sent_count
    
    async def broadcast_to_all(self, message: WebSocketMessage, exclude: Set[str] = None):
        """Broadcast a message to all connected users."""
        exclude = exclude or set()
        sent_count = 0
        
        for connection_id in list(self.connections.keys()):
            if connection_id not in exclude:
                try:
                    await self._send_message(connection_id, message)
                    sent_count += 1
                except Exception:
                    pass
        
        return sent_count
    
    async def handle_message(self, connection_id: str, raw_message: str):
        """Handle incoming WebSocket message."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(connection_id):
            await self._send_error(connection_id, "Rate limit exceeded")
            return
        
        try:
            # Parse message
            data = json.loads(raw_message)
            message_type = MessageType(data.get("type", MessageType.CUSTOM.value))
            
            message = WebSocketMessage(
                type=message_type,
                data=data.get("data", {}),
                sender_id=connection.user_id,
                room_id=data.get("room_id")
            )
            
            # Update connection activity
            connection.message_count += 1
            connection.last_activity = datetime.utcnow()
            self.stats["messages_received"] += 1
            
            # Handle system messages
            if message_type == MessageType.PING:
                await self._handle_ping(connection_id)
            elif message_type == MessageType.PONG:
                await self._handle_pong(connection_id)
            else:
                # Call registered handlers
                if message_type in self.message_handlers:
                    for handler in self.message_handlers[message_type]:
                        try:
                            await handler(connection_id, message)
                        except Exception as e:
                            logger.error(f"Message handler error: {e}")
                
                # Forward to room if specified
                if message.room_id:
                    await self.broadcast_to_room(
                        message.room_id, 
                        message, 
                        exclude={connection_id}
                    )
        
        except json.JSONDecodeError:
            await self._send_error(connection_id, "Invalid JSON message")
        except ValueError as e:
            await self._send_error(connection_id, f"Invalid message type: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(connection_id, "Message processing error")
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for a specific message type."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection information."""
        return self.connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """Get all connections for a user."""
        if user_id not in self.user_connections:
            return []
        
        return [
            self.connections[conn_id] 
            for conn_id in self.user_connections[user_id]
            if conn_id in self.connections
        ]
    
    def get_room_members(self, room_id: str) -> List[ConnectionInfo]:
        """Get all connections in a room."""
        if room_id not in self.rooms:
            return []
        
        return [
            self.connections[conn_id]
            for conn_id in self.rooms[room_id]
            if conn_id in self.connections
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            **self.stats,
            "active_connections": len(self.connections),
            "active_users": len(self.user_connections),
            "active_rooms": len(self.rooms),
            "uptime_seconds": time.time() - (self.stats.get("start_time", time.time()))
        }
    
    async def _send_message(self, connection_id: str, message: WebSocketMessage):
        """Send a message to a specific connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            message_data = {
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp,
                "id": message.id,
                "sender_id": message.sender_id,
                "room_id": message.room_id
            }
            
            await connection.websocket.send_text(json.dumps(message_data))
            self.stats["messages_sent"] += 1
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.stats["errors"] += 1
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send an error message to a connection."""
        await self._send_message(connection_id, WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message}
        ))
    
    async def _handle_ping(self, connection_id: str):
        """Handle ping message."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.last_ping = datetime.utcnow()
            await self._send_message(connection_id, WebSocketMessage(type=MessageType.PONG))
    
    async def _handle_pong(self, connection_id: str):
        """Handle pong message."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.last_pong = datetime.utcnow()
    
    async def _ping_loop(self):
        """Background task to ping connections and detect dead ones."""
        while self.connections:
            try:
                now = datetime.utcnow()
                dead_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Send ping if needed
                    if (not connection.last_ping or 
                        (now - connection.last_ping).seconds >= self.ping_interval):
                        try:
                            await self._send_message(connection_id, WebSocketMessage(type=MessageType.PING))
                            connection.last_ping = now
                        except Exception:
                            dead_connections.append(connection_id)
                    
                    # Check for timeout
                    elif (connection.last_ping and not connection.last_pong or
                          (connection.last_pong and 
                           (now - connection.last_pong).seconds > self.ping_timeout)):
                        dead_connections.append(connection_id)
                
                # Disconnect dead connections
                for connection_id in dead_connections:
                    await self.disconnect(connection_id, code=1006, reason="Ping timeout")
                
                await asyncio.sleep(self.ping_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
                await asyncio.sleep(5)
    
    async def _broadcast_user_presence(self, user: User, status: str):
        """Broadcast user presence change to relevant rooms/users."""
        message = WebSocketMessage(
            type=MessageType.PRESENCE_UPDATE,
            data={
                "user_id": user.id,
                "username": user.username,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            },
            sender_id=user.id
        )
        
        # For now, broadcast to all connections
        # In a real app, you'd broadcast only to relevant rooms/users
        await self.broadcast_to_all(message)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()