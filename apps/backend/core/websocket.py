"""
WebSocket management for real-time updates
Handles connections, broadcasting, and model status updates
"""
import asyncio
import json
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import uuid

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a single WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.subscriptions: Set[str] = set()
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON data to the client"""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_json(data)
                return True
        except Exception as e:
            logger.error(f"Failed to send to connection {self.connection_id}: {e}")
        return False
    
    async def send_text(self, text: str) -> bool:
        """Send text data to the client"""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(text)
                return True
        except Exception as e:
            logger.error(f"Failed to send to connection {self.connection_id}: {e}")
        return False


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.topic_subscribers: Dict[str, Set[str]] = {}  # topic -> connection_ids
        self._heartbeat_task = None
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: Optional[str] = None
    ) -> WebSocketConnection:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(websocket, connection_id, user_id)
        
        self.active_connections[connection_id] = connection
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        
        # Send welcome message
        await connection.send_json({
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start heartbeat if not already running
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        return connection
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id not in self.active_connections:
            return
        
        connection = self.active_connections[connection_id]
        
        # Remove from user connections
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from topic subscriptions
        for topic in connection.subscriptions:
            if topic in self.topic_subscribers:
                self.topic_subscribers[topic].discard(connection_id)
                if not self.topic_subscribers[topic]:
                    del self.topic_subscribers[topic]
        
        del self.active_connections[connection_id]
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe(self, connection_id: str, topics: List[str]):
        """Subscribe a connection to topics"""
        if connection_id not in self.active_connections:
            return
        
        connection = self.active_connections[connection_id]
        
        for topic in topics:
            connection.subscriptions.add(topic)
            if topic not in self.topic_subscribers:
                self.topic_subscribers[topic] = set()
            self.topic_subscribers[topic].add(connection_id)
        
        logger.info(f"Connection {connection_id} subscribed to: {topics}")
        
        # Confirm subscription
        await connection.send_json({
            "type": "subscription",
            "status": "subscribed",
            "topics": topics,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def unsubscribe(self, connection_id: str, topics: List[str]):
        """Unsubscribe a connection from topics"""
        if connection_id not in self.active_connections:
            return
        
        connection = self.active_connections[connection_id]
        
        for topic in topics:
            connection.subscriptions.discard(topic)
            if topic in self.topic_subscribers:
                self.topic_subscribers[topic].discard(connection_id)
                if not self.topic_subscribers[topic]:
                    del self.topic_subscribers[topic]
        
        logger.info(f"Connection {connection_id} unsubscribed from: {topics}")
        
        # Confirm unsubscription
        await connection.send_json({
            "type": "subscription",
            "status": "unsubscribed",
            "topics": topics,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        message["timestamp"] = datetime.utcnow().isoformat()
        disconnected = []
        
        for connection_id, connection in self.active_connections.items():
            success = await connection.send_json(message)
            if not success:
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """Broadcast a message to all subscribers of a topic"""
        if topic not in self.topic_subscribers:
            return
        
        message["topic"] = topic
        message["timestamp"] = datetime.utcnow().isoformat()
        disconnected = []
        
        for connection_id in self.topic_subscribers[topic]:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                success = await connection.send_json(message)
                if not success:
                    disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections for a specific user"""
        if user_id not in self.user_connections:
            return
        
        message["timestamp"] = datetime.utcnow().isoformat()
        disconnected = []
        
        for connection_id in self.user_connections[user_id]:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                success = await connection.send_json(message)
                if not success:
                    disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    async def send_model_update(self, model_id: str, status: str, details: Optional[Dict] = None):
        """Send model status update to subscribers"""
        message = {
            "type": "model_update",
            "model_id": model_id,
            "status": status,
            "details": details or {}
        }
        
        # Broadcast to model-specific topic
        await self.broadcast_to_topic(f"model:{model_id}", message)
        
        # Also broadcast to general models topic
        await self.broadcast_to_topic("models", message)
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        if connection_id not in self.active_connections:
            return
        
        connection = self.active_connections[connection_id]
        message_type = message.get("type")
        
        if message_type == "ping":
            # Handle ping
            connection.last_ping = datetime.utcnow()
            await connection.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "subscribe":
            # Handle subscription request
            topics = message.get("topics", [])
            await self.subscribe(connection_id, topics)
        
        elif message_type == "unsubscribe":
            # Handle unsubscription request
            topics = message.get("topics", [])
            await self.unsubscribe(connection_id, topics)
        
        else:
            # Unknown message type
            await connection.send_json({
                "type": "error",
                "error": "Unknown message type",
                "message_type": message_type,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to all connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
                if not self.active_connections:
                    continue
                
                # Send heartbeat
                await self.broadcast({
                    "type": "heartbeat",
                    "server_time": datetime.utcnow().isoformat()
                })
                
                # Check for stale connections
                now = datetime.utcnow()
                stale_connections = []
                
                for connection_id, connection in self.active_connections.items():
                    time_since_ping = (now - connection.last_ping).total_seconds()
                    if time_since_ping > 90:  # 90 seconds without ping
                        stale_connections.append(connection_id)
                
                # Remove stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Removing stale connection: {connection_id}")
                    self.disconnect(connection_id)
                    
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "authenticated_users": len(self.user_connections),
            "topics": list(self.topic_subscribers.keys()),
            "connections_by_topic": {
                topic: len(subscribers) 
                for topic, subscribers in self.topic_subscribers.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = None
):
    """
    WebSocket endpoint handler
    """
    connection = await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await manager.handle_message(connection.connection_id, message)
            except json.JSONDecodeError:
                await connection.send_json({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(connection.connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection.connection_id)