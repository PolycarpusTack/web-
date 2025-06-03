# Developer Guide

This guide provides detailed information for developers working on the web-plus project. It covers the project architecture, key components, and development workflows.

## Development Environment Setup

### Setting up the Backend

1. Create a Python virtual environment:
   ```bash
   cd apps/backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Running the development server:
   ```bash
   python main.py
   ```

   This will start the FastAPI server on port 8000.

4. Access the API documentation:
   - OpenAPI docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Setting up the Frontend

1. Install Node.js dependencies:
   ```bash
   cd apps/frontend
   npm install
   # or
   pnpm install
   ```

2. Running the development server:
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

   This will start the Vite dev server on port 5173.

3. Building for production:
   ```bash
   npm run build
   # or
   pnpm build
   ```

## Architecture

### Backend Architecture

The backend follows a modular architecture based on FastAPI:

- `main.py` - The entry point and application setup
- API routes are organized into routers (models, chat, etc.)
- Database integration is planned but not implemented yet
- Authentication is handled via API keys

#### API Design

The API follows RESTful principles:

- Resources are addressed via URLs
- HTTP methods are used appropriately (GET, POST, etc.)
- JSON is used for request and response bodies
- Error handling is consistent with proper status codes

#### Model Management

- Models are fetched from Ollama instance
- Caching is used to improve performance
- WebSockets provide real-time updates

### Frontend Architecture

The frontend follows a component-based architecture using React:

- TypeScript is used for type safety
- Functional components with hooks for state management
- API clients for backend communication
- shadcn/ui components for UI elements

#### Component Structure

- `src/components` - Reusable UI components
- `src/app` - App-specific components and pages
- `src/api` - API clients
- `src/hooks` - Custom React hooks
- `src/lib` - Utility functions

#### State Management

- React hooks (`useState`, `useReducer`, `useContext`) for state
- Custom hooks for shared functionality
- Component composition for UI organization

## Key Features Implementation

### 1. Ollama Integration

The application communicates with Ollama to:

- List available models
- Start and stop models
- Send chat requests to models

Implementation details:

- HTTP client (httpx) is used for API calls
- Requests are proxied through the backend for security
- Response formats are normalized for consistent UI

### 2. Chat Interface

The chat interface provides:

- Real-time messaging with LLMs
- Context preservation
- Message history

Implementation details:

- Messages are stored in state
- Streaming responses (planned)
- WebSockets for real-time updates (planned)

### 3. Code Factory Pipeline

The Code Factory pipeline allows:

- Configuring multiple LLMs for different roles
- Sequential processing of inputs
- Visualization of the pipeline

Implementation details:

- Pipeline configuration stored in state
- Sequential API calls for each step
- Progress tracking and visualization

## Testing

### Backend Testing

- Use pytest for unit and integration tests
- Mock external services (Ollama API)
- Test API endpoints with TestClient

Example:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_models():
    response = client.get("/api/models/available")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
```

### Frontend Testing

- Use Vitest for unit tests
- React Testing Library for component tests
- Mock API requests with MSW

Example:
```typescript
import { render, screen } from '@testing-library/react';
import { ModelCard } from './ModelCard';

test('renders model card', () => {
  render(
    <ModelCard 
      id="test-model" 
      name="Test Model" 
      running={true} 
    />
  );
  
  expect(screen.getByText('Test Model')).toBeInTheDocument();
  expect(screen.getByText('Actief')).toBeInTheDocument();
});
```

## Code Conventions

### TypeScript Conventions

- Use explicit types for function parameters and return values
- Use interfaces for complex objects
- Use type inference where appropriate
- Avoid using `any` type

### React Conventions

- Use functional components
- Use hooks for state and side effects
- Split components into smaller, focused components
- Use named exports for components

### Python Conventions

- Follow PEP 8 style guidelines
- Use type hints
- Use f-strings for string formatting
- Use async/await for asynchronous code

## Performance Optimization

### Backend Optimization

- Use caching for expensive operations
- Limit API call frequency
- Use database indexes for faster queries (when implemented)
- Optimize WebSocket connections

### Frontend Optimization

- Use React.memo for expensive components
- Implement virtualization for long lists
- Optimize network requests with caching
- Use proper bundle splitting

## Deployment

### Backend Deployment

- Deploy as a Docker container
- Use Uvicorn for production server
- Set environment variables for configuration
- Use a reverse proxy (Nginx) for SSL termination

### Frontend Deployment

- Build the static assets
- Host on a CDN or static hosting service
- Configure for production environment
- Use environment variables for API URLs

## Troubleshooting

### Common Backend Issues

- Ollama not running
- Incorrect API keys
- Rate limiting
- Memory leaks in long-running processes

### Common Frontend Issues

- CORS errors
- State management complexity
- API response handling
- Type errors in TypeScript

## Contributing Guidelines

1. Always create a feature branch for new work
2. Use descriptive commit messages
3. Write tests for new features
4. Update documentation
5. Follow code style conventions
6. Create pull requests for code reviews
