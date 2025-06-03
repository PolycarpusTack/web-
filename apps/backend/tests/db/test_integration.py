import pytest
import asyncio
from sqlalchemy import text
from db.database import Base, engine
from db.init_db import init_db
from db.models import User, APIKey, Model, Tag, Conversation, Message, File, MessageThread
from db.crud import create_user, create_model, get_user_by_email, get_model
from auth.password import get_password_hash


@pytest.mark.integration
class TestDatabaseIntegration:

    @pytest.mark.asyncio
    async def test_database_initialization(self, db_session):
        """Test that database initialization creates tables correctly."""
        # Check that tables were created
        result = await db_session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))
        tables = [row[0] for row in result.all()]
        
        # Check for important tables
        assert "users" in tables
        assert "api_keys" in tables
        assert "models" in tables
        assert "conversations" in tables
        assert "messages" in tables
        assert "files" in tables
        assert "message_threads" in tables
        
        # Check for junction tables
        assert "message_files" in tables
        assert "model_tag_association" in tables
        assert "user_conversation_association" in tables

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_session):
        """Test that foreign key constraints are working."""
        # Create a user
        user = await create_user(
            db=db_session,
            username="fkuser",
            email="fk@example.com",
            hashed_password="hashedpassword"
        )
        
        # Create a model
        model = await create_model(
            db=db_session,
            model_data={
                "id": "fk-model",
                "name": "FK Test Model",
                "provider": "test",
                "context_window": 4096
            }
        )
        
        # Create a conversation with valid foreign keys
        conversation = Conversation(
            title="FK Test Conversation",
            model_id=model.id
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        
        # Add user to conversation
        conversation.users.append(user)
        await db_session.commit()
        
        # Create a message with valid foreign keys
        message = Message(
            conversation_id=conversation.id,
            user_id=user.id,
            role="user",
            content="FK test message"
        )
        db_session.add(message)
        await db_session.commit()
        
        # Try to create a message with invalid conversation_id
        invalid_message = Message(
            conversation_id="invalid-conversation-id",
            user_id=user.id,
            role="user",
            content="Invalid FK test message"
        )
        db_session.add(invalid_message)
        
        # Should raise an exception
        with pytest.raises(Exception):
            await db_session.commit()
        
        # Rollback for next test
        await db_session.rollback()
        
        # Try to create a message with invalid user_id
        invalid_message = Message(
            conversation_id=conversation.id,
            user_id="invalid-user-id",
            role="user",
            content="Invalid FK test message"
        )
        db_session.add(invalid_message)
        
        # Should raise an exception
        with pytest.raises(Exception):
            await db_session.commit()
            
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session):
        """Test that cascade delete is working properly."""
        # Create a user
        user = await create_user(
            db=db_session,
            username="cascadeuser",
            email="cascade@example.com",
            hashed_password="hashedpassword"
        )
        
        # Create an API key for the user
        api_key = APIKey(
            user_id=user.id,
            key="cascadeapikey",
            name="Cascade Test Key"
        )
        db_session.add(api_key)
        await db_session.commit()
        
        # Get the API key ID
        api_key_id = api_key.id
        
        # Now delete the user
        await db_session.delete(user)
        await db_session.commit()
        
        # The API key should be deleted as well (cascade)
        result = await db_session.execute(text(
            f"SELECT id FROM api_keys WHERE id = '{api_key_id}'"
        ))
        row = result.first()
        assert row is None

    @pytest.mark.asyncio
    async def test_unique_constraints(self, db_session):
        """Test that unique constraints are working."""
        # Create a user
        await create_user(
            db=db_session,
            username="uniqueuser",
            email="unique@example.com",
            hashed_password="hashedpassword"
        )
        
        # Try to create another user with the same username
        with pytest.raises(Exception):
            await create_user(
                db=db_session,
                username="uniqueuser",  # Same username
                email="different@example.com",
                hashed_password="hashedpassword"
            )
            
        await db_session.rollback()
        
        # Try to create another user with the same email
        with pytest.raises(Exception):
            await create_user(
                db=db_session,
                username="differentuser",
                email="unique@example.com",  # Same email
                hashed_password="hashedpassword"
            )
            
        await db_session.rollback()
        
        # Try with Model ID which should be unique
        await create_model(
            db=db_session,
            model_data={
                "id": "unique-model-id",
                "name": "Unique Test Model",
                "provider": "test",
                "context_window": 4096
            }
        )
        
        # Try to create another model with the same ID
        with pytest.raises(Exception):
            await create_model(
                db=db_session,
                model_data={
                    "id": "unique-model-id",  # Same ID
                    "name": "Different Model Name",
                    "provider": "different",
                    "context_window": 8192
                }
            )
            
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_db_init_idempotence(self, db_session):
        """Test that init_db function is idempotent."""
        # Create a known user
        email = "admin@example.com"
        username = "admin"
        
        # First check if user already exists
        existing_user = await get_user_by_email(db_session, email)
        if existing_user:
            # Delete user to ensure clean test
            await db_session.delete(existing_user)
            await db_session.commit()
        
        # Run init_db once
        await init_db()
        
        # Check that admin user was created
        user1 = await get_user_by_email(db_session, email)
        assert user1 is not None
        assert user1.username == username
        
        user1_id = user1.id
        
        # Run init_db again
        await init_db()
        
        # Check that admin user is still there and wasn't duplicated
        user2 = await get_user_by_email(db_session, email)
        assert user2 is not None
        assert user2.id == user1_id
        assert user2.username == username
        
        # Check that default models were created
        model = await get_model(db_session, "llama2:7b")
        assert model is not None
        assert model.name == "Llama 2 7B"
        assert model.provider == "meta"

    @pytest.mark.asyncio
    async def test_relationship_operations(self, db_session, test_user, test_model):
        """Test that relationship operations work correctly."""
        # Create conversation
        conversation = Conversation(
            title="Relationship Test Conv",
            model_id=test_model.id
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        
        # Add user to conversation
        conversation.users.append(test_user)
        await db_session.commit()
        await db_session.refresh(conversation)
        await db_session.refresh(test_user)
        
        # Check user-conversation relationship
        assert test_user in conversation.users
        assert conversation in test_user.conversations
        
        # Create thread
        thread = MessageThread(
            conversation_id=conversation.id,
            title="Test Thread",
            creator_id=test_user.id
        )
        db_session.add(thread)
        await db_session.commit()
        await db_session.refresh(thread)
        await db_session.refresh(conversation)
        
        # Check conversation-thread relationship
        assert thread in conversation.threads
        assert thread.conversation_id == conversation.id
        
        # Create messages
        user_message = Message(
            conversation_id=conversation.id,
            user_id=test_user.id,
            role="user",
            content="User message",
            thread_id=thread.id
        )
        db_session.add(user_message)
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Assistant message",
            thread_id=thread.id
        )
        db_session.add(assistant_message)
        
        await db_session.commit()
        await db_session.refresh(thread)
        
        # Check thread-message relationship
        assert len(thread.messages) == 2
        
        # Check message-user relationship
        assert user_message.user_id == test_user.id
        assert user_message.user.id == test_user.id
        
        # Create a file
        file = File(
            filename="relationship_test.txt",
            original_filename="original.txt",
            content_type="text/plain",
            size=100,
            path="/tmp/relationship_test.txt",
            user_id=test_user.id,
            conversation_id=conversation.id
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)
        
        # Associate file with message
        message_file = MessageFile(
            message_id=user_message.id,
            file_id=file.id
        )
        db_session.add(message_file)
        await db_session.commit()
        await db_session.refresh(user_message)
        await db_session.refresh(file)
        
        # Check message-file relationship
        assert len(user_message.files) == 1
        assert file in [mf.file for mf in user_message.files]
        
        # Create a tag
        tag = Tag(name="relationship-test-tag")
        db_session.add(tag)
        await db_session.commit()
        
        # Associate tag with model
        test_model.tags.append(tag)
        await db_session.commit()
        await db_session.refresh(test_model)
        await db_session.refresh(tag)
        
        # Check model-tag relationship
        assert tag in test_model.tags
        assert test_model in tag.models