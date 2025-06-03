import asyncio
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Base, async_engine, async_session_maker
from .models import User, APIKey, Model
from .crud import create_user, create_api_key, create_model
import uuid
import secrets
from passlib.context import CryptContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password handling
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def init_db() -> None:
    """Initialize the database with tables and default data."""
    # Create tables
    async with async_engine.begin() as conn:
        logger.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as db:
        await create_default_data(db)

async def create_default_data(db: AsyncSession) -> None:
    """Create default data in the database."""
    # Create default admin user if not exists
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")  # Should be changed in production
    
    # Check if admin user already exists
    from .crud import get_user_by_email
    admin_user = await get_user_by_email(db, admin_email)
    
    if not admin_user:
        logger.info(f"Creating default admin user: {admin_username}")
        hashed_password = pwd_context.hash(admin_password)
        admin_user = await create_user(
            db=db,
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            full_name="Administrator"
        )
        
        # Make the user a superuser
        admin_user.is_superuser = True
        await db.commit()
        
        # Create a default API key for the admin
        api_key_value = secrets.token_urlsafe(32)
        await create_api_key(
            db=db,
            user_id=admin_user.id,
            key=api_key_value,
            name="Default Admin Key"
        )
        
        logger.info(f"Created API key for admin: {api_key_value}")
        
    else:
        logger.info(f"Admin user already exists: {admin_username}")
    
    # Create some default models if they don't exist
    default_models = [
        {
            "id": "llama2:7b",
            "name": "Llama 2 7B",
            "provider": "meta",
            "is_active": True,
            "description": "Meta's Llama 2 7B parameter model for general purpose tasks",
            "size": "3.8 GB",
            "version": "2.0",
            "context_window": 4096,
            "max_output_tokens": 2048,
            "parameters": {"model_type": "general"},
            "capabilities": {"text_generation": True, "chat": True}
        },
        {
            "id": "codellama:7b",
            "name": "Code Llama 7B",
            "provider": "meta",
            "is_active": True,
            "description": "Meta's Code Llama 7B parameter model for code generation and understanding",
            "size": "3.8 GB",
            "version": "1.0",
            "context_window": 4096,
            "max_output_tokens": 2048,
            "parameters": {"model_type": "code"},
            "capabilities": {"text_generation": True, "code_generation": True}
        },
        {
            "id": "mistral:7b-instruct",
            "name": "Mistral 7B Instruct",
            "provider": "mistral",
            "is_active": True,
            "description": "Mistral AI's 7B parameter instruct model",
            "size": "4.1 GB",
            "version": "0.1",
            "context_window": 4096,
            "max_output_tokens": 2048,
            "parameters": {"model_type": "general"},
            "capabilities": {"text_generation": True, "chat": True}
        }
    ]
    
    # Add external API models
    external_models = [
        {
            "id": "gpt-4-turbo",
            "name": "GPT-4 Turbo",
            "provider": "openai",
            "is_active": True,
            "description": "OpenAI's GPT-4 Turbo model with improved capabilities and lower latency",
            "version": "1.0",
            "context_window": 128000,
            "max_output_tokens": 4096,
            "parameters": {"model_type": "general"},
            "capabilities": {"text_generation": True, "chat": True}
        },
        {
            "id": "claude-3-opus",
            "name": "Claude 3 Opus",
            "provider": "anthropic",
            "is_active": True,
            "description": "Anthropic's most powerful Claude model with exceptional performance across tasks",
            "version": "1.0",
            "context_window": 100000,
            "max_output_tokens": 4096,
            "parameters": {"model_type": "general"},
            "capabilities": {"text_generation": True, "chat": True}
        }
    ]
    
    # Combine all models
    all_models = default_models + external_models
    
    # Create models
    for model_data in all_models:
        # Check if model already exists
        from .crud import get_model
        existing_model = await get_model(db, model_data["id"])
        
        if not existing_model:
            logger.info(f"Creating model: {model_data['name']}")
            await create_model(db, model_data)
        else:
            logger.info(f"Model already exists: {model_data['name']}")

if __name__ == "__main__":
    """Run the database initialization script."""
    asyncio.run(init_db())
    logger.info("Database initialization complete!")
