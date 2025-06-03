# Web+ API Reference

This document provides a comprehensive reference for the Web+ API endpoints.

## Base URL

The base URL for all API endpoints is:

```
http://localhost:8000
```

For production deployments, this will be your production domain.

## Authentication

The API supports two authentication methods:

### API Key Authentication

```
X-API-Key: your_api_key
```

### JWT Token Authentication

```
Authorization: Bearer your_jwt_token
```

Most endpoints can use either method. Some user-specific endpoints require JWT authentication.

## Error Handling

All API errors follow this format:

```json
{
  "error": "Error message",
  "message": "Human-readable error message",
  "code": "error_code",
  "details": {
    "field1": "Error details for field1",
    "field2": "Error details for field2"
  }
}
```

Common error codes:

| Code | Description |
|------|-------------|
| `invalid_credentials` | Invalid username or password |
| `invalid_token` | Invalid or expired token |
| `permission_denied` | Insufficient permissions |
| `resource_not_found` | Requested resource not found |
| `validation_error` | Input validation failed |
| `database_error` | Database operation failed |
| `rate_limit_exceeded` | Too many requests |

## Pagination

For endpoints that return lists, pagination is supported:

**Query Parameters**:
- `page` - Page number (starting from 1, default: 1)
- `page_size` - Number of items per page (default: 20, max: 100)

**Response Format**:
```json
{
  "items": [...],
  "metadata": {
    "page": 1,
    "page_size": 20,
    "total_items": 42,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

## API Endpoints

### Authentication API

#### Register a New User

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
  "is_verified": false,
  "created_at": "2025-05-08T12:00:00Z",
  "updated_at": "2025-05-08T12:00:00Z",
  "role": "user"
}
```

#### Login

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

#### Refresh Token

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

#### Get Current User

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
  "is_verified": false,
  "created_at": "2025-05-08T12:00:00Z",
  "updated_at": "2025-05-08T12:00:00Z",
  "role": "user"
}
```

#### Update Current User

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
  "is_verified": false,
  "created_at": "2025-05-08T12:00:00Z",
  "updated_at": "2025-05-08T12:05:00Z",
  "role": "user"
}
```

#### Change Password

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

### API Key Management

#### Create API Key

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

#### List API Keys

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

#### Revoke API Key

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

#### Delete API Key

Delete an API key.

**Endpoint**: `DELETE /api/api-keys/{api_key_id}`

**Authentication**: JWT token required

**Response**: `204 No Content`

### Models API

#### List Available Models

Retrieves a list of all available models.

**Endpoint**: `GET /api/models/available`

**Query Parameters**:
- `use_cache` (optional): Boolean flag to control cache usage (default: true)
- `provider` (optional): Filter models by provider

**Response**:
```json
{
  "models": [
    {
      "id": "llama2:7b",
      "name": "Llama2",
      "provider": "ollama",
      "size": "3.42 GB",
      "status": "running",
      "running": true,
      "is_active": true,
      "description": "Meta's Llama 2 7B parameter model",
      "version": "2.0",
      "context_window": 4096,
      "metadata": {
        "digest": "sha256:123..."
      }
    },
    ...
  ],
  "cache_hit": true
}
```

#### Start Model

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

#### Stop Model

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

#### Get Model Details

Gets detailed information about a specific model.

**Endpoint**: `GET /api/models/{model_id}`

**Response**:
```json
{
  "id": "llama2:7b",
  "name": "Llama2",
  "provider": "ollama",
  "size": "3.42 GB",
  "status": "running",
  "running": true,
  "is_active": true,
  "description": "Meta's Llama 2 7B parameter model",
  "version": "2.0",
  "context_window": 4096,
  "max_output_tokens": 2048,
  "capabilities": {
    "chat": true,
    "code": true,
    "vision": false
  },
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9
  },
  "metadata": {
    "digest": "sha256:123..."
  }
}
```

### Chat API

#### Create a Conversation

Create a new conversation.

**Endpoint**: `POST /api/chat/conversations`

**Request Body**:
```json
{
  "model_id": "llama2:7b",
  "title": "New Conversation",
  "system_prompt": "You are a helpful assistant."
}
```

**Response**:
```json
{
  "id": "conv123",
  "title": "New Conversation",
  "model_id": "llama2:7b",
  "created_at": "2025-05-08T12:00:00Z",
  "updated_at": "2025-05-08T12:00:00Z",
  "system_prompt": "You are a helpful assistant."
}
```

#### List Conversations

Get a list of conversations for the current user.

**Endpoint**: `GET /api/chat/conversations`

**Query Parameters**:
- `model_id` (optional): Filter by model
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response**:
```json
{
  "conversations": [
    {
      "id": "conv123",
      "title": "New Conversation",
      "model_id": "llama2:7b",
      "created_at": "2025-05-08T12:00:00Z",
      "updated_at": "2025-05-08T12:05:00Z",
      "message_count": 5
    },
    ...
  ]
}
```

#### Get Conversation

Get a conversation with its messages.

**Endpoint**: `GET /api/chat/conversations/{conversation_id}`

**Response**:
```json
{
  "id": "conv123",
  "title": "New Conversation",
  "model_id": "llama2:7b",
  "created_at": "2025-05-08T12:00:00Z",
  "updated_at": "2025-05-08T12:05:00Z",
  "system_prompt": "You are a helpful assistant.",
  "messages": [
    {
      "id": "msg1",
      "role": "user",
      "content": "Hello!",
      "created_at": "2025-05-08T12:01:00Z",
      "tokens": 1,
      "cost": 0.00001
    },
    {
      "id": "msg2",
      "role": "assistant",
      "content": "Hello! How can I help you today?",
      "created_at": "2025-05-08T12:01:05Z",
      "tokens": 8,
      "cost": 0.00016
    },
    ...
  ],
  "files": [
    {
      "id": "file1",
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024000,
      "created_at": "2025-05-08T12:02:00Z",
      "is_public": false
    }
  ]
}
```

#### Send Chat Message

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
  "stream": false,
  "conversation_id": "conv123"
}
```

**Response**:
```json
{
  "id": "msg3",
  "model": "llama2:7b",
  "created": 1714291200,
  "content": "I'm doing well, thank you for asking! How can I assist you today?",
  "processing_time": 1.23,
  "usage": {
    "prompt_tokens": 4,
    "completion_tokens": 13,
    "total_tokens": 17,
    "prompt_cost": 0.00004,
    "completion_cost": 0.00026,
    "total_cost": 0.0003
  },
  "conversation_id": "conv123"
}
```

### Message Threads API

#### Create a Thread

Create a new message thread in a conversation.

**Endpoint**: `POST /api/chat/threads`

**Request Body**:
```json
{
  "conversation_id": "conv123",
  "title": "Discussion about feature",
  "parent_thread_id": null
}
```

**Response**:
```json
{
  "id": "thread1",
  "conversation_id": "conv123",
  "title": "Discussion about feature",
  "created_at": "2025-05-08T12:10:00Z",
  "updated_at": "2025-05-08T12:10:00Z",
  "creator_id": "user123",
  "parent_thread_id": null,
  "metadata": null
}
```

#### Get Thread

Get a thread with its messages.

**Endpoint**: `GET /api/chat/threads/{thread_id}`

**Response**:
```json
{
  "id": "thread1",
  "conversation_id": "conv123",
  "title": "Discussion about feature",
  "created_at": "2025-05-08T12:10:00Z",
  "updated_at": "2025-05-08T12:15:00Z",
  "creator_id": "user123",
  "parent_thread_id": null,
  "metadata": null,
  "messages": [
    {
      "id": "msg4",
      "role": "user",
      "content": "Let's discuss this feature.",
      "created_at": "2025-05-08T12:11:00Z",
      "tokens": 5,
      "cost": 0.00005,
      "thread_id": "thread1"
    },
    {
      "id": "msg5",
      "role": "assistant",
      "content": "Sure, what aspects of the feature would you like to discuss?",
      "created_at": "2025-05-08T12:11:05Z",
      "tokens": 11,
      "cost": 0.00022,
      "thread_id": "thread1"
    }
  ]
}
```

#### List Threads for Conversation

Get all threads for a conversation.

**Endpoint**: `GET /api/chat/conversations/{conversation_id}/threads`

**Response**:
```json
{
  "threads": [
    {
      "id": "thread1",
      "conversation_id": "conv123",
      "title": "Discussion about feature",
      "created_at": "2025-05-08T12:10:00Z",
      "updated_at": "2025-05-08T12:15:00Z",
      "creator_id": "user123",
      "parent_thread_id": null,
      "metadata": null
    },
    ...
  ]
}
```

#### Send Message to Thread

Send a message to a thread.

**Endpoint**: `POST /api/chat/threads/{thread_id}/completions`

**Request Body**:
```json
{
  "model_id": "llama2:7b",
  "prompt": "What do you think about this approach?",
  "options": {
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

**Response**: Same as chat completions response, with `thread_id` included.

### Files API

#### Upload File

Upload a file.

**Endpoint**: `POST /api/files/upload`

**Content-Type**: `multipart/form-data`

**Form Data**:
- `file`: The file to upload
- `conversation_id` (optional): ID of the conversation
- `description` (optional): File description

**Response**:
```json
{
  "id": "file1",
  "filename": "abc123.pdf",
  "original_filename": "document.pdf",
  "content_type": "application/pdf",
  "size": 1024000,
  "created_at": "2025-05-08T12:20:00Z",
  "user_id": "user123",
  "conversation_id": "conv123",
  "is_public": false,
  "analyzed": false
}
```

#### Get File

Get a file's content.

**Endpoint**: `GET /api/files/{file_id}`

**Response**: The file content with appropriate Content-Type header.

#### Get File Info

Get file metadata without downloading the file.

**Endpoint**: `GET /api/files/{file_id}/info`

**Response**:
```json
{
  "id": "file1",
  "filename": "abc123.pdf",
  "original_filename": "document.pdf",
  "content_type": "application/pdf",
  "size": 1024000,
  "created_at": "2025-05-08T12:20:00Z",
  "user_id": "user123",
  "conversation_id": "conv123",
  "is_public": false,
  "analyzed": false
}
```

#### Delete File

Delete a file.

**Endpoint**: `DELETE /api/files/{file_id}`

**Response**: `204 No Content`

#### Analyze File

Request analysis of a file.

**Endpoint**: `POST /api/files/{file_id}/analyze`

**Response**:
```json
{
  "id": "file1",
  "analyzed": true,
  "analysis_status": "completed",
  "analysis_result": {
    "summary": "This document discusses the implementation of AI models...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "topics": ["AI", "Machine Learning", "Implementation"],
    "sentiment": "neutral",
    "language": "en",
    "entities": [
      {"name": "GPT-4", "type": "MODEL"},
      {"name": "Microsoft", "type": "ORGANIZATION"}
    ]
  },
  "extracted_text": "The first few lines of extracted text...",
  "extraction_quality": 0.95
}
```

For large files, the analysis may be initiated asynchronously:

```json
{
  "id": "file1",
  "analyzed": false,
  "analysis_status": "in_progress",
  "progress": 0.2,
  "estimated_completion_time": "2025-05-08T12:25:00Z"
}
```

#### Get File Analysis

Get analysis results for a file.

**Endpoint**: `GET /api/files/{file_id}/analysis`

**Response**: Same format as the analyze file response.

#### Get Extracted Text

Get only the extracted text from a file.

**Endpoint**: `GET /api/files/{file_id}/text`

**Query Parameters**:
- `offset` (optional): Character offset to start from (default: 0)
- `limit` (optional): Maximum number of characters to return (default: 10000)

**Response**:
```json
{
  "id": "file1",
  "extraction_status": "completed",
  "extracted_text": "The extracted text content...",
  "total_length": 56789,
  "offset": 0,
  "limit": 10000,
  "has_more": true
}
```

### WebSocket API

#### Model Updates

Receive real-time updates about model status changes.

**Endpoint**: `WS /api/models/ws`

**Messages**:
- Model started
- Model stopped
- Model status changed
- Model metrics updated

**Example Message**:
```json
{
  "event": "model_status_changed",
  "data": {
    "model_id": "llama2:7b",
    "status": "running",
    "timestamp": "2025-05-08T12:30:00Z"
  }
}
```

#### Chat Message Streaming

Receive streamed responses for chat completions.

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
  "stream": true,
  "conversation_id": "conv123"
}
```

**Response**: Server-sent events with chunks of the generated text.

**Example Chunk**:
```json
{
  "id": "msg6",
  "delta": "The ocean",
  "finished": false
}
```

**Final Chunk**:
```json
{
  "id": "msg6",
  "delta": ".",
  "finished": true,
  "usage": {
    "prompt_tokens": 7,
    "completion_tokens": 50,
    "total_tokens": 57,
    "prompt_cost": 0.00007,
    "completion_cost": 0.001,
    "total_cost": 0.00107
  }
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse. The default limit is:

- 60 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1714291260
```

## Versioning

The API version is included in the URL path:

```
/api/v1/models/available
```

The current version is v1. When breaking changes are introduced, a new version will be created.

## Best Practices

1. **Authentication**: Always use API key or JWT token for authentication
2. **Error Handling**: Handle error responses appropriately
3. **Rate Limiting**: Respect rate limits and implement backoff strategies
4. **Conversation Management**: Use threads for organizing related messages
5. **File Analysis**: Implement polling for large file analysis
