# Web+ Backend API

## Overview

The Web+ backend is a high-performance REST API built with FastAPI, providing robust endpoints for AI model management, chat completions, file handling, and pipeline automation. It features async operations, JWT authentication, and comprehensive database integration.

## Architecture

### Technology Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations
- **PostgreSQL/SQLite** - Database options
- **Redis** - Caching and session storage (optional)
- **JWT** - Authentication tokens
- **Pydantic** - Data validation
- **httpx** - Async HTTP client

### Project Structure

```
backend/
├── auth/            # Authentication module
├── core/            # Core configurations and middleware
├── db/              # Database models and operations
├── files/           # File handling module
├── migrations/      # Alembic database migrations
├── pipeline/        # Pipeline execution engine
├── routers/         # Additional API routes
├── scripts/         # Utility scripts
├── tests/           # Test suite
├── utils/           # Utility functions
└── main.py          # Application entry point
```

### Key Features

- **Async Architecture**: Full async/await support for high performance
- **JWT Authentication**: Secure token-based authentication
- **API Key Support**: Alternative authentication method
- **File Processing**: Upload, storage, and analysis capabilities
- **Pipeline Engine**: Execute complex AI workflows
- **Rate Limiting**: Configurable rate limits per user/endpoint
- **CORS Support**: Configurable cross-origin resource sharing
- **WebSocket Support**: Real-time communication channels
- **Database Flexibility**: Support for PostgreSQL and SQLite

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or SQLite for development)
- Redis (optional, for caching)

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python setup_database.py
```

### Environment Configuration

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/webplus
# For SQLite: DATABASE_URL=sqlite+aiosqlite:///./web_plus.db

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Configuration
API_HOST=0.0.0.0
API_PORT=8002
API_RELOAD=true

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=backend.log
```

## Development

### Running the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --port 8002

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4
```

### Database Management

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### API Documentation

Once running, interactive API documentation is available at:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py

# Run tests in parallel
pytest -n auto
```

## API Structure

### Authentication Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token
- `GET /auth/me` - Get current user
- `POST /auth/api-keys` - Create API key

### Model Management

- `GET /models/available` - List available models
- `POST /models/start` - Start a model
- `POST /models/stop` - Stop a model
- `GET /models/{id}/status` - Get model status

### Conversations

- `POST /conversations` - Create conversation
- `GET /conversations` - List conversations
- `GET /conversations/{id}` - Get conversation details
- `DELETE /conversations/{id}` - Delete conversation

### Chat Completions

- `POST /chat/completions` - Send message and get response
- `POST /chat/completions/stream` - Streaming responses

### File Management

- `POST /files/upload` - Upload single file
- `POST /files/upload-multiple` - Upload multiple files
- `GET /files/{id}` - Get file details
- `POST /files/{id}/analyze` - Analyze file content

### Pipelines

- `POST /pipelines` - Create pipeline
- `GET /pipelines` - List pipelines
- `POST /pipelines/{id}/execute` - Execute pipeline
- `GET /pipeline-executions/{id}` - Get execution status

## Database Schema

### Key Models

- **User** - User accounts and authentication
- **Conversation** - Chat conversations
- **Message** - Individual messages in conversations
- **Model** - AI model configurations
- **Pipeline** - Pipeline definitions
- **PipelineStep** - Individual pipeline steps
- **File** - Uploaded file metadata

### Migrations

Database schema is managed through Alembic migrations. Always create migrations for schema changes:

```bash
# After model changes
alembic revision --autogenerate -m "Add new field to User model"
alembic upgrade head
```

## Security

### Authentication

- JWT tokens for session management
- API keys for programmatic access
- Password hashing with bcrypt
- Rate limiting on auth endpoints

### Best Practices

1. Always validate input data with Pydantic
2. Use parameterized queries (SQLAlchemy handles this)
3. Implement proper CORS policies
4. Sanitize file uploads
5. Use environment variables for secrets
6. Enable HTTPS in production

## Performance Optimization

### Database

- Use connection pooling
- Add appropriate indexes
- Use eager loading for relationships
- Implement query result caching

### API

- Use async operations throughout
- Implement response caching where appropriate
- Use pagination for list endpoints
- Optimize file handling with streaming

### Monitoring

- Use structured logging
- Implement health check endpoints
- Monitor response times
- Track error rates

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Production Considerations

1. Use a production ASGI server (uvicorn with gunicorn)
2. Enable HTTPS with proper certificates
3. Set up proper logging and monitoring
4. Use a production database (PostgreSQL)
5. Implement backup strategies
6. Set up CI/CD pipelines

### Environment Variables (Production)

- Set strong `JWT_SECRET_KEY`
- Disable `API_RELOAD`
- Set appropriate `LOG_LEVEL`
- Configure production database URL
- Set up Redis for caching
- Configure rate limits

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database is running
   # For PostgreSQL:
   pg_isready
   # Check connection string format
   ```

2. **Migration Errors**
   ```bash
   # Reset migrations
   alembic downgrade base
   alembic upgrade head
   ```

3. **Import Errors**
   ```bash
   # Ensure virtual environment is activated
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Performance Issues**
   - Check for N+1 queries
   - Review async operation usage
   - Monitor database query times
   - Check for blocking I/O operations

## Contributing

See the main [CONTRIBUTING.md](../../CONTRIBUTING.md) for general guidelines.

### Backend-Specific Guidelines

1. Write async code where possible
2. Add appropriate type hints
3. Create Pydantic schemas for all endpoints
4. Write comprehensive tests
5. Document API changes in OpenAPI schema
6. Follow PEP 8 style guidelines

## License

This project is part of Web+ and follows the same license terms.