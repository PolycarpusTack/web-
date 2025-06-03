# API Reference

This document provides a detailed reference for the web-plus API endpoints.

## Authentication

The API supports two authentication methods:

1. **API Key Authentication**:
   ```
   X-API-Key: your_api_key
   ```

2. **JWT Token Authentication**:
   ```
   Authorization: Bearer your_jwt_token
   ```

You can use either method for most endpoints. Some user-specific endpoints require JWT authentication.

## Authentication API

### Register a New User

Create a new user account.

**Endpoint**: `POST /api/auth/register`

**Request Body**:
```json
{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!"
}
```

**Response**:
```json
{
  "id": "user123",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-05-08T12:00:00Z",
  "updated_at": "2025-05-08T12:00:00Z"
}
```

### Login

Authenticate a user and get access/refresh tokens.

**Endpoint**: `POST /api/auth/login`

**Request Body**:
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "expires_at": "2025-05-08T13:00:00Z"
}
```

### Refresh Token

Get a new access token using a refresh token.

**Endpoint**: `POST /api/auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1..."
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "expires_at": "2025-05-08T14:00:00Z"
}
```

### Get Current User

Get information about the currently authenticated user.

**Endpoint**: `GET /api/auth/me`

**Authentication**: JWT token required

**Response**:
```json
{
  "id": "user123",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-05-08T12:00:00Z"
}
```

### Update Current User

Update the current user's information.

**Endpoint**: `PUT /api/auth/me`

**Authentication**: JWT token required

**Request Body**:
```json
{
  "email": "new.email@example.com",
  "full_name": "John D. Doe"
}
```

**Response**:
```json
{
  "id": "user123",
  "username": "johndoe",
  "email": "new.email@example.com",
  "full_name": "John D. Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-05-08T12:00:00Z"
}
```

### Change Password

Change the current user's password.

**Endpoint**: `POST /api/auth/change-password`

**Authentication**: JWT token required

**Request Body**:
```json
{
  "current_password": "SecurePassword123!",
  "new_password": "EvenMoreSecure456!",
  "new_password_confirm": "EvenMoreSecure456!"
}
```

**Response**: `204 No Content`

## API Key Management

### Create API Key

Create a new API key for the current user.

**Endpoint**: `POST /api/api-keys`

**Authentication**: JWT token required

**Request Body**:
```json
{
  "name": "Development API Key",
  "expires_in_days": 30
}
```

**Response**:
```json
{
  "id": "key123",
  "name": "Development API Key",
  "key": "your-api-key-value",
  "created_at": "2025-05-08T12:00:00Z",
  "expires_at": "2025-06-07T12:00:00Z",
  "last_used_at": null,
  "is_active": true
}
```

Note: The API key value is returned only once and cannot be retrieved again.

### List API Keys

Get a list of all API keys for the current user.

**Endpoint**: `GET /api/api-keys`

**Authentication**: JWT token required

**Response**:
```json
[
  {
    "id": "key123",
    "name": "Development API Key",
    "created_at": "2025-05-08T12:00:00Z",
    "expires_at": "2025-06-07T12:00:00Z",
    "last_used_at": "2025-05-08T12:30:00Z",
    "is_active": true
  },
  {
    "id": "key456",
    "name": "Production API Key",
    "created_at": "2025-05-01T12:00:00Z",
    "expires_at": null,
    "last_used_at": "2025-05-08T12:15:00Z",
    "is_active": true
  }
]
```

Note: For security reasons, the actual API key values are not returned.

### Revoke API Key

Revoke an API key without deleting it.

**Endpoint**: `PUT /api/api-keys/{api_key_id}/revoke`

**Authentication**: JWT token required

**Response**:
```json
{
  "id": "key123",
  "name": "Development API Key",
  "created_at": "2025-05-08T12:00:00Z",
  "expires_at": "2025-06-07T12:00:00Z",
  "last_used_at": "2025-05-08T12:30:00Z",
  "is_active": false
}
```

### Delete API Key

Delete an API key.

**Endpoint**: `DELETE /api/api-keys/{api_key_id}`

**Authentication**: JWT token required

**Response**: `204 No Content`

## Models API

### List Available Models

Retrieves a list of all available models.

**Endpoint**: `GET /api/models/available`

**Query Parameters**:
- `use_cache` (optional): Boolean flag to control cache usage (default: true)

**Response**:
```json
{
  "models": [
    {
      "id": "llama2:7b",
      "name": "Llama2",
      "size": "3.42 GB",
      "status": "running",
      "running": true,
      "metadata": {
        "digest": "sha256:123..."
      }
    },
    ...
  ],
  "cache_hit": true
}
```

### Start Model

Starts a specified model.

**Endpoint**: `POST /api/models/start`

**Request Body**:
```json
{
  "model_id": "llama2:7b"
}
```

**Response**:
```json
{
  "message": "Model llama2:7b started successfully",
  "model_id": "llama2:7b",
  "status": "running"
}
```

### Stop Model

Stops a specified model.

**Endpoint**: `POST /api/models/stop`

**Request Body**:
```json
{
  "model_id": "llama2:7b"
}
```

**Response**:
```json
{
  "message": "Model llama2:7b stopped successfully",
  "model_id": "llama2:7b",
  "status": "stopped"
}
```

### Get Model Details

Gets detailed information about a specific model.

**Endpoint**: `GET /api/models/{model_id}`

**Response**:
```json
{
  "id": "llama2:7b",
  "name": "Llama2",
  "size": "3.42 GB",
  "status": "running",
  "running": true,
  "type": "general",
  "description": "Meta's Llama 2 7B parameter model",
  "tags": ["general", "chatbot"],
  "version": "2.0",
  "provider": "meta",
  "lastUpdated": "2023-07-15T00:00:00Z",
  "metadata": {
    "digest": "sha256:123..."
  }
}
```

## Chat API

### Send Chat Message

Sends a message to a model and retrieves a response.

**Endpoint**: `POST /api/chat/completions`

**Request Body**:
```json
{
  "model_id": "llama2:7b",
  "prompt": "Hello, how are you?",
  "system_prompt": "You are a helpful assistant.",
  "options": {
    "temperature": 0.7,
    "max_tokens": 500
  },
  "stream": false
}
```

**Response**:
```json
{
  "id": "chat-123456",
  "model": "llama2:7b",
  "created": 1672531200,
  "content": "I'm doing well, thank you for asking! How can I assist you today?",
  "processing_time": 1.23
}
```

### Stream Chat Response

Streams a response from a model in real-time.

**Endpoint**: `POST /api/chat/completions`

**Request Body**:
```json
{
  "model_id": "llama2:7b",
  "prompt": "Write a poem about the ocean",
  "system_prompt": "You are a creative poet.",
  "options": {
    "temperature": 0.8,
    "max_tokens": 500
  },
  "stream": true
}
```

**Response**: Server-sent events with chunks of the generated text.

## WebSocket API

### Model Updates

Receive real-time updates about model status changes.

**Endpoint**: `WS /api/models/ws`

**Messages**:
- Model started
- Model stopped
- Model status changed
- Model metrics updated

## Error Handling

### Error Responses

All API errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK` - Request succeeded
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Invalid or missing API key
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - Ollama API error
- `503 Service Unavailable` - Ollama service not available

## Rate Limiting

API endpoints are rate-limited to prevent abuse. The default limit is 10 requests per minute for most endpoints.

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1672531260
```

## Pagination

For endpoints that return lists, pagination is supported:

**Query Parameters**:
- `page` - Page number (starting from 1)
- `page_size` - Number of items per page (default: 10, max: 100)

**Response Headers**:
```
X-Total-Count: 42
X-Page-Count: 5
X-Current-Page: 1
```

## Versioning

The API version is included in the URL path:

```
/api/v1/models/available
```

The current version is v1. When breaking changes are introduced, a new version will be created.

## Examples

### Example: List Models

**Request**:
```bash
curl -X GET "http://localhost:8000/api/models/available" -H "X-API-Key: SECRET_KEY"
```

**Response**:
```json
{
  "models": [
    {
      "id": "llama2:7b",
      "name": "Llama2",
      "size": "3.42 GB",
      "status": "running",
      "running": true,
      "metadata": {
        "digest": "sha256:123..."
      }
    },
    {
      "id": "mistral:7b",
      "name": "Mistral",
      "size": "4.1 GB",
      "status": "stopped",
      "running": false,
      "metadata": {
        "digest": "sha256:456..."
      }
    }
  ],
  "cache_hit": false
}
```

### Example: Send Chat Message

**Request**:
```bash
curl -X POST "http://localhost:8000/api/chat/completions" \
  -H "X-API-Key: SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "llama2:7b",
    "prompt": "What is the capital of France?",
    "options": {
      "temperature": 0.5
    }
  }'
```

**Response**:
```json
{
  "id": "chat-789012",
  "model": "llama2:7b",
  "created": 1672531300,
  "content": "The capital of France is Paris. Paris is located in the north-central part of the country on the Seine River.",
  "processing_time": 0.87
}
```

### Example: Create API Key

**Request**:
```bash
curl -X POST "http://localhost:8000/api/api-keys" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Development API Key",
    "expires_in_days": 30
  }'
```

**Response**:
```json
{
  "id": "key123",
  "name": "Development API Key",
  "key": "your-api-key-value",
  "created_at": "2025-05-08T12:00:00Z",
  "expires_at": "2025-06-07T12:00:00Z",
  "last_used_at": null,
  "is_active": true
}
```
