import pytest
import uuid
from datetime import datetime, timedelta
from db.models import (
    User, APIKey, Model, Tag, Conversation, Message, 
    File, MessageFile, MessageThread, generate_uuid
)


@pytest.mark.unit
@pytest.mark.models
class TestModels:

    def test_generate_uuid(self):
        """Test that generate_uuid returns a valid UUID string."""
        uuid_str = generate_uuid()
        assert isinstance(uuid_str, str)
        # Verify it's a valid UUID
        uuid_obj = uuid.UUID(uuid_str)
        assert str(uuid_obj) == uuid_str

    @pytest.mark.asyncio
    async def test_user_model(self, db_session):
        """Test User model creation and attributes."""
        # Create a user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashedpassword",
            full_name="Test User",
            role="user"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Check attributes
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashedpassword"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.role == "user"
        assert user.created_at is not None
        assert user.preferences is None

    @pytest.mark.asyncio
    async def test_api_key_model(self, db_session, test_user):
        """Test APIKey model creation and attributes."""
        # Create API key
        expires_at = datetime.now() + timedelta(days=30)
        api_key = APIKey(
            key="testapikey123",
            name="Test API Key",
            user_id=test_user.id,
            expires_at=expires_at,
            is_active=True
        )
        db_session.add(api_key)
        await db_session.commit()
        await db_session.refresh(api_key)

        # Check attributes
        assert api_key.id is not None
        assert api_key.key == "testapikey123"
        assert api_key.name == "Test API Key"
        assert api_key.user_id == test_user.id
        assert api_key.created_at is not None
        assert api_key.is_active is True
        assert (api_key.expires_at - expires_at).total_seconds() < 1  # Allow slight difference

        # Check relationship
        assert api_key.user.id == test_user.id

    @pytest.mark.asyncio
    async def test_model_model(self, db_session):
        """Test Model model creation and attributes."""
        # Create a model
        model = Model(
            id="test-model-1",
            name="Test Model",
            provider="test",
            description="A test model",
            version="1.0",
            is_active=True,
            context_window=4096
        )
        db_session.add(model)
        await db_session.commit()
        await db_session.refresh(model)

        # Check attributes
        assert model.id == "test-model-1"
        assert model.name == "Test Model"
        assert model.provider == "test"
        assert model.description == "A test model"
        assert model.version == "1.0"
        assert model.is_active is True
        assert model.created_at is not None
        assert model.context_window == 4096

    @pytest.mark.asyncio
    async def test_conversation_model(self, db_session, test_model):
        """Test Conversation model creation and attributes."""
        # Create a conversation
        conversation = Conversation(
            title="Test Conversation",
            model_id=test_model.id,
            system_prompt="This is a test conversation."
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        # Check attributes
        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.model_id == test_model.id
        assert conversation.system_prompt == "This is a test conversation."
        assert conversation.created_at is not None
        assert conversation.metadata is None

        # Check relationship
        assert conversation.model.id == test_model.id

    @pytest.mark.asyncio
    async def test_message_model(self, db_session, test_conversation, test_user):
        """Test Message model creation and attributes."""
        # Create a message
        message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            role="user",
            content="Test message content",
            tokens=10,
            cost=0.00001
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        # Check attributes
        assert message.id is not None
        assert message.conversation_id == test_conversation.id
        assert message.user_id == test_user.id
        assert message.role == "user"
        assert message.content == "Test message content"
        assert message.created_at is not None
        assert message.tokens == 10
        assert message.cost == 0.00001
        assert message.metadata is None

        # Check relationships
        assert message.conversation.id == test_conversation.id
        assert message.user.id == test_user.id

    @pytest.mark.asyncio
    async def test_file_model(self, db_session, test_user):
        """Test File model creation and attributes."""
        # Create a file
        file = File(
            filename="test.txt",
            original_filename="original_test.txt",
            content_type="text/plain",
            size=100,
            path="/tmp/test.txt",
            user_id=test_user.id,
            is_public=False,
            analyzed=False
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        # Check attributes
        assert file.id is not None
        assert file.filename == "test.txt"
        assert file.original_filename == "original_test.txt"
        assert file.content_type == "text/plain"
        assert file.size == 100
        assert file.path == "/tmp/test.txt"
        assert file.user_id == test_user.id
        assert file.created_at is not None
        assert file.is_public is False
        assert file.analyzed is False
        assert file.analysis_result is None
        assert file.extracted_text is None

        # Check relationship
        assert file.user.id == test_user.id

    @pytest.mark.asyncio
    async def test_message_file_association(self, db_session, test_message, test_file):
        """Test MessageFile junction table."""
        # Create association
        message_file = MessageFile(
            message_id=test_message.id,
            file_id=test_file.id
        )
        db_session.add(message_file)
        await db_session.commit()

        # Query the association
        result = await db_session.execute(
            "SELECT message_id, file_id FROM message_files WHERE message_id = :message_id AND file_id = :file_id",
            {"message_id": test_message.id, "file_id": test_file.id}
        )
        row = result.first()

        # Check association
        assert row is not None
        assert row[0] == test_message.id
        assert row[1] == test_file.id

    @pytest.mark.asyncio
    async def test_message_thread_model(self, db_session, test_conversation, test_user):
        """Test MessageThread model creation and attributes."""
        # Create a thread
        thread = MessageThread(
            conversation_id=test_conversation.id,
            title="Test Thread",
            creator_id=test_user.id
        )
        db_session.add(thread)
        await db_session.commit()
        await db_session.refresh(thread)

        # Check attributes
        assert thread.id is not None
        assert thread.conversation_id == test_conversation.id
        assert thread.title == "Test Thread"
        assert thread.creator_id == test_user.id
        assert thread.created_at is not None
        assert thread.parent_thread_id is None
        assert thread.metadata is None

        # Check relationships
        assert thread.conversation.id == test_conversation.id
        assert thread.creator.id == test_user.id

    @pytest.mark.asyncio
    async def test_tag_model(self, db_session):
        """Test Tag model creation and attributes."""
        # Create a tag
        tag = Tag(
            name="test-tag",
            description="Test tag description"
        )
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        # Check attributes
        assert tag.id is not None
        assert tag.name == "test-tag"
        assert tag.description == "Test tag description"

    @pytest.mark.asyncio
    async def test_model_tag_association(self, db_session):
        """Test model-tag many-to-many relationship."""
        # Create a model and a tag
        model = Model(
            id="test-model-2",
            name="Test Model 2",
            provider="test",
            context_window=4096
        )
        db_session.add(model)

        tag = Tag(
            name="test-tag-2",
            description="Test tag description"
        )
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(model)
        await db_session.refresh(tag)

        # Associate the tag with the model
        model.tags.append(tag)
        await db_session.commit()
        await db_session.refresh(model)

        # Check association
        assert len(model.tags) == 1
        assert model.tags[0].id == tag.id
        assert len(tag.models) == 1
        assert tag.models[0].id == model.id

    @pytest.mark.asyncio
    async def test_user_conversation_association(self, db_session, test_user, test_conversation):
        """Test user-conversation many-to-many relationship."""
        # Associate the user with the conversation
        test_conversation.users.append(test_user)
        await db_session.commit()
        await db_session.refresh(test_conversation)
        await db_session.refresh(test_user)

        # Check association
        assert len(test_conversation.users) == 1
        assert test_conversation.users[0].id == test_user.id
        assert len(test_user.conversations) == 1
        assert test_user.conversations[0].id == test_conversation.id

    @pytest.mark.asyncio
    async def test_message_replies(self, db_session, test_conversation, test_user):
        """Test message hierarchical replies."""
        # Create a parent message
        parent_message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            role="user",
            content="Parent message"
        )
        db_session.add(parent_message)
        await db_session.commit()
        await db_session.refresh(parent_message)

        # Create a reply message
        reply_message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            role="assistant",
            content="Reply message",
            parent_id=parent_message.id
        )
        db_session.add(reply_message)
        await db_session.commit()
        await db_session.refresh(parent_message)
        await db_session.refresh(reply_message)

        # Check relationship
        assert reply_message.parent_id == parent_message.id
        assert len(parent_message.replies) == 1
        assert parent_message.replies[0].id == reply_message.id