# Web+ PostgreSQL Migration Plan

## Why Switch to PostgreSQL?

1. **Resolves Current Issues**:
   - Fixes SQLAlchemy async dialect errors (`sqlite+aiosqlite` issues)
   - Eliminates SQLite connection/concurrency limitations
   - Better async support with `asyncpg`

2. **Better for Production**:
   - Handles multiple connections properly
   - Better performance under load
   - Full ACID compliance
   - Better data integrity

## Migration Steps

### Step 1: Install PostgreSQL

#### Option A: Using Docker (Recommended for Development)
```bash
# Start PostgreSQL with Docker Compose
docker-compose -f docker-compose.postgres.yml up -d

# This will:
# - Start PostgreSQL on port 5432
# - Create database: webplus_db
# - Create user: webplus with password: webplus_dev_2024
# - Start pgAdmin on port 5050 (optional GUI)
```

#### Option B: Local Installation
1. Download from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Create user and database manually

### Step 2: Install Python Dependencies
```bash
cd apps/backend
pip install asyncpg psycopg2-binary
```

### Step 3: Update Configuration

Update `apps/backend/.env`:
```env
# Replace SQLite URL with PostgreSQL
WEBPLUS_DATABASE_URL=postgresql+asyncpg://webplus:webplus_dev_2024@localhost:5432/webplus_db
```

### Step 4: Run Migration
```bash
# From project root
python migrate_to_postgres.py
```

### Step 5: Start Application
```bash
# Use the new startup script
start_with_postgres.bat

# Or manually:
# 1. Start PostgreSQL (if not using Docker)
# 2. Start backend: cd apps/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8002
# 3. Start frontend: cd apps/frontend && npm run dev
```

## Verification

1. Check PostgreSQL is running:
   ```bash
   docker ps  # Should show webplus_postgres container
   ```

2. Access pgAdmin (if using Docker):
   - URL: http://localhost:5050
   - Email: admin@webplus.local
   - Password: admin

3. Test the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8002/docs

## Rollback Plan

If you need to switch back to SQLite:
1. Update `apps/backend/.env` back to SQLite URL
2. Restart the application

## Benefits You'll See

1. **No more 500 errors** on `/api/models/available`
2. **Better performance** with concurrent requests
3. **Reliable async operations**
4. **Professional database management** with pgAdmin

## Next Steps After Migration

1. Set up proper database backups
2. Configure connection pooling for production
3. Add database monitoring
4. Set up proper migrations with Alembic

The PostgreSQL migration should resolve your current SQLAlchemy issues and provide a more robust foundation for the Web+ application.
