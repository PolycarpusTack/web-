# Getting Started with Web+

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** (3.10 or 3.11 recommended)
- **Node.js 18+** and npm
- **Git**
- **Ollama** (optional, for local AI models)

### Optional Tools
- **VS Code** (recommended IDE with included debug configurations)
- **Docker** (for containerized deployment)
- **PostgreSQL** (for production database)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/web-plus.git
cd web-plus
```

### 2. Set Up Python Virtual Environment

Web+ uses a single virtual environment in the project root:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up the Backend

```bash
cd apps/backend

# Run database migrations
alembic upgrade head

# Seed the database with sample data
python db/seed_data.py

# Start the backend server
python main.py
```

The backend will be available at `http://localhost:8000`

### 4. Set Up the Frontend

Open a new terminal and run:

```bash
cd apps/frontend

# Install Node dependencies
npm install

# Install Playwright browsers for E2E testing (optional)
npx playwright install

# Start the frontend development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 5. Default Credentials

The seed data includes these default users:

- **Admin User**
  - Username: `admin`
  - Password: `admin123!`
  
- **Test User**
  - Username: `testuser`
  - Password: `test123!`

- **Developer User**
  - Username: `developer`
  - Password: `dev123!`

## One-Command Start (Windows)

For Windows users, use the provided batch script:

```bash
start_web_plus.bat
```

This will:
1. Start the backend in a new window
2. Wait for backend initialization
3. Start the frontend in the current window

## VS Code Development

### Debugging

The project includes VS Code debug configurations:

1. **Backend: FastAPI** - Debug the Python backend
2. **Frontend: Vite** - Debug the React frontend in Chrome
3. **Full Stack** - Debug both frontend and backend simultaneously
4. **Backend: Tests** - Debug Python tests
5. **Frontend: Tests** - Debug JavaScript/TypeScript tests
6. **E2E: Playwright** - Debug end-to-end tests

To use debugging:
1. Open VS Code
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select a configuration from the dropdown
4. Press F5 to start debugging

### Tasks

VS Code tasks are available for common operations:
- `frontend:dev` - Start frontend dev server
- `backend:dev` - Start backend dev server
- `install:backend` - Install Python dependencies
- `install:frontend` - Install Node dependencies
- `test:backend` - Run Python tests
- `test:frontend` - Run JavaScript tests
- `lint:backend` - Lint Python code
- `lint:frontend` - Lint JavaScript/TypeScript code
- `db:migrate` - Run database migrations
- `db:seed` - Seed the database

## Testing

### Unit Tests

```bash
# Backend tests
cd apps/backend
pytest

# Frontend tests
cd apps/frontend
npm test
```

### End-to-End Tests

```bash
cd apps/frontend

# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run e2e

# Run E2E tests with UI
npm run e2e:ui

# Run E2E tests in headed mode
npm run e2e:headed
```

### Test Coverage

```bash
# Backend coverage
cd apps/backend
pytest --cov=. --cov-report=html

# Frontend coverage
cd apps/frontend
npm run test:coverage
```

## Environment Configuration

### Backend (.env)

Create `apps/backend/.env`:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./web_plus.db

# For PostgreSQL (production):
# DATABASE_URL=postgresql+asyncpg://user:password@localhost/webplus

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Redis (optional)
# REDIS_URL=redis://localhost:6379

# CORS
FRONTEND_URL=http://localhost:5173
```

### Frontend (.env)

Create `apps/frontend/.env`:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000

# Feature Flags
VITE_ENABLE_MOCK_API=false
```

## Production Deployment

### Using PostgreSQL

1. Install PostgreSQL
2. Create a database:
   ```sql
   CREATE DATABASE webplus;
   ```
3. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/webplus
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Building for Production

```bash
# Build frontend
cd apps/frontend
npm run build

# The built files will be in apps/frontend/dist
```

### Running in Production

```bash
# Backend with Gunicorn
cd apps/backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Or with Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
web-plus/
├── .venv/                    # Python virtual environment (root)
├── .vscode/                  # VS Code configurations
│   ├── launch.json          # Debug configurations
│   └── tasks.json           # Task definitions
├── apps/
│   ├── backend/             # FastAPI backend
│   │   ├── db/              # Database models and operations
│   │   ├── auth/            # Authentication system
│   │   ├── providers/       # AI provider integrations
│   │   ├── pipeline/        # Pipeline execution engine
│   │   ├── migrations/      # Alembic migrations
│   │   └── main.py          # Main application
│   └── frontend/            # React frontend
│       ├── src/             # Source code
│       ├── e2e/             # End-to-end tests
│       └── playwright.config.ts
├── docs/                    # Documentation
│   └── development-plan/    # Phase-based development plan
└── scripts/                 # Utility scripts
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure virtual environment is activated
   - Check DATABASE_URL in .env
   - Run migrations: `alembic upgrade head`

2. **Frontend Can't Connect to Backend**
   - Ensure backend is running on port 8000
   - Check CORS settings in backend
   - Verify VITE_API_BASE_URL in frontend .env

3. **Module Not Found Errors**
   - Ensure you're in the correct directory
   - Activate virtual environment
   - Reinstall dependencies

4. **Port Already in Use**
   - Backend: Change port in main.py or use `--port` flag
   - Frontend: Change port in vite.config.ts

### Getting Help

- Check the [API documentation](http://localhost:8000/docs) when backend is running
- Review error logs in terminal
- Check browser console for frontend errors
- Ensure all prerequisites are installed

## Next Steps

1. Explore the [User Guide](./user-guide.md)
2. Read the [Developer Guide](./developer-guide.md)
3. Check out the [API Reference](./api-reference.md)
4. Learn about [Pipeline Development](./development-plan/phase-3-pipeline-system/README.md)
5. Review the [Development Plan](./DEVELOPMENT_PLAN_COMPARISON_REPORT.md)