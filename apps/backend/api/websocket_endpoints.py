"""
WebSocket API Endpoints

This module provides WebSocket endpoints for real-time features and integrates
with the WebSocket manager for connection handling and message routing.
"""
import asyncio
import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from auth.jwt import get_current_user_websocket, get_current_user
from core.websocket_manager import websocket_manager, MessageType, WebSocketMessage

router = APIRouter(prefix="/api/ws", tags=["WebSocket"])

# WebSocket endpoint for general real-time communication
@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_websocket)
):
    """
    Main WebSocket endpoint for real-time communication.
    
    Supports:
    - Chat messaging
    - Presence updates
    - Analytics updates
    - System notifications
    """
    connection_id = None
    
    try:
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(websocket, user)
        
        # Handle incoming messages
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Send error back to client
                error_msg = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": str(e)}
                )
                await websocket_manager._send_message(connection_id, error_msg)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        if connection_id:
            await websocket_manager.disconnect(connection_id, code=1011, reason=str(e))
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

# Chat-specific WebSocket endpoint
@router.websocket("/chat/{conversation_id}")
async def chat_websocket(
    websocket: WebSocket,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_websocket)
):
    """
    WebSocket endpoint for real-time chat in a specific conversation.
    """
    connection_id = None
    
    try:
        # Verify user has access to conversation
        from db import crud
        conversation = await crud.get_conversation(db, conversation_id)
        if not conversation or not any(u.id == user.id for u in conversation.users):
            await websocket.close(code=1008, reason="Access denied")
            return
        
        # Connect and join conversation room
        connection_id = await websocket_manager.connect(
            websocket, 
            user, 
            metadata={"conversation_id": conversation_id}
        )
        
        await websocket_manager.join_room(connection_id, f"conversation_{conversation_id}")
        
        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, message)
            except WebSocketDisconnect:
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

# Analytics WebSocket endpoint (already exists in model_analytics.py but we can enhance it)
@router.websocket("/analytics")
async def analytics_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_websocket)
):
    """
    WebSocket endpoint for real-time analytics updates.
    """
    connection_id = None
    
    try:
        connection_id = await websocket_manager.connect(websocket, user)
        await websocket_manager.join_room(connection_id, "analytics")
        
        # Send initial analytics data
        from api.model_analytics import ModelAnalyticsEngine, AnalyticsRequest, TimeRange
        analytics_engine = ModelAnalyticsEngine(db)
        
        request = AnalyticsRequest(time_range=TimeRange.HOUR)
        analytics = await analytics_engine.get_analytics(request)
        
        initial_msg = WebSocketMessage(
            type=MessageType.ANALYTICS_UPDATE,
            data={
                "overview": analytics.overview,
                "active_models": len(analytics.model_metrics),
                "current_usage": analytics.overview["total_messages"]
            }
        )
        await websocket_manager._send_message(connection_id, initial_msg)
        
        # Keep connection alive and handle messages
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, message)
            except WebSocketDisconnect:
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

# Admin/monitoring endpoint
@router.websocket("/admin")
async def admin_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user_websocket)
):
    """
    WebSocket endpoint for admin monitoring and system events.
    """
    # Check if user is admin
    if not user.is_superuser:
        await websocket.close(code=1008, reason="Admin access required")
        return
    
    connection_id = None
    
    try:
        connection_id = await websocket_manager.connect(websocket, user)
        await websocket_manager.join_room(connection_id, "admin")
        
        # Send system stats
        stats_msg = WebSocketMessage(
            type=MessageType.CUSTOM,
            data={
                "type": "system_stats",
                "stats": websocket_manager.get_stats()
            }
        )
        await websocket_manager._send_message(connection_id, stats_msg)
        
        # Handle admin commands
        while True:
            try:
                message = await websocket.receive_text()
                await handle_admin_message(connection_id, message)
            except WebSocketDisconnect:
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

async def handle_admin_message(connection_id: str, raw_message: str):
    """Handle admin-specific WebSocket messages."""
    try:
        data = json.loads(raw_message)
        command = data.get("command")
        
        if command == "get_stats":
            stats = websocket_manager.get_stats()
            response = WebSocketMessage(
                type=MessageType.CUSTOM,
                data={"type": "stats_response", "stats": stats}
            )
            await websocket_manager._send_message(connection_id, response)
        
        elif command == "get_connections":
            connections = [
                {
                    "connection_id": conn.connection_id,
                    "user_id": conn.user_id,
                    "username": conn.user.username,
                    "connected_at": conn.connected_at.isoformat(),
                    "rooms": list(conn.rooms),
                    "message_count": conn.message_count
                }
                for conn in websocket_manager.connections.values()
            ]
            response = WebSocketMessage(
                type=MessageType.CUSTOM,
                data={"type": "connections_response", "connections": connections}
            )
            await websocket_manager._send_message(connection_id, response)
        
        elif command == "broadcast":
            message_text = data.get("message", "Admin broadcast")
            broadcast_msg = WebSocketMessage(
                type=MessageType.CUSTOM,
                data={
                    "type": "admin_broadcast",
                    "message": message_text,
                    "from": "System Administrator"
                }
            )
            count = await websocket_manager.broadcast_to_all(broadcast_msg, exclude={connection_id})
            
            response = WebSocketMessage(
                type=MessageType.CUSTOM,
                data={
                    "type": "broadcast_response",
                    "sent_to": count,
                    "message": "Broadcast sent successfully"
                }
            )
            await websocket_manager._send_message(connection_id, response)
    
    except Exception as e:
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": f"Admin command error: {str(e)}"}
        )
        await websocket_manager._send_message(connection_id, error_msg)

# REST endpoints for WebSocket management
@router.get("/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_user)
):
    """Get WebSocket manager statistics."""
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin access required")
    
    return websocket_manager.get_stats()

@router.get("/connections")
async def get_active_connections(
    current_user: User = Depends(get_current_user)
):
    """Get list of active WebSocket connections."""
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin access required")
    
    connections = []
    for conn in websocket_manager.connections.values():
        connections.append({
            "connection_id": conn.connection_id,
            "user_id": conn.user_id,
            "username": conn.user.username,
            "connected_at": conn.connected_at.isoformat(),
            "last_activity": conn.last_activity.isoformat(),
            "rooms": list(conn.rooms),
            "message_count": conn.message_count,
            "state": conn.state.value
        })
    
    return {
        "connections": connections,
        "total_count": len(connections)
    }

@router.get("/rooms")
async def get_active_rooms(
    current_user: User = Depends(get_current_user)
):
    """Get list of active rooms."""
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin access required")
    
    rooms = []
    for room_id, connection_ids in websocket_manager.rooms.items():
        members = []
        for conn_id in connection_ids:
            if conn_id in websocket_manager.connections:
                conn = websocket_manager.connections[conn_id]
                members.append({
                    "user_id": conn.user_id,
                    "username": conn.user.username,
                    "connection_id": conn.connection_id
                })
        
        rooms.append({
            "room_id": room_id,
            "member_count": len(members),
            "members": members
        })
    
    return {
        "rooms": rooms,
        "total_count": len(rooms)
    }

@router.post("/broadcast")
async def broadcast_message(
    message: str,
    room_id: str = Query(None, description="Room to broadcast to (optional)"),
    current_user: User = Depends(get_current_user)
):
    """Broadcast a message to all connections or a specific room."""
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin access required")
    
    broadcast_msg = WebSocketMessage(
        type=MessageType.CUSTOM,
        data={
            "type": "admin_broadcast",
            "message": message,
            "from": f"Admin ({current_user.username})"
        }
    )
    
    if room_id:
        count = await websocket_manager.broadcast_to_room(room_id, broadcast_msg)
        return {"message": f"Broadcast sent to room {room_id}", "recipients": count}
    else:
        count = await websocket_manager.broadcast_to_all(broadcast_msg)
        return {"message": "Broadcast sent to all connections", "recipients": count}

# Test page for WebSocket connections
@router.get("/test", response_class=HTMLResponse)
async def websocket_test_page():
    """Serve a test page for WebSocket connections."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; }
            .messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
            .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
            .message.sent { background-color: #e3f2fd; }
            .message.received { background-color: #f3e5f5; }
            .message.system { background-color: #fff3e0; }
            input, button { padding: 8px; margin: 5px; }
            input[type="text"] { width: 300px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>WebSocket Test Interface</h1>
            
            <div>
                <button id="connect">Connect</button>
                <button id="disconnect">Disconnect</button>
                <span id="status">Disconnected</span>
            </div>
            
            <div class="messages" id="messages"></div>
            
            <div>
                <input type="text" id="messageInput" placeholder="Enter message..." />
                <button id="send">Send</button>
            </div>
            
            <div>
                <input type="text" id="roomInput" placeholder="Room ID..." />
                <button id="joinRoom">Join Room</button>
                <button id="leaveRoom">Leave Room</button>
            </div>
        </div>

        <script>
            let socket = null;
            const messages = document.getElementById('messages');
            const status = document.getElementById('status');
            const messageInput = document.getElementById('messageInput');
            const roomInput = document.getElementById('roomInput');

            function addMessage(content, type = 'received') {
                const div = document.createElement('div');
                div.className = `message ${type}`;
                div.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${content}`;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }

            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/ws/connect`;
                
                socket = new WebSocket(wsUrl);
                
                socket.onopen = () => {
                    status.textContent = 'Connected';
                    status.style.color = 'green';
                    addMessage('Connected to WebSocket', 'system');
                };
                
                socket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    addMessage(`[${data.type}] ${JSON.stringify(data.data)}`, 'received');
                };
                
                socket.onclose = () => {
                    status.textContent = 'Disconnected';
                    status.style.color = 'red';
                    addMessage('WebSocket connection closed', 'system');
                };
                
                socket.onerror = (error) => {
                    addMessage(`Error: ${error}`, 'system');
                };
            }

            function disconnect() {
                if (socket) {
                    socket.close();
                    socket = null;
                }
            }

            function sendMessage() {
                if (socket && messageInput.value.trim()) {
                    const message = {
                        type: 'custom',
                        data: { message: messageInput.value.trim() }
                    };
                    socket.send(JSON.stringify(message));
                    addMessage(messageInput.value.trim(), 'sent');
                    messageInput.value = '';
                }
            }

            function joinRoom() {
                if (socket && roomInput.value.trim()) {
                    const message = {
                        type: 'custom',
                        data: { action: 'join_room', room_id: roomInput.value.trim() }
                    };
                    socket.send(JSON.stringify(message));
                    addMessage(`Joining room: ${roomInput.value.trim()}`, 'sent');
                }
            }

            function leaveRoom() {
                if (socket && roomInput.value.trim()) {
                    const message = {
                        type: 'custom',
                        data: { action: 'leave_room', room_id: roomInput.value.trim() }
                    };
                    socket.send(JSON.stringify(message));
                    addMessage(`Leaving room: ${roomInput.value.trim()}`, 'sent');
                }
            }

            // Event listeners
            document.getElementById('connect').onclick = connect;
            document.getElementById('disconnect').onclick = disconnect;
            document.getElementById('send').onclick = sendMessage;
            document.getElementById('joinRoom').onclick = joinRoom;
            document.getElementById('leaveRoom').onclick = leaveRoom;
            
            messageInput.onkeypress = (e) => {
                if (e.key === 'Enter') sendMessage();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)