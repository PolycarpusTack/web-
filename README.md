# Codex Machina Web+

A modern web application for managing and interacting with large language models. This application provides an interface for managing local Ollama models, chatting with LLMs, and creating automated AI pipelines.

## Features

- **LLM Manager**: View, start, stop, and monitor your Ollama models
- **Chatbot Interface**: Have conversations with your preferred AI models
- **Code Factory**: Create automated pipelines of LLMs for complex tasks

## Architecture

### Backend

The backend is built with Python FastAPI and provides the following features:

- RESTful API for model management
- Chat functionality with LLMs
- WebSocket support for real-time updates
- Caching for better performance
- Rate limiting and authentication

### Frontend

The frontend is built with React, TypeScript, and modern tooling:

- Vite for fast development and optimized builds
- TypeScript for type safety
- Tailwind CSS for styling
- shadcn/ui components for UI elements

## Getting Started

### Prerequisites

- Node.js 16+ and npm/pnpm
- Python 3.9+
- [Ollama](https://ollama.ai/) installed and running

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/web-plus.git
   cd web-plus
   ```

2. Install backend dependencies
   ```
   cd apps/backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Initialize the database
   ```
   python -m db.init_db
   ```

4. Install frontend dependencies
   ```
   cd ../frontend
   npm install
   # or
   pnpm install
   ```

### Running the Application

1. Start the backend server
   ```
   cd apps/backend
   python main.py
   ```

2. Start the frontend development server
   ```
   cd ../frontend
   npm run dev
   # or
   pnpm dev
   ```

3. Open your browser and navigate to `http://localhost:5173`

## Project Structure

```
web-plus/
│
├── apps/
│   ├── backend/              # Python FastAPI backend
│   │   ├── .venv/            # Python virtual environment
│   │   ├── db/               # Database models and operations
│   │   │   ├── models.py     # SQLAlchemy models
│   │   │   ├── crud.py       # CRUD operations
│   │   │   ├── database.py   # Database configuration
│   │   │   └── init_db.py    # Database initialization
│   │   ├── migrations/       # Alembic migrations
│   │   ├── main.py           # Main FastAPI application
│   │   └── requirements.txt  # Python dependencies
│   │
│   ├── frontend/             # React/TypeScript frontend
│   │   ├── src/              # Source code
│   │   │   ├── api/          # API clients
│   │   │   ├── app/          # App-specific components
│   │   │   ├── components/   # Reusable UI components
│   │   │   ├── hooks/        # Custom React hooks
│   │   │   └── lib/          # Utility functions
│   │   ├── public/           # Static assets
│   │   ├── index.html        # HTML template
│   │   ├── vite.config.ts    # Vite configuration
│   │   └── package.json      # Node dependencies
│   │
│   └── frontend-old/         # Legacy frontend (to be migrated)
│
├── docs/                     # Project documentation
│   ├── api-reference.md      # API documentation
│   ├── developer-guide.md    # Guide for developers
│   └── user-guide.md         # Guide for end users
│
├── shared/                   # Shared code and types
├── scripts/                  # Utility scripts
│
├── postcss.config.js         # PostCSS configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── provision_web.sh          # Setup script
└── README.md                 # Project documentation
```

## Core Functionality

### 1. LLM Manager

The LLM Manager allows you to:

- View all installed Ollama models
- Start and stop models
- View detailed information about each model
- Monitor model usage and performance
- Add external API-based models (OpenAI, Anthropic, etc.)

### 2. Chatbot Interface

The Chatbot Interface provides:

- Ability to select any available model for conversation
- Real-time chat with context preservation
- Code highlighting for programming responses
- Conversation history saving and management
- Customizable model parameters (temperature, max tokens, etc.)

### 3. Code Factory Pipeline

The Code Factory feature enables:

- Creating pipelines of specialized LLMs for complex tasks
- Assigning different roles to each LLM in the pipeline
- Configuring the workflow between models
- Visualization of the pipeline process
- Saving and reusing pipeline configurations

## API Documentation

### Model Management API

- `GET /api/models/available` - List all available models
- `POST /api/models/start` - Start a model
- `POST /api/models/stop` - Stop a model
- `GET /api/models/{id}` - Get detailed information about a model

### Chat API

- `POST /api/chat/completions` - Send a message to a model and get a response
- `GET /api/chat/history/{modelId}` - Get conversation history for a model
- `WS /api/models/ws` - WebSocket endpoint for real-time model updates

## Development Roadmap

### Phase 1: Database Integration ✅
- Implement SQLAlchemy with async support
- Create database models for all entities
- Enhance API endpoints to use the database
- Add conversation persistence
- Implement usage tracking

### Phase 2: Authentication & Frontend Integration
- Implement JWT-based authentication
- User registration and login flows
- Profile management
- Update frontend to use new endpoints
- Enhance UI for conversations

### Phase 3: Enhanced Chat Interface
- Conversation history UI
- Message threading
- Code highlighting improvements
- Model parameter configuration
- File uploads and processing

### Phase 4: Code Factory Pipeline
- Pipeline builder UI
- Pipeline execution engine
- Step visualization
- Pipeline templates
- Result formatting

### Phase 5: Enhanced Model Management
- External API integration (OpenAI, Anthropic)
- Model performance metrics
- Usage dashboards
- Cost management

### Phase 6: Production Preparation
- Performance optimization
- Security audit
- Documentation updates
- Deployment configurations

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
# web-
