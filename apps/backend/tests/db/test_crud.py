import pytest
import uuid
from datetime import datetime, timedelta
from db.models import User, APIKey, Model, Tag, Conversation, Message, File, MessageFile
from db.crud import (
    create_user, get_user, get_user_by_username, get_user_by_email, update_user, delete_user, get_users,
    create_api_key, get_api_key, get_api_key_by_id, get_user_api_keys, update_api_key, delete_api_key, validate_api_key,
    create_model, get_model, get_models, update_model, delete_model,
    create_conversation, add_user_to_conversation, get_conversation, get_user_conversations,
    add_message, get_conversation_messages, delete_message,
    create_file, get_file, get_file_by_path, get_user_files, get_conversation_files, 
    get_message_files, update_file, delete_file, associate_file_with_message, remove_file_from_message,
    create_tag, get_tag, get_tag_by_name, get_or_create_tag, add_tag_to_model
)


@pytest.mark.unit
@pytest.mark.crud
class TestUserCrud:

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test create_user function."""
        user = await create_user(
            db=db_session,
            username="testuser1",
            email="test1@example.com",
            hashed_password="hashedpassword1",
            full_name="Test User 1"
        )

        assert user.id is not None
        assert user.username == "testuser1"
        assert user.email == "test1@example.com"
        assert user.hashed_password == "hashedpassword1"
        assert user.full_name == "Test User 1"

    @pytest.mark.asyncio
    async def test_get_user(self, db_session, test_user):
        """Test get_user function."""
        retrieved_user = await get_user(db_session, test_user.id)
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.username == test_user.username

        # Test non-existent user
        non_existent = await get_user(db_session, str(uuid.uuid4()))
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, db_session, test_user):
        """Test get_user_by_username function."""
        retrieved_user = await get_user_by_username(db_session, test_user.username)
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.username == test_user.username

        # Test non-existent user
        non_existent = await get_user_by_username(db_session, "nonexistentuser")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session, test_user):
        """Test get_user_by_email function."""
        retrieved_user = await get_user_by_email(db_session, test_user.email)
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.email == test_user.email

        # Test non-existent user
        non_existent = await get_user_by_email(db_session, "nonexistent@example.com")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_update_user(self, db_session, test_user):
        """Test update_user function."""
        updated_data = {
            "full_name": "Updated Name",
            "is_active": False
        }
        updated_user = await update_user(db_session, test_user.id, updated_data)
        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.is_active is False
        assert updated_user.id == test_user.id

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session):
        """Test delete_user function."""
        # Create a user to delete
        user = await create_user(
            db=db_session,
            username="userToDelete",
            email="delete@example.com",
            hashed_password="hashedpassword",
            full_name="User To Delete"
        )

        # Verify user exists
        retrieved_user = await get_user(db_session, user.id)
        assert retrieved_user is not None

        # Delete user
        result = await delete_user(db_session, user.id)
        assert result is True

        # Verify user no longer exists
        deleted_user = await get_user(db_session, user.id)
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_get_users(self, db_session):
        """Test get_users function."""
        # Create multiple test users
        for i in range(3):
            await create_user(
                db=db_session,
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                hashed_password=f"hashedpassword{i}",
                full_name=f"Test User {i}"
            )

        # Get users with pagination
        users = await get_users(db_session, skip=0, limit=2)
        assert len(users) == 2

        # Get next page
        users_page2 = await get_users(db_session, skip=2, limit=2)
        assert len(users_page2) > 0
        assert users[0].id != users_page2[0].id


@pytest.mark.unit
@pytest.mark.crud
class TestApiKeyCrud:

    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session, test_user):
        """Test create_api_key function."""
        api_key = await create_api_key(
            db=db_session,
            user_id=test_user.id,
            key="testapikey123",
            name="Test API Key"
        )

        assert api_key.id is not None
        assert api_key.key == "testapikey123"
        assert api_key.name == "Test API Key"
        assert api_key.user_id == test_user.id
        assert api_key.is_active is True
        assert api_key.expires_at is None

    @pytest.mark.asyncio
    async def test_get_api_key(self, db_session, test_api_key):
        """Test get_api_key function."""
        retrieved_key = await get_api_key(db_session, test_api_key.key)
        assert retrieved_key is not None
        assert retrieved_key.id == test_api_key.id
        assert retrieved_key.key == test_api_key.key

        # Test non-existent key
        non_existent = await get_api_key(db_session, "nonexistentkey")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_api_key_by_id(self, db_session, test_api_key):
        """Test get_api_key_by_id function."""
        retrieved_key = await get_api_key_by_id(db_session, test_api_key.id)
        assert retrieved_key is not None
        assert retrieved_key.id == test_api_key.id
        assert retrieved_key.key == test_api_key.key

        # Test non-existent key
        non_existent = await get_api_key_by_id(db_session, str(uuid.uuid4()))
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_user_api_keys(self, db_session, test_user):
        """Test get_user_api_keys function."""
        # Create multiple API keys for the user
        for i in range(3):
            await create_api_key(
                db=db_session,
                user_id=test_user.id,
                key=f"testapikey{i}",
                name=f"Test API Key {i}"
            )

        # Get keys
        keys = await get_user_api_keys(db_session, test_user.id)
        assert len(keys) >= 3

    @pytest.mark.asyncio
    async def test_update_api_key(self, db_session, test_api_key):
        """Test update_api_key function."""
        updated_data = {
            "name": "Updated Key Name",
            "is_active": False
        }
        updated_key = await update_api_key(db_session, test_api_key.id, updated_data)
        assert updated_key is not None
        assert updated_key.name == "Updated Key Name"
        assert updated_key.is_active is False
        assert updated_key.id == test_api_key.id

    @pytest.mark.asyncio
    async def test_delete_api_key(self, db_session, test_user):
        """Test delete_api_key function."""
        # Create an API key to delete
        api_key = await create_api_key(
            db=db_session,
            user_id=test_user.id,
            key="keyToDelete",
            name="Key To Delete"
        )

        # Verify key exists
        retrieved_key = await get_api_key_by_id(db_session, api_key.id)
        assert retrieved_key is not None

        # Delete key
        result = await delete_api_key(db_session, api_key.id)
        assert result is True

        # Verify key no longer exists
        deleted_key = await get_api_key_by_id(db_session, api_key.id)
        assert deleted_key is None

    @pytest.mark.asyncio
    async def test_validate_api_key(self, db_session, test_user):
        """Test validate_api_key function."""
        # Create a valid API key
        valid_key = await create_api_key(
            db=db_session,
            user_id=test_user.id,
            key="validkey123",
            name="Valid API Key"
        )

        # Create an expired API key
        expired_key = await create_api_key(
            db=db_session,
            user_id=test_user.id,
            key="expiredkey123",
            name="Expired API Key",
            expires_at=datetime.now() - timedelta(days=1)
        )

        # Create an inactive API key
        inactive_key_obj = await create_api_key(
            db=db_session,
            user_id=test_user.id,
            key="inactivekey123",
            name="Inactive API Key"
        )
        inactive_key_obj.is_active = False
        await db_session.commit()

        # Test validation
        valid_result = await validate_api_key(db_session, "validkey123")
        assert valid_result is not None
        assert valid_result.id == valid_key.id
        assert valid_result.last_used_at is not None

        expired_result = await validate_api_key(db_session, "expiredkey123")
        assert expired_result is None

        inactive_result = await validate_api_key(db_session, "inactivekey123")
        assert inactive_result is None

        nonexistent_result = await validate_api_key(db_session, "nonexistentkey")
        assert nonexistent_result is None


@pytest.mark.unit
@pytest.mark.crud
class TestModelCrud:

    @pytest.mark.asyncio
    async def test_create_model(self, db_session):
        """Test create_model function."""
        model_data = {
            "id": "test-model-crud",
            "name": "Test Model CRUD",
            "provider": "test",
            "description": "Model for CRUD testing",
            "version": "1.0",
            "is_active": True,
            "context_window": 4096
        }
        model = await create_model(db_session, model_data)

        assert model.id == "test-model-crud"
        assert model.name == "Test Model CRUD"
        assert model.provider == "test"
        assert model.description == "Model for CRUD testing"
        assert model.version == "1.0"
        assert model.is_active is True
        assert model.context_window == 4096

    @pytest.mark.asyncio
    async def test_get_model(self, db_session, test_model):
        """Test get_model function."""
        retrieved_model = await get_model(db_session, test_model.id)
        assert retrieved_model is not None
        assert retrieved_model.id == test_model.id
        assert retrieved_model.name == test_model.name

        # Test non-existent model
        non_existent = await get_model(db_session, "nonexistentmodel")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_models(self, db_session):
        """Test get_models function."""
        # Create multiple test models
        model_providers = ["openai", "anthropic", "meta"]
        for i, provider in enumerate(model_providers):
            await create_model(
                db_session, 
                {
                    "id": f"{provider}-model-{i}",
                    "name": f"{provider.capitalize()} Model {i}",
                    "provider": provider,
                    "is_active": True,
                    "context_window": 4096
                }
            )

        # Get all models
        all_models = await get_models(db_session)
        assert len(all_models) >= 3

        # Filter models by provider
        openai_models = await get_models(db_session, {"provider": "openai"})
        assert len(openai_models) >= 1
        for model in openai_models:
            assert model.provider == "openai"

        # Filter models by is_active
        active_models = await get_models(db_session, {"is_active": True})
        assert len(active_models) >= 3

        # Filter models by search term
        search_models = await get_models(db_session, {"search": "Model"})
        assert len(search_models) >= 3

    @pytest.mark.asyncio
    async def test_update_model(self, db_session, test_model):
        """Test update_model function."""
        updated_data = {
            "name": "Updated Model Name",
            "description": "Updated model description",
            "is_active": False
        }
        updated_model = await update_model(db_session, test_model.id, updated_data)
        assert updated_model is not None
        assert updated_model.name == "Updated Model Name"
        assert updated_model.description == "Updated model description"
        assert updated_model.is_active is False
        assert updated_model.id == test_model.id

    @pytest.mark.asyncio
    async def test_delete_model(self, db_session):
        """Test delete_model function."""
        # Create a model to delete
        model_data = {
            "id": "model-to-delete",
            "name": "Model To Delete",
            "provider": "test",
            "context_window": 4096
        }
        model = await create_model(db_session, model_data)

        # Verify model exists
        retrieved_model = await get_model(db_session, model.id)
        assert retrieved_model is not None

        # Delete model
        result = await delete_model(db_session, model.id)
        assert result is True

        # Verify model no longer exists
        deleted_model = await get_model(db_session, model.id)
        assert deleted_model is None


@pytest.mark.unit
@pytest.mark.crud
class TestConversationCrud:

    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session, test_model):
        """Test create_conversation function."""
        conversation = await create_conversation(
            db=db_session,
            model_id=test_model.id,
            title="Test Conversation",
            system_prompt="This is a test system prompt."
        )

        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.model_id == test_model.id
        assert conversation.system_prompt == "This is a test system prompt."

    @pytest.mark.asyncio
    async def test_add_user_to_conversation(self, db_session, test_user, test_conversation):
        """Test add_user_to_conversation function."""
        # Ensure user is not already in conversation
        test_conversation.users = []
        await db_session.commit()

        # Add user to conversation
        result = await add_user_to_conversation(db_session, test_conversation.id, test_user.id)
        assert result is True

        # Verify user was added
        retrieved_conv = await get_conversation(db_session, test_conversation.id)
        assert retrieved_conv is not None
        assert len(retrieved_conv.users) == 1
        assert retrieved_conv.users[0].id == test_user.id

        # Test idempotence - adding same user again should still return True
        result = await add_user_to_conversation(db_session, test_conversation.id, test_user.id)
        assert result is True

        # Test non-existent conversation
        result = await add_user_to_conversation(db_session, str(uuid.uuid4()), test_user.id)
        assert result is False

        # Test non-existent user
        result = await add_user_to_conversation(db_session, test_conversation.id, str(uuid.uuid4()))
        assert result is False

    @pytest.mark.asyncio
    async def test_get_conversation(self, db_session, test_conversation):
        """Test get_conversation function."""
        retrieved_conv = await get_conversation(db_session, test_conversation.id)
        assert retrieved_conv is not None
        assert retrieved_conv.id == test_conversation.id
        assert retrieved_conv.title == test_conversation.title

        # Test non-existent conversation
        non_existent = await get_conversation(db_session, str(uuid.uuid4()))
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, db_session, test_user, test_model):
        """Test get_user_conversations function."""
        # Create multiple conversations for user
        for i in range(3):
            conversation = await create_conversation(
                db=db_session,
                model_id=test_model.id,
                title=f"User Conversation {i}"
            )
            await add_user_to_conversation(db_session, conversation.id, test_user.id)

        # Get all user conversations
        user_convs = await get_user_conversations(db_session, test_user.id)
        assert len(user_convs) >= 3

        # Get user conversations filtered by model
        model_convs = await get_user_conversations(db_session, test_user.id, test_model.id)
        assert len(model_convs) >= 3
        for conv in model_convs:
            assert conv.model_id == test_model.id

    @pytest.mark.asyncio
    async def test_add_message(self, db_session, test_conversation, test_user):
        """Test add_message function."""
        message = await add_message(
            db=db_session,
            conversation_id=test_conversation.id,
            role="user",
            content="Hello, this is a test message.",
            user_id=test_user.id,
            tokens=10,
            cost=0.00001
        )

        assert message.id is not None
        assert message.conversation_id == test_conversation.id
        assert message.role == "user"
        assert message.content == "Hello, this is a test message."
        assert message.user_id == test_user.id
        assert message.tokens == 10
        assert message.cost == 0.00001

        # Verify conversation updated_at timestamp was updated
        retrieved_conv = await get_conversation(db_session, test_conversation.id)
        assert retrieved_conv.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, db_session, test_conversation, test_user):
        """Test get_conversation_messages function."""
        # Create multiple messages
        for i in range(3):
            await add_message(
                db=db_session,
                conversation_id=test_conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                user_id=test_user.id if i % 2 == 0 else None
            )

        # Get messages
        messages = await get_conversation_messages(db_session, test_conversation.id)
        assert len(messages) >= 3

        # Verify order (oldest first)
        for i in range(1, len(messages)):
            assert messages[i-1].created_at <= messages[i].created_at

    @pytest.mark.asyncio
    async def test_delete_message(self, db_session, test_message):
        """Test delete_message function."""
        # Verify message exists
        assert test_message.id is not None

        # Delete message
        result = await delete_message(db_session, test_message.id)
        assert result is True

        # Verify message no longer exists in database
        # This requires directly querying the database since delete_message uses db.get
        result = await db_session.execute(f"SELECT id FROM messages WHERE id = '{test_message.id}'")
        row = result.first()
        assert row is None


@pytest.mark.unit
@pytest.mark.crud
class TestFileCrud:

    @pytest.mark.asyncio
    async def test_create_file(self, db_session, test_user, test_conversation):
        """Test create_file function."""
        file = await create_file(
            db=db_session,
            filename="test.txt",
            original_filename="original_test.txt",
            content_type="text/plain",
            size=100,
            path="/tmp/test.txt",
            user_id=test_user.id,
            conversation_id=test_conversation.id,
            metadata={"key": "value"},
            is_public=True
        )

        assert file.id is not None
        assert file.filename == "test.txt"
        assert file.original_filename == "original_test.txt"
        assert file.content_type == "text/plain"
        assert file.size == 100
        assert file.path == "/tmp/test.txt"
        assert file.user_id == test_user.id
        assert file.conversation_id == test_conversation.id
        assert file.metadata == {"key": "value"}
        assert file.is_public is True
        assert file.created_at is not None

    @pytest.mark.asyncio
    async def test_get_file(self, db_session, test_file):
        """Test get_file function."""
        retrieved_file = await get_file(db_session, test_file.id)
        assert retrieved_file is not None
        assert retrieved_file.id == test_file.id
        assert retrieved_file.filename == test_file.filename

        # Test non-existent file
        non_existent = await get_file(db_session, str(uuid.uuid4()))
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_file_by_path(self, db_session, test_file):
        """Test get_file_by_path function."""
        retrieved_file = await get_file_by_path(db_session, test_file.path)
        assert retrieved_file is not None
        assert retrieved_file.id == test_file.id
        assert retrieved_file.path == test_file.path

        # Test non-existent path
        non_existent = await get_file_by_path(db_session, "/nonexistent/path.txt")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_user_files(self, db_session, test_user):
        """Test get_user_files function."""
        # Create multiple files for user
        for i in range(3):
            await create_file(
                db=db_session,
                filename=f"user_file_{i}.txt",
                original_filename=f"original_{i}.txt",
                content_type="text/plain",
                size=100,
                path=f"/tmp/user_file_{i}.txt",
                user_id=test_user.id
            )

        # Get user files
        files = await get_user_files(db_session, test_user.id)
        assert len(files) >= 3

    @pytest.mark.asyncio
    async def test_get_conversation_files(self, db_session, test_conversation, test_user):
        """Test get_conversation_files function."""
        # Create multiple files for conversation
        for i in range(3):
            await create_file(
                db=db_session,
                filename=f"conv_file_{i}.txt",
                original_filename=f"original_{i}.txt",
                content_type="text/plain",
                size=100,
                path=f"/tmp/conv_file_{i}.txt",
                user_id=test_user.id,
                conversation_id=test_conversation.id
            )

        # Get conversation files
        files = await get_conversation_files(db_session, test_conversation.id)
        assert len(files) >= 3

    @pytest.mark.asyncio
    async def test_associate_and_get_message_files(self, db_session, test_message, test_file):
        """Test associate_file_with_message and get_message_files functions."""
        # Associate file with message
        result = await associate_file_with_message(db_session, test_file.id, test_message.id)
        assert result is True

        # Get message files
        files = await get_message_files(db_session, test_message.id)
        assert len(files) == 1
        assert files[0].id == test_file.id

    @pytest.mark.asyncio
    async def test_update_file(self, db_session, test_file):
        """Test update_file function."""
        updated_data = {
            "metadata": {"updated": True},
            "is_public": True,
            "analyzed": True,
            "analysis_result": {"summary": "This is a test file."}
        }
        updated_file = await update_file(db_session, test_file.id, updated_data)
        assert updated_file is not None
        assert updated_file.metadata == {"updated": True}
        assert updated_file.is_public is True
        assert updated_file.analyzed is True
        assert updated_file.analysis_result == {"summary": "This is a test file."}
        assert updated_file.id == test_file.id

    @pytest.mark.asyncio
    async def test_remove_file_from_message(self, db_session, test_message, test_file):
        """Test remove_file_from_message function."""
        # First associate file with message
        await associate_file_with_message(db_session, test_file.id, test_message.id)

        # Verify association exists
        files = await get_message_files(db_session, test_message.id)
        assert len(files) == 1

        # Remove association
        result = await remove_file_from_message(db_session, test_file.id, test_message.id)
        assert result is True

        # Verify association is gone
        files = await get_message_files(db_session, test_message.id)
        assert len(files) == 0

    @pytest.mark.asyncio
    async def test_delete_file(self, monkeypatch, db_session, test_user):
        """Test delete_file function."""
        # Create a file to delete
        file = await create_file(
            db=db_session,
            filename="file_to_delete.txt",
            original_filename="original.txt",
            content_type="text/plain",
            size=100,
            path="/tmp/file_to_delete.txt",
            user_id=test_user.id
        )

        # Mock os.path.exists and os.remove to avoid file system interactions
        monkeypatch.setattr('os.path.exists', lambda path: True)
        monkeypatch.setattr('os.remove', lambda path: None)

        # Verify file exists in database
        retrieved_file = await get_file(db_session, file.id)
        assert retrieved_file is not None

        # Delete file without file system interaction
        result = await delete_file(db_session, file.id, delete_from_storage=False)
        assert result is True

        # Verify file no longer exists in database
        deleted_file = await get_file(db_session, file.id)
        assert deleted_file is None


@pytest.mark.unit
@pytest.mark.crud
class TestTagCrud:

    @pytest.mark.asyncio
    async def test_create_tag(self, db_session):
        """Test create_tag function."""
        tag = await create_tag(
            db=db_session,
            name="test-tag",
            description="Test tag description"
        )

        assert tag.id is not None
        assert tag.name == "test-tag"
        assert tag.description == "Test tag description"

    @pytest.mark.asyncio
    async def test_get_tag(self, db_session):
        """Test get_tag function."""
        # Create a tag first
        tag = await create_tag(db_session, "get-test-tag")

        # Get tag by ID
        retrieved_tag = await get_tag(db_session, tag.id)
        assert retrieved_tag is not None
        assert retrieved_tag.id == tag.id
        assert retrieved_tag.name == "get-test-tag"

        # Test non-existent tag
        non_existent = await get_tag(db_session, 9999)
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_tag_by_name(self, db_session):
        """Test get_tag_by_name function."""
        # Create a tag first
        tag = await create_tag(db_session, "name-test-tag")

        # Get tag by name
        retrieved_tag = await get_tag_by_name(db_session, "name-test-tag")
        assert retrieved_tag is not None
        assert retrieved_tag.id == tag.id
        assert retrieved_tag.name == "name-test-tag"

        # Test non-existent tag
        non_existent = await get_tag_by_name(db_session, "non-existent-tag")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_or_create_tag(self, db_session):
        """Test get_or_create_tag function."""
        # Get or create a new tag
        tag1 = await get_or_create_tag(db_session, "new-tag")
        assert tag1 is not None
        assert tag1.name == "new-tag"

        # Get or create an existing tag
        tag2 = await get_or_create_tag(db_session, "new-tag")
        assert tag2 is not None
        assert tag2.id == tag1.id
        assert tag2.name == "new-tag"

    @pytest.mark.asyncio
    async def test_add_tag_to_model(self, db_session, test_model):
        """Test add_tag_to_model function."""
        # Add a tag to model
        result = await add_tag_to_model(db_session, test_model.id, "model-tag")
        assert result is True

        # Verify tag was added
        retrieved_model = await get_model(db_session, test_model.id)
        assert len(retrieved_model.tags) == 1
        assert retrieved_model.tags[0].name == "model-tag"

        # Test idempotence - adding same tag again should still return True
        result = await add_tag_to_model(db_session, test_model.id, "model-tag")
        assert result is True

        # Test non-existent model
        result = await add_tag_to_model(db_session, "non-existent-model", "model-tag")
        assert result is False