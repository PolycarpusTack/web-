# Web+ Launch Commands

## Option 1: All-in-one startup script

Run the provided start script:

```bash
cd /mnt/c/Projects/web-plus
./start.sh
```

This will start both backend and frontend services.

## Option 2: Launch services separately

### Start Backend

```bash
cd /mnt/c/Projects/web-plus
python3 scripts/run_backend.py
```

The backend will run on http://localhost:8000 with API documentation available at http://localhost:8000/docs.

### Start Frontend

```bash
cd /mnt/c/Projects/web-plus/apps/frontend
npm run dev
```

The frontend will run on http://localhost:5173.

## Prerequisites

1. Make sure Python 3.9+ is installed with required packages:
   ```bash
   pip install sqlalchemy fastapi uvicorn alembic pydantic-settings httpx cachetools prometheus-fastapi-instrumentator python-jose aiosqlite fastapi-limiter python-json-logger
   ```

2. Make sure Node.js and npm are installed:
   ```bash
   node --version  # Should be v16+ 
   npm --version   # Should be v7+
   ```

3. Optionally, start Ollama if you want to connect to LLM models:
   - Download from: https://ollama.ai/
   - Run Ollama before starting Web+

## Notes

- The frontend won't show any models if the backend is not running
- The backend won't connect to any models if Ollama is not running
- Some features might be limited without proper backend initialization