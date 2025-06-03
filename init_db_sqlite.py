"""
Pure SQLite3 initialization script for Web+.
This is a last-resort workaround for SQLAlchemy dialect issues.
"""
import os
import sys
import sqlite3
import logging
import json
import uuid
import secrets
import datetime
import hashlib
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db_sqlite():
    """Initialize the SQLite database directly without SQLAlchemy."""
    # Get the base directory
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "apps" / "backend" / "web_plus.db"
    
    logger.info(f"Initializing database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        hashed_password TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create models table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS models (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        type TEXT,
        provider TEXT,
        size TEXT,
        status TEXT NOT NULL DEFAULT 'inactive',
        version TEXT,
        is_local BOOLEAN NOT NULL DEFAULT TRUE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        context_window INTEGER DEFAULT 4096,
        metadata TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create API keys table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        key TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Check if admin user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    admin_user = cursor.fetchone()
    
    # Create admin user if not exists
    if not admin_user:
        admin_id = str(uuid.uuid4())
        # Simple password hashing (in production this would use a proper hashing library)
        hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
        
        logger.info("Creating default admin user")
        cursor.execute("""
        INSERT INTO users (id, username, email, full_name, hashed_password, is_superuser)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (admin_id, "admin", "admin@example.com", "Administrator", hashed_password, True))
        
        # Create API key for admin
        api_key = secrets.token_urlsafe(32)
        cursor.execute("""
        INSERT INTO api_keys (id, user_id, key, name)
        VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4()), admin_id, api_key, "Default Admin Key"))
        
        logger.info(f"Created API key for admin: {api_key}")
    
    # Add default models if they don't exist
    default_models = [
        {
            "id": "llama2:7b",
            "name": "Llama 2 7B",
            "type": "general",
            "provider": "meta",
            "is_local": True,
            "status": "inactive",
            "description": "Meta's Llama 2 7B parameter model for general purpose tasks",
            "size": "3.8 GB",
            "version": "2.0",
        },
        {
            "id": "codellama:7b",
            "name": "Code Llama 7B",
            "type": "code",
            "provider": "meta",
            "is_local": True,
            "status": "inactive",
            "description": "Meta's Code Llama 7B parameter model for code generation and understanding",
            "size": "3.8 GB",
            "version": "1.0",
        },
        {
            "id": "mistral:7b-instruct",
            "name": "Mistral 7B Instruct",
            "type": "general",
            "provider": "mistral",
            "is_local": True,
            "status": "inactive",
            "description": "Mistral AI's 7B parameter instruct model",
            "size": "4.1 GB",
            "version": "0.1",
        },
        {
            "id": "gpt-4-turbo",
            "name": "GPT-4 Turbo",
            "type": "general",
            "provider": "openai",
            "is_local": False,
            "status": "available",
            "description": "OpenAI's GPT-4 Turbo model with improved capabilities and lower latency",
            "version": "1.0",
        },
        {
            "id": "claude-3-opus",
            "name": "Claude 3 Opus",
            "type": "general",
            "provider": "anthropic",
            "is_local": False,
            "status": "available",
            "description": "Anthropic's most powerful Claude model with exceptional performance across tasks",
            "version": "1.0",
        }
    ]
    
    for model_data in default_models:
        # Check if model exists
        cursor.execute("SELECT id FROM models WHERE id = ?", (model_data["id"],))
        existing_model = cursor.fetchone()
        
        if not existing_model:
            logger.info(f"Creating model: {model_data['name']}")
            
            # Convert metadata to JSON string if present
            metadata = json.dumps(model_data.get("metadata", {}))
            
            cursor.execute("""
            INSERT INTO models (
                id, name, description, type, provider, size, status, version, 
                is_local, is_active, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model_data["id"],
                model_data["name"],
                model_data.get("description", ""),
                model_data.get("type", "general"),
                model_data.get("provider", "unknown"),
                model_data.get("size", ""),
                model_data.get("status", "inactive"),
                model_data.get("version", "1.0"),
                model_data.get("is_local", True),
                True,  # is_active
                metadata
            ))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    logger.info("Database initialization complete!")
    return True

if __name__ == "__main__":
    try:
        init_db_sqlite()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)
