#!/usr/bin/env python3
"""
Complete Database Initialization and Migration Script for Web+

This script handles:
1. Database existence checks
2. Table creation from models
3. Initial seed data for testing
4. Both SQLite (dev) and PostgreSQL (prod) support
5. Rollback capability
6. Proper logging and error handling
7. Idempotent operations (safe to run multiple times)

Usage:
    python -m db.init_database --help
    python -m db.init_database --init          # Initialize with default data
    python -m db.init_database --seed          # Add seed data only
    python -m db.init_database --reset         # Reset database (dangerous!)
    python -m db.init_database --check         # Check database status
"""

import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import secrets
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database imports
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError, OperationalError
from passlib.context import CryptContext

# Local imports
from db.database import (
    Base, 
    async_engine, 
    sync_engine,
    async_session_maker,
    sync_session_maker,
    get_async_session,
    test_async_connection,
    test_sync_connection,
    IS_SQLITE,
    DB_FILE,
    ASYNC_DATABASE_URL,
    SYNC_DATABASE_URL,
    close_async_db,
    close_sync_db,
)

from db.models import (
    User, APIKey, Model, Tag, Conversation, Message, 
    File, MessageFile, MessageThread, model_tag_association
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_init.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Password handling
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DatabaseManager:
    """Manages database initialization, migration, and seeding operations."""
    
    def __init__(self):
        self.backup_file = None
        self.rollback_data = {}
    
    async def check_database_exists(self) -> bool:
        """Check if database exists and is accessible."""
        try:
            if IS_SQLITE:
                exists = os.path.exists(DB_FILE)
                logger.info(f"SQLite database {'exists' if exists else 'does not exist'}: {DB_FILE}")
                return exists
            else:
                # For PostgreSQL, try to connect
                connection_ok = await test_async_connection()
                logger.info(f"PostgreSQL database {'accessible' if connection_ok else 'not accessible'}")
                return connection_ok
        except Exception as e:
            logger.error(f"Error checking database existence: {e}")
            return False
    
    async def check_tables_exist(self) -> Dict[str, bool]:
        """Check which tables exist in the database."""
        tables_status = {}
        expected_tables = [
            'users', 'api_keys', 'models', 'tags', 'conversations', 
            'messages', 'files', 'message_files', 'message_threads',
            'model_tag_association', 'user_conversation_association'
        ]
        
        try:
            async with async_session_maker() as session:
                # Use inspector to check existing tables
                inspector = inspect(sync_engine)
                existing_tables = inspector.get_table_names()
                
                for table in expected_tables:
                    tables_status[table] = table in existing_tables
                    
                logger.info(f"Table status check complete. Found {len(existing_tables)} tables.")
                return tables_status
                
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            # Return all False if we can't check
            return {table: False for table in expected_tables}
    
    async def create_backup(self) -> Optional[str]:
        """Create a backup before making changes (SQLite only)."""
        if not IS_SQLITE or not os.path.exists(DB_FILE):
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{DB_FILE}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(DB_FILE, backup_file)
            
            self.backup_file = backup_file
            logger.info(f"Created backup: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    async def rollback_from_backup(self) -> bool:
        """Restore from backup if available."""
        if not self.backup_file or not os.path.exists(self.backup_file):
            logger.warning("No backup file available for rollback")
            return False
            
        try:
            import shutil
            shutil.copy2(self.backup_file, DB_FILE)
            logger.info(f"Restored from backup: {self.backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback from backup: {e}")
            return False
    
    async def create_tables(self) -> bool:
        """Create all tables from models."""
        try:
            logger.info("Creating database tables...")
            
            # Create all tables
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Successfully created all tables")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    async def drop_all_tables(self) -> bool:
        """Drop all tables (for reset operations)."""
        try:
            logger.warning("Dropping all database tables...")
            
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("Successfully dropped all tables")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            return False
    
    async def create_admin_user(self, session) -> User:
        """Create the default admin user."""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@webplus.local")
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "webplus123")
        
        # Check if admin already exists
        result = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email}
        )
        existing_admin = result.fetchone()
        
        if existing_admin:
            logger.info(f"Admin user already exists: {admin_username}")
            # Return the existing admin
            result = await session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": admin_email}
            )
            admin_data = result.fetchone()
            return admin_data
        
        # Create new admin user
        hashed_password = pwd_context.hash(admin_password)
        
        admin_user = User(
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            full_name="System Administrator",
            is_active=True,
            is_verified=True,
            role="admin",
            preferences={
                "theme": "light",
                "notifications": True,
                "default_model": "gpt-4"
            }
        )
        
        session.add(admin_user)
        await session.flush()  # Get the ID
        
        logger.info(f"Created admin user: {admin_username} ({admin_email})")
        logger.info(f"Admin password: {admin_password}")
        
        return admin_user
    
    async def create_api_key_for_user(self, session, user: User) -> APIKey:
        """Create an API key for a user."""
        api_key_value = f"wp_{secrets.token_urlsafe(32)}"
        
        api_key = APIKey(
            key=api_key_value,
            name="Default API Key",
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year
            is_active=True
        )
        
        session.add(api_key)
        await session.flush()
        
        logger.info(f"Created API key for user {user.username}: {api_key_value}")
        return api_key
    
    async def create_default_tags(self, session) -> List[Tag]:
        """Create default tags for models."""
        default_tags = [
            {"name": "text-generation", "description": "Models capable of generating text"},
            {"name": "chat", "description": "Models optimized for conversational AI"},
            {"name": "code", "description": "Models specialized for code generation and analysis"},
            {"name": "multimodal", "description": "Models that can process multiple input types"},
            {"name": "reasoning", "description": "Models with strong reasoning capabilities"},
            {"name": "creative", "description": "Models optimized for creative tasks"},
            {"name": "analysis", "description": "Models for data and content analysis"},
            {"name": "local", "description": "Locally hosted models"},
            {"name": "api", "description": "Cloud-based API models"},
            {"name": "open-source", "description": "Open source models"},
            {"name": "proprietary", "description": "Proprietary commercial models"},
        ]
        
        created_tags = []
        for tag_data in default_tags:
            # Check if tag already exists
            result = await session.execute(
                text("SELECT id FROM tags WHERE name = :name"),
                {"name": tag_data["name"]}
            )
            existing_tag = result.fetchone()
            
            if not existing_tag:
                tag = Tag(**tag_data)
                session.add(tag)
                await session.flush()
                created_tags.append(tag)
                logger.info(f"Created tag: {tag_data['name']}")
            else:
                logger.info(f"Tag already exists: {tag_data['name']}")
        
        return created_tags
    
    async def create_default_models(self, session) -> List[Model]:
        """Create default models for testing."""
        default_models = [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "openai",
                "description": "OpenAI's most capable model with strong reasoning abilities",
                "version": "1.0",
                "context_window": 8192,
                "max_output_tokens": 4096,
                "parameters": {
                    "model_type": "general",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions"
                },
                "capabilities": {
                    "text_generation": True,
                    "chat": True,
                    "reasoning": True,
                    "code_generation": True
                },
                "pricing": {
                    "input_tokens": 0.03,
                    "output_tokens": 0.06,
                    "currency": "USD",
                    "per_tokens": 1000
                },
                "is_active": True
            },
            {
                "id": "claude-3-opus",
                "name": "Claude 3 Opus",
                "provider": "anthropic",
                "description": "Anthropic's most powerful model with exceptional performance",
                "version": "1.0",
                "context_window": 200000,
                "max_output_tokens": 4096,
                "parameters": {
                    "model_type": "general",
                    "api_endpoint": "https://api.anthropic.com/v1/messages"
                },
                "capabilities": {
                    "text_generation": True,
                    "chat": True,
                    "reasoning": True,
                    "analysis": True
                },
                "pricing": {
                    "input_tokens": 0.015,
                    "output_tokens": 0.075,
                    "currency": "USD",
                    "per_tokens": 1000
                },
                "is_active": True
            },
            {
                "id": "llama2:7b",
                "name": "Llama 2 7B",
                "provider": "meta",
                "description": "Meta's open-source Llama 2 model (7B parameters)",
                "version": "2.0",
                "context_window": 4096,
                "max_output_tokens": 2048,
                "size": "3.8 GB",
                "parameters": {
                    "model_type": "general",
                    "requires_ollama": True
                },
                "capabilities": {
                    "text_generation": True,
                    "chat": True
                },
                "pricing": {
                    "input_tokens": 0.0,
                    "output_tokens": 0.0,
                    "currency": "USD",
                    "per_tokens": 1000
                },
                "is_active": True
            },
            {
                "id": "codellama:7b",
                "name": "Code Llama 7B",
                "provider": "meta",
                "description": "Meta's specialized code generation model",
                "version": "1.0",
                "context_window": 4096,
                "max_output_tokens": 2048,
                "size": "3.8 GB",
                "parameters": {
                    "model_type": "code",
                    "requires_ollama": True
                },
                "capabilities": {
                    "text_generation": True,
                    "code_generation": True
                },
                "pricing": {
                    "input_tokens": 0.0,
                    "output_tokens": 0.0,
                    "currency": "USD",
                    "per_tokens": 1000
                },
                "is_active": True
            },
            {
                "id": "mistral:7b-instruct",
                "name": "Mistral 7B Instruct",
                "provider": "mistral",
                "description": "Mistral AI's instruction-tuned model",
                "version": "0.1",
                "context_window": 4096,
                "max_output_tokens": 2048,
                "size": "4.1 GB",
                "parameters": {
                    "model_type": "general",
                    "requires_ollama": True
                },
                "capabilities": {
                    "text_generation": True,
                    "chat": True
                },
                "pricing": {
                    "input_tokens": 0.0,
                    "output_tokens": 0.0,
                    "currency": "USD",
                    "per_tokens": 1000
                },
                "is_active": True
            }
        ]
        
        created_models = []
        for model_data in default_models:
            # Check if model already exists
            result = await session.execute(
                text("SELECT id FROM models WHERE id = :id"),
                {"id": model_data["id"]}
            )
            existing_model = result.fetchone()
            
            if not existing_model:
                model = Model(**model_data)
                session.add(model)
                await session.flush()
                created_models.append(model)
                logger.info(f"Created model: {model_data['name']}")
            else:
                logger.info(f"Model already exists: {model_data['name']}")
        
        return created_models
    
    async def create_test_users(self, session) -> List[User]:
        """Create test users for development."""
        test_users = [
            {
                "username": "testuser1",
                "email": "test1@webplus.local",
                "full_name": "Test User One",
                "role": "user"
            },
            {
                "username": "testuser2", 
                "email": "test2@webplus.local",
                "full_name": "Test User Two",
                "role": "user"
            },
            {
                "username": "developer",
                "email": "dev@webplus.local", 
                "full_name": "Developer User",
                "role": "developer"
            }
        ]
        
        created_users = []
        default_password = "testpass123"
        hashed_password = pwd_context.hash(default_password)
        
        for user_data in test_users:
            # Check if user already exists
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user_data["email"]}
            )
            existing_user = result.fetchone()
            
            if not existing_user:
                user = User(
                    **user_data,
                    hashed_password=hashed_password,
                    is_active=True,
                    is_verified=True,
                    preferences={
                        "theme": "light",
                        "notifications": True
                    }
                )
                session.add(user)
                await session.flush()
                created_users.append(user)
                logger.info(f"Created test user: {user_data['username']}")
            else:
                logger.info(f"Test user already exists: {user_data['username']}")
        
        return created_users
    
    async def create_sample_conversation(self, session, user: User, model: Model) -> Conversation:
        """Create a sample conversation for testing."""
        conversation = Conversation(
            title="Welcome to Web+",
            model_id=model.id,
            system_prompt="You are a helpful assistant for the Web+ platform.",
            meta_data={
                "created_by": "system",
                "sample": True
            }
        )
        
        session.add(conversation)
        await session.flush()
        
        # Add the user to the conversation
        conversation.users.append(user)
        
        # Create sample messages
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for the Web+ platform. Help users understand how to use the system.",
                "user_id": None
            },
            {
                "role": "user", 
                "content": "Hello! How does Web+ work?",
                "user_id": user.id
            },
            {
                "role": "assistant",
                "content": "Welcome to Web+! This platform allows you to interact with various AI models, manage conversations, and upload files for analysis. You can switch between different models, organize your chats, and collaborate with others. Is there anything specific you'd like to know?",
                "user_id": None
            }
        ]
        
        for msg_data in messages:
            message = Message(
                conversation_id=conversation.id,
                **msg_data,
                tokens=len(msg_data["content"].split()) * 2,  # Rough estimate
                cost=0.001 if msg_data["role"] == "assistant" else 0.0
            )
            session.add(message)
        
        logger.info(f"Created sample conversation: {conversation.title}")
        return conversation
    
    async def seed_database(self) -> bool:
        """Add seed data to the database."""
        try:
            logger.info("Adding seed data to database...")
            
            async with get_async_session() as session:
                # Create admin user
                admin_user = await self.create_admin_user(session)
                
                # Create API key for admin
                admin_api_key = await self.create_api_key_for_user(session, admin_user)
                
                # Create default tags
                tags = await self.create_default_tags(session)
                
                # Create default models
                models = await self.create_default_models(session)
                
                # Create test users (only in development)
                if IS_SQLITE:
                    test_users = await self.create_test_users(session)
                    
                    # Create API keys for test users
                    for user in test_users:
                        await self.create_api_key_for_user(session, user)
                    
                    # Create sample conversation if we have models and users
                    if models and test_users:
                        await self.create_sample_conversation(session, test_users[0], models[0])
                
                await session.commit()
            
            logger.info("Successfully added seed data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to seed database: {e}")
            return False
    
    async def get_database_status(self) -> Dict[str, Any]:
        """Get comprehensive database status."""
        status = {
            "database_type": "SQLite" if IS_SQLITE else "PostgreSQL",
            "database_url": ASYNC_DATABASE_URL,
            "database_exists": False,
            "connection_ok": False,
            "tables": {},
            "record_counts": {},
            "last_check": datetime.utcnow().isoformat()
        }
        
        try:
            # Check database existence
            status["database_exists"] = await self.check_database_exists()
            
            # Check connection
            status["connection_ok"] = await test_async_connection()
            
            if status["connection_ok"]:
                # Check tables
                status["tables"] = await self.check_tables_exist()
                
                # Get record counts
                async with async_session_maker() as session:
                    for table_name in ["users", "models", "conversations", "messages"]:
                        if status["tables"].get(table_name, False):
                            try:
                                result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                                count = result.scalar()
                                status["record_counts"][table_name] = count
                            except Exception as e:
                                status["record_counts"][table_name] = f"Error: {str(e)}"
        
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    async def reset_database(self, confirm: bool = False) -> bool:
        """Reset the entire database (dangerous operation)."""
        if not confirm:
            logger.error("Database reset requires explicit confirmation")
            return False
        
        try:
            logger.warning("Resetting database - this will delete ALL data!")
            
            # Create backup first
            backup_file = await self.create_backup()
            
            # Drop all tables
            success = await self.drop_all_tables()
            if not success:
                logger.error("Failed to drop tables")
                if backup_file:
                    await self.rollback_from_backup()
                return False
            
            # Recreate tables
            success = await self.create_tables()
            if not success:
                logger.error("Failed to recreate tables")
                if backup_file:
                    await self.rollback_from_backup()
                return False
            
            # Add seed data
            success = await self.seed_database()
            if not success:
                logger.error("Failed to seed database")
                if backup_file:
                    await self.rollback_from_backup()
                return False
            
            logger.info("Database reset completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            if self.backup_file:
                await self.rollback_from_backup()
            return False


async def main():
    """Main entry point for the database initialization script."""
    parser = argparse.ArgumentParser(description="Web+ Database Initialization and Management")
    parser.add_argument("--init", action="store_true", help="Initialize database with tables and seed data")
    parser.add_argument("--seed", action="store_true", help="Add seed data only")
    parser.add_argument("--reset", action="store_true", help="Reset database (WARNING: deletes all data)")
    parser.add_argument("--check", action="store_true", help="Check database status")
    parser.add_argument("--confirm", action="store_true", help="Confirm dangerous operations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create database manager
    db_manager = DatabaseManager()
    
    try:
        logger.info("=" * 60)
        logger.info("Web+ Database Management")
        logger.info("=" * 60)
        
        if args.check or not any([args.init, args.seed, args.reset]):
            # Show database status
            status = await db_manager.get_database_status()
            logger.info("\nDatabase Status:")
            logger.info(f"  Type: {status['database_type']}")
            logger.info(f"  Exists: {status['database_exists']}")
            logger.info(f"  Connection: {status['connection_ok']}")
            
            if status.get("tables"):
                logger.info("  Tables:")
                for table, exists in status["tables"].items():
                    logger.info(f"    {table}: {'✓' if exists else '✗'}")
            
            if status.get("record_counts"):
                logger.info("  Record Counts:")
                for table, count in status["record_counts"].items():
                    logger.info(f"    {table}: {count}")
        
        if args.reset:
            if not args.confirm:
                logger.error("Database reset requires --confirm flag for safety")
                logger.error("This operation will DELETE ALL DATA!")
                return 1
            
            success = await db_manager.reset_database(confirm=True)
            if not success:
                logger.error("Database reset failed")
                return 1
        
        elif args.init:
            # Full initialization
            logger.info("Initializing database...")
            
            # Create backup if database exists
            await db_manager.create_backup()
            
            # Create tables
            success = await db_manager.create_tables()
            if not success:
                logger.error("Failed to create tables")
                return 1
            
            # Add seed data
            success = await db_manager.seed_database()
            if not success:
                logger.error("Failed to seed database")
                return 1
            
            logger.info("Database initialization completed successfully!")
        
        elif args.seed:
            # Seed data only
            success = await db_manager.seed_database()
            if not success:
                logger.error("Failed to seed database")
                return 1
            
            logger.info("Database seeding completed successfully!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        # Cleanup
        await close_async_db()
        close_sync_db()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)