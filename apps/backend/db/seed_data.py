"""
Production-grade seed data system for Web+ backend.

This module provides comprehensive seed data for development, testing,
and initial production setup.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_async_session
from db.models import User, Model, APIKey, Conversation, Message
from db.pipeline_models import Pipeline, PipelineStep
from auth.password import hash_password
import uuid

logger = logging.getLogger(__name__)


class SeedDataManager:
    """Manages seed data for different environments."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.seed_data_path = Path(__file__).parent / "seed_data"
        self.seed_data_path.mkdir(exist_ok=True)
        
    async def seed_all(self, db: AsyncSession, force: bool = False) -> Dict[str, Any]:
        """Seed all data for the environment."""
        logger.info(f"Starting seed data process for {self.environment}")
        
        results = {
            "environment": self.environment,
            "seeded_at": datetime.now().isoformat(),
            "results": {}
        }
        
        # Check if already seeded (unless force is True)
        if not force and await self._is_already_seeded(db):
            logger.info("Database already seeded, skipping...")
            results["skipped"] = True
            return results
        
        try:
            # Seed in order of dependencies
            results["results"]["users"] = await self._seed_users(db)
            results["results"]["models"] = await self._seed_models(db)
            results["results"]["api_keys"] = await self._seed_api_keys(db)
            results["results"]["pipelines"] = await self._seed_pipelines(db)
            
            # Only seed sample data in development
            if self.environment == "development":
                results["results"]["conversations"] = await self._seed_conversations(db)
                results["results"]["messages"] = await self._seed_messages(db)
            
            await db.commit()
            logger.info("Seed data process completed successfully")
            results["success"] = True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Seed data process failed: {e}")
            results["error"] = str(e)
            results["success"] = False
            
        return results
    
    async def _is_already_seeded(self, db: AsyncSession) -> bool:
        """Check if database is already seeded."""
        # Check if we have users (simple indicator)
        result = await db.execute(select(User).limit(1))
        return result.first() is not None
    
    async def _seed_users(self, db: AsyncSession) -> Dict[str, Any]:
        """Seed users based on environment."""
        logger.info("Seeding users...")
        
        users_data = self._get_users_data()
        created_users = []
        
        for user_data in users_data:
            # Check if user already exists
            result = await db.execute(
                select(User).where(User.username == user_data["username"])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                user = User(
                    id=user_data.get("id", str(uuid.uuid4())),
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=user_data.get("is_active", True),
                    is_verified=user_data.get("is_verified", True),
                    is_superuser=user_data.get("is_superuser", False),
                    role=user_data.get("role", "user"),
                    created_at=datetime.utcnow()
                )
                db.add(user)
                created_users.append({
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                })
                logger.info(f"Created user: {user.username}")
            else:
                logger.info(f"User already exists: {user_data['username']}")
        
        await db.flush()
        return {"created": len(created_users), "users": created_users}
    
    async def _seed_models(self, db: AsyncSession) -> Dict[str, Any]:
        """Seed AI models."""
        logger.info("Seeding models...")
        
        models_data = self._get_models_data()
        created_models = []
        
        for model_data in models_data:
            # Check if model already exists
            result = await db.execute(
                select(Model).where(Model.id == model_data["id"])
            )
            existing_model = result.scalar_one_or_none()
            
            if not existing_model:
                model = Model(
                    id=model_data["id"],
                    name=model_data["name"],
                    provider=model_data["provider"],
                    description=model_data.get("description", ""),
                    version=model_data.get("version", "1.0"),
                    is_active=model_data.get("is_active", True),
                    is_local=model_data.get("is_local", True),
                    status=model_data.get("status", "inactive"),
                    context_window=model_data.get("context_window", 4096),
                    max_output_tokens=model_data.get("max_output_tokens", 2048),
                    input_cost_per_token=model_data.get("input_cost_per_token", 0.00001),
                    output_cost_per_token=model_data.get("output_cost_per_token", 0.00002),
                    metadata=model_data.get("metadata", {}),
                    created_at=datetime.utcnow()
                )
                db.add(model)
                created_models.append({
                    "id": model.id,
                    "name": model.name,
                    "provider": model.provider
                })
                logger.info(f"Created model: {model.id}")
            else:
                logger.info(f"Model already exists: {model_data['id']}")
        
        await db.flush()
        return {"created": len(created_models), "models": created_models}
    
    async def _seed_api_keys(self, db: AsyncSession) -> Dict[str, Any]:
        """Seed API keys for testing."""
        logger.info("Seeding API keys...")
        
        if self.environment == "production":
            logger.info("Skipping API key seeding in production")
            return {"created": 0, "api_keys": []}
        
        api_keys_data = self._get_api_keys_data()
        created_keys = []
        
        # Get admin user for API keys
        result = await db.execute(
            select(User).where(User.role == "admin").limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            logger.warning("No admin user found for API key creation")
            return {"created": 0, "api_keys": []}
        
        for key_data in api_keys_data:
            # Check if API key already exists
            result = await db.execute(
                select(APIKey).where(APIKey.key == key_data["key"])
            )
            existing_key = result.scalar_one_or_none()
            
            if not existing_key:
                api_key = APIKey(
                    id=str(uuid.uuid4()),
                    key=key_data["key"],
                    name=key_data["name"],
                    user_id=admin_user.id,
                    is_active=True,
                    permissions=key_data.get("permissions", ["read", "write"]),
                    expires_at=datetime.utcnow() + timedelta(days=365),
                    created_at=datetime.utcnow()
                )
                db.add(api_key)
                created_keys.append({
                    "name": api_key.name,
                    "key": api_key.key[:8] + "..."  # Truncated for security
                })
                logger.info(f"Created API key: {api_key.name}")
            else:
                logger.info(f"API key already exists: {key_data['name']}")
        
        await db.flush()
        return {"created": len(created_keys), "api_keys": created_keys}
    
    async def _seed_pipelines(self, db: AsyncSession) -> Dict[str, Any]:
        """Seed sample pipelines."""
        logger.info("Seeding pipelines...")
        
        pipelines_data = self._get_pipelines_data()
        created_pipelines = []
        
        # Get admin user for pipeline ownership
        result = await db.execute(
            select(User).where(User.role == "admin").limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            logger.warning("No admin user found for pipeline creation")
            return {"created": 0, "pipelines": []}
        
        for pipeline_data in pipelines_data:
            # Check if pipeline already exists
            result = await db.execute(
                select(Pipeline).where(Pipeline.name == pipeline_data["name"])
            )
            existing_pipeline = result.scalar_one_or_none()
            
            if not existing_pipeline:
                pipeline = Pipeline(
                    id=str(uuid.uuid4()),
                    name=pipeline_data["name"],
                    description=pipeline_data["description"],
                    user_id=admin_user.id,
                    is_active=True,
                    is_public=pipeline_data.get("is_public", True),
                    tags=pipeline_data.get("tags", []),
                    metadata=pipeline_data.get("metadata", {}),
                    created_at=datetime.utcnow()
                )
                db.add(pipeline)
                await db.flush()  # Flush to get pipeline ID
                
                # Add pipeline steps
                for i, step_data in enumerate(pipeline_data.get("steps", [])):
                    step = PipelineStep(
                        id=str(uuid.uuid4()),
                        pipeline_id=pipeline.id,
                        name=step_data["name"],
                        type=step_data["type"],
                        order=i,
                        config=step_data["config"],
                        description=step_data.get("description", ""),
                        is_active=True,
                        input_mapping=step_data.get("input_mapping", {}),
                        output_mapping=step_data.get("output_mapping", {}),
                        created_at=datetime.utcnow()
                    )
                    db.add(step)
                
                created_pipelines.append({
                    "name": pipeline.name,
                    "steps": len(pipeline_data.get("steps", []))
                })
                logger.info(f"Created pipeline: {pipeline.name}")
            else:
                logger.info(f"Pipeline already exists: {pipeline_data['name']}")
        
        await db.flush()
        return {"created": len(created_pipelines), "pipelines": created_pipelines}
    
    async def _seed_conversations(self, db: AsyncSession) -> Dict[str, Any]:
        """Seed sample conversations (development only)."""
        logger.info("Seeding sample conversations...")
        
        if self.environment != "development":
            return {"created": 0, "conversations": []}
        
        # Get a user and model for the conversation
        user_result = await db.execute(select(User).limit(1))
        user = user_result.scalar_one_or_none()
        
        model_result = await db.execute(select(Model).limit(1))
        model = model_result.scalar_one_or_none()
        
        if not user or not model:
            logger.warning("No user or model found for conversation creation")
            return {"created": 0, "conversations": []}
        
        conversations_data = self._get_conversations_data()
        created_conversations = []
        
        for conv_data in conversations_data:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                title=conv_data["title"],
                model_id=model.id,
                user_id=user.id,
                system_prompt=conv_data.get("system_prompt", ""),
                created_at=datetime.utcnow()
            )
            db.add(conversation)
            created_conversations.append({
                "title": conversation.title,
                "model_id": conversation.model_id
            })
            logger.info(f"Created conversation: {conversation.title}")
        
        await db.flush()
        return {"created": len(created_conversations), "conversations": created_conversations}
    
    async def _seed_messages(self, db: AsyncSession) -> Dict[str, Any]:
        """Seed sample messages (development only)."""
        logger.info("Seeding sample messages...")
        
        if self.environment != "development":
            return {"created": 0, "messages": []}
        
        # Get the first conversation
        conv_result = await db.execute(select(Conversation).limit(1))
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            logger.warning("No conversation found for message creation")
            return {"created": 0, "messages": []}
        
        messages_data = self._get_messages_data()
        created_messages = []
        
        for msg_data in messages_data:
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role=msg_data["role"],
                content=msg_data["content"],
                user_id=conversation.user_id if msg_data["role"] == "user" else None,
                tokens=msg_data.get("tokens", 10),
                cost=msg_data.get("cost", 0.001),
                metadata=msg_data.get("metadata", {}),
                created_at=datetime.utcnow()
            )
            db.add(message)
            created_messages.append({
                "role": message.role,
                "content": message.content[:50] + "..." if len(message.content) > 50 else message.content
            })
        
        await db.flush()
        return {"created": len(created_messages), "messages": created_messages}
    
    def _get_users_data(self) -> List[Dict[str, Any]]:
        """Get user seed data for the environment."""
        base_users = [
            {
                "username": "admin",
                "email": "admin@webplus.dev",
                "password": "admin123!",
                "full_name": "System Administrator",
                "role": "admin",
                "is_superuser": True
            }
        ]
        
        if self.environment == "development":
            base_users.extend([
                {
                    "username": "testuser",
                    "email": "test@webplus.dev",
                    "password": "test123!",
                    "full_name": "Test User",
                    "role": "user"
                },
                {
                    "username": "developer",
                    "email": "dev@webplus.dev",
                    "password": "dev123!",
                    "full_name": "Developer User",
                    "role": "developer"
                }
            ])
        
        return base_users
    
    def _get_models_data(self) -> List[Dict[str, Any]]:
        """Get model seed data."""
        return [
            {
                "id": "llama3.2:latest",
                "name": "Llama 3.2",
                "provider": "ollama",
                "description": "Meta's Llama 3.2 model",
                "is_local": True,
                "context_window": 8192,
                "max_output_tokens": 4096
            },
            {
                "id": "codellama:latest",
                "name": "Code Llama",
                "provider": "ollama",
                "description": "Code-specialized Llama model",
                "is_local": True,
                "context_window": 16384,
                "max_output_tokens": 8192
            },
            {
                "id": "mistral:latest",
                "name": "Mistral 7B",
                "provider": "ollama",
                "description": "Mistral's efficient 7B model",
                "is_local": True,
                "context_window": 8192,
                "max_output_tokens": 4096
            }
        ]
    
    def _get_api_keys_data(self) -> List[Dict[str, Any]]:
        """Get API key seed data (development only)."""
        if self.environment == "production":
            return []
        
        return [
            {
                "key": "dev_test_key_12345",
                "name": "Development Test Key",
                "permissions": ["read", "write"]
            },
            {
                "key": "integration_test_key_67890",
                "name": "Integration Test Key",
                "permissions": ["read"]
            }
        ]
    
    def _get_pipelines_data(self) -> List[Dict[str, Any]]:
        """Get pipeline seed data."""
        return [
            {
                "name": "Code Review Pipeline",
                "description": "Automated code review and feedback pipeline",
                "is_public": True,
                "tags": ["code", "review", "automation"],
                "steps": [
                    {
                        "name": "Code Analysis",
                        "type": "prompt",
                        "config": {
                            "model_id": "codellama:latest",
                            "prompt": "Analyze the following code for best practices, bugs, and improvements:\\n\\n{{input}}",
                            "options": {"temperature": 0.1}
                        },
                        "description": "Analyze code quality and suggest improvements"
                    },
                    {
                        "name": "Security Check",
                        "type": "prompt",
                        "config": {
                            "model_id": "llama3.2:latest",
                            "prompt": "Review this code for security vulnerabilities:\\n\\n{{previous_output}}",
                            "options": {"temperature": 0.0}
                        },
                        "description": "Check for security issues"
                    }
                ]
            },
            {
                "name": "Content Generation Pipeline",
                "description": "Generate and refine content with multiple AI steps",
                "is_public": True,
                "tags": ["content", "generation", "writing"],
                "steps": [
                    {
                        "name": "Initial Draft",
                        "type": "prompt",
                        "config": {
                            "model_id": "mistral:latest",
                            "prompt": "Write a comprehensive article about: {{topic}}\\n\\nTarget audience: {{audience}}\\nTone: {{tone}}",
                            "options": {"temperature": 0.7}
                        },
                        "description": "Generate initial content draft"
                    },
                    {
                        "name": "Content Refinement",
                        "type": "prompt",
                        "config": {
                            "model_id": "llama3.2:latest",
                            "prompt": "Improve the following content for clarity, engagement, and structure:\\n\\n{{previous_output}}",
                            "options": {"temperature": 0.3}
                        },
                        "description": "Refine and improve content"
                    }
                ]
            }
        ]
    
    def _get_conversations_data(self) -> List[Dict[str, Any]]:
        """Get conversation seed data (development only)."""
        return [
            {
                "title": "Welcome Conversation",
                "system_prompt": "You are a helpful assistant for Web+ users. Be friendly and informative."
            },
            {
                "title": "Code Help Session",
                "system_prompt": "You are an expert programming assistant. Help users with code questions and debugging."
            }
        ]
    
    def _get_messages_data(self) -> List[Dict[str, Any]]:
        """Get message seed data (development only)."""
        return [
            {
                "role": "user",
                "content": "Hello! Can you help me get started with Web+?",
                "tokens": 12,
                "cost": 0.0001
            },
            {
                "role": "assistant",
                "content": "Hello! Welcome to Web+! I'd be happy to help you get started. Web+ is a platform for managing and interacting with AI models. You can create conversations, build automated pipelines, and manage your AI workflows. What would you like to know more about?",
                "tokens": 45,
                "cost": 0.0005
            }
        ]


async def seed_database(environment: str = "development", force: bool = False) -> Dict[str, Any]:
    """Main function to seed the database."""
    logger.info(f"Starting database seeding for {environment}")
    
    seeder = SeedDataManager(environment)
    
    async with get_async_session() as db:
        try:
            results = await seeder.seed_all(db, force=force)
            logger.info("Database seeding completed")
            return results
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    # Command line usage
    environment = sys.argv[1] if len(sys.argv) > 1 else "development"
    force = "--force" in sys.argv
    
    results = asyncio.run(seed_database(environment, force))
    
    print(json.dumps(results, indent=2))
    
    if results.get("success", False):
        print(f"\\n🏎️ Ferrari seed data installed for {environment}!")
        sys.exit(0)
    else:
        print(f"\\n❌ Seed data failed for {environment}")
        sys.exit(1)