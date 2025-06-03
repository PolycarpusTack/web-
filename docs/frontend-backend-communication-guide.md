# Frontend-Backend Communication Guide

This guide covers the complete setup for proper communication between the Web+ frontend and backend, including authentication, CORS, WebSocket connections, and error handling.

## Table of Contents

- [Overview](#overview)
- [Backend Configuration](#backend-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Authentication Flow](#authentication-flow)
- [WebSocket Implementation](#websocket-implementation)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Overview

The Web+ platform uses:
- **REST API** for standard CRUD operations
- **WebSocket** for real-time updates
- **JWT tokens** for user authentication
- **API keys** for service authentication

## Backend Configuration

### 1. Enhanced Configuration (`core/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # CORS settings - CRITICAL for frontend communication
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    cors_allow_headers: List[str] = ["*"]
    cors_expose_headers: List[str] = ["Content-Length", "X-Total-Count"]
```

### 2. Middleware Setup (`core/middleware.py`)

The middleware provides:
- **Request/Response Logging**: Track all API calls
- **Error Handling**: Consistent error responses
- **Authentication Logging**: Monitor auth attempts
- **CORS Debugging**: Debug CORS issues in development

### 3. CORS Configuration in FastAPI

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    expose_headers=settings.cors_expose_headers,
)
```

### 4. WebSocket Manager (`core/websocket.py`)

Features:
- Connection management with unique IDs
- Topic-based subscriptions
- Automatic heartbeat/keepalive
- Reconnection support
- User-specific messaging

## Frontend Configuration

### 1. Enhanced API Client (`lib/api-client.ts`)

Features:
- Automatic token refresh
- Retry logic with exponential backoff
- Request/response logging in development
- Proper error handling and typing
- Support for both JWT and API key auth

```typescript
import { apiClient } from '@/lib/api-client';

// Configure API client
const client = new ApiClient({
  baseUrl: 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
});

// Make API calls
const models = await client.get('/api/models');
const result = await client.post('/api/chat/completions', { 
  model_id: 'llama2',
  prompt: 'Hello' 
});
```

### 2. WebSocket Client (`lib/websocket-client.ts`)

Features:
- Automatic reconnection with backoff
- Connection state management
- Event-based messaging
- Topic subscriptions
- React hook integration

```typescript
import { createWebSocketClient } from '@/lib/websocket-client';

const wsClient = createWebSocketClient({
  url: 'ws://localhost:8000/ws',
  reconnect: true,
  reconnectMaxRetries: 10,
});

// Subscribe to topics
wsClient.subscribe(['models', 'model:llama2']);

// Handle messages
wsClient.on('model_update', (data) => {
  console.log('Model updated:', data);
});
```

### 3. Environment Variables

Create `.env` file in frontend:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Authentication Flow

### 1. Login Flow

```typescript
// Frontend login
const response = await apiClient.post('/auth/login', {
  username: 'user@example.com',
  password: 'password'
});

// Response contains tokens
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "user": { ... }
}

// Tokens are automatically stored and used
```

### 2. Token Refresh

The API client automatically:
1. Checks token expiry before requests
2. Refreshes token if expired
3. Retries original request with new token
4. Logs out user if refresh fails

### 3. API Key Authentication

```typescript
// Set API key
apiClient.setApiKey('your-api-key');

// API key is sent as X-API-Key header
```

## WebSocket Implementation

### 1. Backend WebSocket Endpoint

```python
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    api_key: str = None
):
    # Validate authentication
    user_id = validate_auth(token, api_key)
    
    # Handle connection
    await manager.connect(websocket, user_id)
```

### 2. Frontend WebSocket Hook

```typescript
function ModelStatus() {
  const { state, lastMessage, subscribe } = useWebSocket();
  
  useEffect(() => {
    if (state === ConnectionState.CONNECTED) {
      subscribe('models');
    }
  }, [state]);
  
  useEffect(() => {
    if (lastMessage?.type === 'model_update') {
      // Handle model update
    }
  }, [lastMessage]);
}
```

### 3. Real-time Model Updates

```python
# Backend sends update
await manager.send_model_update(
    model_id="llama2",
    status="running",
    details={"message": "Model started"}
)

# Frontend receives update
{
  "type": "model_update",
  "model_id": "llama2",
  "status": "running",
  "details": {
    "message": "Model started"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Handling

### 1. API Error Format

```json
{
  "error": "Validation error",
  "message": "Invalid model ID",
  "details": { ... },
  "request_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. Frontend Error Handling

```typescript
try {
  const data = await apiClient.get('/api/models');
} catch (error) {
  if (error instanceof ApiError) {
    if (error.isAuthError()) {
      // Handle auth error
    } else if (error.isValidationError()) {
      // Handle validation error
    } else if (error.isServerError()) {
      // Handle server error
    }
  }
}
```

### 3. WebSocket Error Recovery

The WebSocket client automatically:
1. Detects disconnections
2. Attempts reconnection with backoff
3. Re-subscribes to topics on reconnect
4. Queues messages during disconnection

## Testing

### 1. Test CORS Configuration

```bash
# Test preflight request
curl -X OPTIONS http://localhost:8000/api/models \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" -v
```

### 2. Test Authentication

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "password"}'

# Use token
curl http://localhost:8000/api/models \
  -H "Authorization: Bearer <token>"
```

### 3. Test WebSocket

```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8000/ws?token=<token>');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.send(JSON.stringify({ type: 'subscribe', topics: ['models'] }));
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check that frontend URL is in `cors_origins`
   - Ensure credentials are allowed
   - Check browser console for specific CORS errors

2. **401 Unauthorized**
   - Check token expiry
   - Verify token is being sent
   - Check API key if using

3. **WebSocket Connection Failed**
   - Verify WebSocket URL
   - Check authentication
   - Look for firewall/proxy issues

4. **Request Timeouts**
   - Increase timeout in API client
   - Check backend processing time
   - Verify network connectivity

### Debug Mode

Enable debug logging:

```python
# Backend
settings.debug = True
settings.log_level = "DEBUG"
```

```typescript
// Frontend
const client = new ApiClient({
  debug: true
});

const wsClient = createWebSocketClient({
  debug: true
});
```

### Monitoring

1. **Backend Logs**
   - Request/response details
   - Authentication attempts
   - WebSocket connections
   - Error stack traces

2. **Frontend Console**
   - API request/response
   - WebSocket messages
   - Connection state changes

3. **Network Tab**
   - Check request headers
   - Verify response format
   - Monitor WebSocket frames

## Best Practices

1. **Security**
   - Use HTTPS in production
   - Secure WebSocket (WSS)
   - Rotate API keys regularly
   - Implement rate limiting

2. **Performance**
   - Enable compression
   - Use connection pooling
   - Implement caching
   - Batch WebSocket messages

3. **Reliability**
   - Handle network errors gracefully
   - Implement retry logic
   - Use circuit breakers
   - Monitor connection health

4. **Development**
   - Use consistent error formats
   - Log important events
   - Document API changes
   - Test edge cases

This setup ensures reliable, secure, and performant communication between the Web+ frontend and backend with proper error handling and real-time updates.