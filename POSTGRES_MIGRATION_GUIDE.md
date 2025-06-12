# PostgreSQL Setup for Web+

## 1. Install PostgreSQL Dependencies

First, let's update the backend requirements to include PostgreSQL support:

```bash
pip install asyncpg psycopg2-binary
```

## 2. PostgreSQL Installation

### Option A: Using Docker (Recommended)
Create a `docker-compose.postgres.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: webplus_postgres
    environment:
      POSTGRES_USER: webplus
      POSTGRES_PASSWORD: webplus_dev_2024
      POSTGRES_DB: webplus_db
    ports:
      - "5432:5432"
    volumes:
      - webplus_postgres_data:/var/lib/postgresql/data

volumes:
  webplus_postgres_data:
```

Start with: `docker-compose -f docker-compose.postgres.yml up -d`

### Option B: Local PostgreSQL Installation
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Create database and user:
   ```sql
   CREATE USER webplus WITH PASSWORD 'webplus_dev_2024';
   CREATE DATABASE webplus_db OWNER webplus;
   GRANT ALL PRIVILEGES ON DATABASE webplus_db TO webplus;
   ```

## 3. Update Environment Configuration

Update `apps/backend/.env`:

```env
# Change from SQLite to PostgreSQL
WEBPLUS_DATABASE_URL=postgresql+asyncpg://webplus:webplus_dev_2024@localhost:5432/webplus_db

# For synchronous operations (migrations)
WEBPLUS_SYNC_DATABASE_URL=postgresql://webplus:webplus_dev_2024@localhost:5432/webplus_db
```

## 4. Update Database Configuration

The existing `database.py` should work, but let's ensure it handles both async and sync URLs properly.

## 5. Migration Steps

1. Create initial migration
2. Apply migrations
3. Seed initial data
