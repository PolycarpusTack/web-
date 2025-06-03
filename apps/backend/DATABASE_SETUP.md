# Web+ Database Setup Guide

This guide covers the complete database initialization and management system for Web+.

## Quick Start

### Windows
```bash
# Run the setup script
setup_database.bat
```

### Linux/macOS
```bash
# Quick setup
python setup_database.py

# Or use the full script
python -m db.init_database --init
```

## Database Scripts Overview

### 1. `setup_database.py` - Quick Setup (Recommended)
- Interactive setup script
- Automatically detects current state
- Guides you through the setup process
- Shows admin credentials at the end

### 2. `db/init_database.py` - Full Management Script
- Comprehensive database management
- Command-line interface with multiple options
- Backup and rollback capabilities
- Detailed logging

### 3. `test_db_connection.py` - Connection Testing
- Tests database connectivity
- Verifies both sync and async connections
- Creates basic tables if needed

## Database Management Commands

### Initialize Database (First Time Setup)
```bash
# Complete initialization with tables and seed data
python -m db.init_database --init

# Initialize with verbose logging
python -m db.init_database --init --verbose
```

### Check Database Status
```bash
# Check current database status
python -m db.init_database --check
```

### Add Seed Data Only
```bash
# Add seed data to existing database
python -m db.init_database --seed
```

### Reset Database (⚠️ Dangerous)
```bash
# Reset entire database (requires confirmation)
python -m db.init_database --reset --confirm
```

### Test Connection
```bash
# Test database connectivity
python test_db_connection.py
```

## Database Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database Configuration
DATABASE_URL=                              # Leave empty for SQLite (default)
# DATABASE_URL=postgresql://user:pass@localhost/webplus  # For PostgreSQL

# Security
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin User (created during setup)
ADMIN_EMAIL=admin@webplus.local
ADMIN_USERNAME=admin
ADMIN_PASSWORD=webplus123

# Optional Settings
SQL_ECHO=false                            # Set to true for SQL query logging
```

### Database Types

#### SQLite (Development - Default)
- File-based database: `web_plus.db`
- No additional setup required
- Automatically created on first run
- Perfect for development and testing

#### PostgreSQL (Production)
- Set `DATABASE_URL` in `.env` file
- Requires PostgreSQL server
- Better performance for production
- Supports concurrent users

## Default Data Created

### Admin User
- **Username**: admin
- **Email**: admin@webplus.local  
- **Password**: webplus123
- **Role**: admin
- **API Key**: Generated automatically

### Test Users (SQLite only)
- testuser1@webplus.local
- test2@webplus.local
- dev@webplus.local
- **Password**: testpass123

### Default Models
- **GPT-4** (OpenAI)
- **Claude 3 Opus** (Anthropic)
- **Llama 2 7B** (Meta/Ollama)
- **Code Llama 7B** (Meta/Ollama)
- **Mistral 7B Instruct** (Mistral/Ollama)

### Default Tags
- text-generation
- chat
- code
- multimodal
- reasoning
- creative
- analysis
- local
- api
- open-source
- proprietary

### Sample Data
- Welcome conversation with sample messages
- API keys for all users
- Model-tag associations

## Database Schema

### Core Tables
- **users** - User accounts and authentication
- **api_keys** - API authentication keys
- **models** - AI model definitions
- **conversations** - Chat conversations
- **messages** - Individual chat messages
- **files** - Uploaded files and attachments
- **tags** - Model categorization tags

### Junction Tables
- **user_conversation_association** - User-conversation relationships
- **model_tag_association** - Model-tag relationships
- **message_files** - Message-file attachments
- **message_threads** - Threaded conversations

## Backup and Recovery

### Automatic Backups (SQLite)
- Backups created before dangerous operations
- Timestamped backup files: `web_plus.db.backup_YYYYMMDD_HHMMSS`
- Automatic rollback on failure

### Manual Backup
```bash
# SQLite
cp web_plus.db web_plus.db.backup

# PostgreSQL
pg_dump webplus > webplus_backup.sql
```

### Restore from Backup
```bash
# SQLite
cp web_plus.db.backup web_plus.db

# PostgreSQL
psql webplus < webplus_backup.sql
```

## Troubleshooting

### Common Issues

#### 1. "Cannot import name 'engine'" Error
- **Solution**: Run `pip install -r requirements.txt` to update dependencies
- The database configuration was updated for SQLAlchemy 2.0+

#### 2. "Textual SQL expression should be declared as text()" Error
- **Fixed**: Updated to use `text()` function for raw SQL
- This is required by SQLAlchemy 2.0+

#### 3. Permission Errors on Windows
- **Solution**: Run Command Prompt as Administrator
- Or use the `install_windows.bat` script

#### 4. Database Connection Fails
- Check if PostgreSQL is running (if using PostgreSQL)
- Verify `DATABASE_URL` in `.env` file
- Check file permissions for SQLite

#### 5. Tables Already Exist Error
- **Solution**: Use `--check` to see current status
- Use `--seed` to add data only
- Use `--reset --confirm` to start fresh (⚠️ deletes all data)

### Debug Mode
```bash
# Enable verbose logging
python -m db.init_database --init --verbose

# Check what went wrong
tail -f database_init.log
```

### Reset Everything
```bash
# Delete database file (SQLite only)
rm web_plus.db*

# Reinitialize
python -m db.init_database --init
```

## Security Considerations

### Production Deployment
1. **Change default passwords**
   - Update `ADMIN_PASSWORD` in `.env`
   - Force password change on first login

2. **Use strong secrets**
   - Generate secure `SECRET_KEY`
   - Use long, random API keys

3. **Database security**
   - Use PostgreSQL for production
   - Enable SSL connections
   - Restrict database access

4. **Remove test data**
   - Delete test users in production
   - Remove sample conversations

## Migration from Old Schema

If upgrading from an older version:

1. **Backup current database**
2. **Check migration requirements**
3. **Use Alembic for schema changes**
4. **Test with a copy first**

```bash
# Create migration
alembic revision --autogenerate -m "Migration description"

# Apply migration
alembic upgrade head
```

## Performance Optimization

### SQLite Settings
- WAL mode enabled for better concurrency
- Optimized pragma settings
- Foreign key constraints enforced

### PostgreSQL Settings
- Connection pooling configured
- Proper indexes on frequently queried columns
- Query optimization for large datasets

## Monitoring and Maintenance

### Regular Tasks
- Monitor database size growth
- Clean up old conversations/messages
- Update model information
- Check for unused files

### Health Checks
```bash
# Quick health check
python -m db.init_database --check

# Detailed connection test
python test_db_connection.py
```