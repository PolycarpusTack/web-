import pytest
import asyncio
from db.optimized_crud import (
    get_users, count_users, get_conversations, get_user_conversations,
    get_conversation_with_messages, get_conversation_messages,
    get_thread_with_messages, get_conversation_files, get_models
)
from db.models import (
    User, APIKey, Model, Tag, Conversation, Message, 
    File, MessageFile, MessageThread
)


@pytest.mark.unit
@pytest.mark.crud
class TestOptimizedCrud:

    @pytest.mark.asyncio
    async def test_get_users_with_filters(self, db_session):
        """Test get_users function with filters."""
        # Create test users with various attributes
        # Regular user
        regular_user = User(
            username="regularuser",
            email="regular@example.com",
            hashed_password="hashedpassword",
            role="user"
        )
        db_session.add(regular_user)

        # Admin user
        admin_user = User(
            username="adminuser",
            email="admin@example.com",
            hashed_password="hashedpassword",
            role="admin"
        )
        db_session.add(admin_user)

        # Inactive user
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password="hashedpassword",
            is_active=False
        )
        db_session.add(inactive_user)

        await db_session.commit()

        # Test with username filter
        users = await get_users(db_session, filters={"username": "admin"})
        assert len(users) == 1
        assert users[0].username == "adminuser"

        # Test with email filter
        users = await get_users(db_session, filters={"email": "regular"})
        assert len(users) == 1
        assert users[0].email == "regular@example.com"

        # Test with active status filter
        users = await get_users(db_session, filters={"is_active": False})
        assert len(users) == 1
        assert users[0].username == "inactiveuser"

        # Test with role filter
        users = await get_users(db_session, filters={"role": "admin"})
        assert len(users) == 1
        assert users[0].role == "admin"

        # Test with multiple filters
        users = await get_users(db_session, filters={"is_active": True, "role": "user"})
        assert len(users) == 1
        assert users[0].username == "regularuser"

        # Test pagination
        all_users = await get_users(db_session)
        assert len(all_users) >= 3

        first_page = await get_users(db_session, skip=0, limit=2)
        assert len(first_page) == 2

        second_page = await get_users(db_session, skip=2, limit=2)
        assert len(second_page) <= 2
        if len(second_page) > 0:
            assert first_page[0].id != second_page[0].id

    @pytest.mark.asyncio
    async def test_count_users(self, db_session):
        """Test count_users function."""
        # Create test users
        user_count_before = await count_users(db_session)

        # Add 5 new users
        for i in range(5):
            user = User(
                username=f"countuser{i}",
                email=f"count{i}@example.com",
                hashed_password="hashedpassword"
            )
            db_session.add(user)
        await db_session.commit()

        # Get total count
        total_count = await count_users(db_session)
        assert total_count == user_count_before + 5

        # Count with filters
        active_count = await count_users(db_session, filters={"is_active": True})
        assert active_count >= 5

        username_count = await count_users(db_session, filters={"username": "countuser"})
        assert username_count == 5

    @pytest.mark.asyncio
    async def test_get_conversations(self, db_session, test_user, test_model):
        """Test get_conversations function."""
        # Create several conversations
        for i in range(3):
            conversation = Conversation(
                title=f"Test Conversation {i}",
                model_id=test_model.id
            )
            db_session.add(conversation)
            await db_session.commit()
            await db_session.refresh(conversation)

            # Add user to conversation
            conversation.users.append(test_user)
            await db_session.commit()

            # Add a message to each conversation
            message = Message(
                conversation_id=conversation.id,
                user_id=test_user.id,
                role="user",
                content=f"Hello in conversation {i}"
            )
            db_session.add(message)

        await db_session.commit()

        # Test basic functionality
        conversations = await get_conversations(db_session)
        assert len(conversations) >= 3

        # Test with filters
        filtered_convs = await get_conversations(
            db_session, 
            filters={"model_id": test_model.id}
        )
        assert len(filtered_convs) >= 3
        for conv in filtered_convs:
            assert conv.model_id == test_model.id

        # Test with user filter
        user_convs = await get_conversations(
            db_session,
            filters={"user_id": test_user.id}
        )
        assert len(user_convs) >= 3

        # Test with title filter
        title_convs = await get_conversations(
            db_session,
            filters={"title": "Test Conversation"}
        )
        assert len(title_convs) >= 3

        # Test with include_messages
        msg_convs = await get_conversations(
            db_session,
            include_messages=True
        )
        assert len(msg_convs) >= 3
        # At least one conversation should have messages
        has_messages = False
        for conv in msg_convs:
            if len(conv.messages) > 0:
                has_messages = True
                break
        assert has_messages is True

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, db_session, test_user, test_model):
        """Test get_user_conversations function."""
        # Ensure we have multiple conversations
        for i in range(3):
            conversation = Conversation(
                title=f"User Conv Test {i}",
                model_id=test_model.id
            )
            db_session.add(conversation)
            await db_session.commit()
            await db_session.refresh(conversation)

            # Add user to conversation
            conversation.users.append(test_user)

            # Add messages
            for j in range(2):
                message = Message(
                    conversation_id=conversation.id,
                    user_id=test_user.id,
                    role="user" if j % 2 == 0 else "assistant",
                    content=f"Message {j} in conversation {i}"
                )
                db_session.add(message)

        await db_session.commit()

        # Test basic functionality
        conversations = await get_user_conversations(db_session, test_user.id)
        assert len(conversations) >= 3

        # Test with model filter
        filtered_convs = await get_user_conversations(
            db_session,
            test_user.id,
            model_id=test_model.id
        )
        assert len(filtered_convs) >= 3
        for conv in filtered_convs:
            assert conv.model_id == test_model.id

        # Test with message count
        count_convs = await get_user_conversations(
            db_session,
            test_user.id,
            include_message_count=True
        )
        assert len(count_convs) >= 3
        
        # Verify message counts
        for conv in count_convs:
            assert hasattr(conv, 'message_count')
            # Each test conversation has at least 2 messages
            assert conv.message_count >= 0

        # Test without message count
        no_count_convs = await get_user_conversations(
            db_session,
            test_user.id,
            include_message_count=False
        )
        assert len(no_count_convs) >= 3
        # Verify no message counts
        for conv in no_count_convs:
            assert not hasattr(conv, 'message_count')

        # Test pagination
        page1 = await get_user_conversations(
            db_session,
            test_user.id,
            skip=0,
            limit=2
        )
        assert len(page1) == 2

        page2 = await get_user_conversations(
            db_session,
            test_user.id,
            skip=2,
            limit=2
        )
        assert len(page2) >= 1
        if len(page2) > 0:
            assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_conversation_with_messages(self, db_session, test_conversation, test_user):
        """Test get_conversation_with_messages function."""
        # Add multiple messages to the conversation
        for i in range(5):
            message = Message(
                conversation_id=test_conversation.id,
                user_id=test_user.id if i % 2 == 0 else None,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i}"
            )
            db_session.add(message)
        await db_session.commit()

        # Get conversation with messages
        conversation = await get_conversation_with_messages(
            db_session,
            test_conversation.id
        )

        # Verify conversation
        assert conversation is not None
        assert conversation.id == test_conversation.id
        assert len(conversation.messages) >= 5

        # Test with pagination
        conversation_page1 = await get_conversation_with_messages(
            db_session,
            test_conversation.id,
            message_skip=0,
            message_limit=3
        )
        assert conversation_page1 is not None
        assert len(conversation_page1.messages) == 3

        conversation_page2 = await get_conversation_with_messages(
            db_session,
            test_conversation.id,
            message_skip=3,
            message_limit=3
        )
        assert conversation_page2 is not None
        assert len(conversation_page2.messages) >= 2
        if len(conversation_page2.messages) > 0:
            assert conversation_page1.messages[0].id != conversation_page2.messages[0].id

        # Test non-existent conversation
        non_existent = await get_conversation_with_messages(
            db_session,
            "non-existent-id"
        )
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, db_session, test_conversation, test_user, test_thread):
        """Test get_conversation_messages function."""
        # Add regular messages to conversation
        for i in range(3):
            message = Message(
                conversation_id=test_conversation.id,
                user_id=test_user.id if i % 2 == 0 else None,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Regular message {i}",
                thread_id=None
            )
            db_session.add(message)

        # Add threaded messages
        for i in range(3):
            message = Message(
                conversation_id=test_conversation.id,
                user_id=test_user.id if i % 2 == 0 else None,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Threaded message {i}",
                thread_id=test_thread.id
            )
            db_session.add(message)

        await db_session.commit()

        # Get all regular messages
        regular_messages = await get_conversation_messages(
            db_session,
            test_conversation.id
        )
        assert len(regular_messages) >= 3
        for msg in regular_messages:
            assert msg.thread_id is None

        # Get threaded messages
        threaded_messages = await get_conversation_messages(
            db_session,
            test_conversation.id,
            thread_id=test_thread.id
        )
        assert len(threaded_messages) >= 3
        for msg in threaded_messages:
            assert msg.thread_id == test_thread.id

        # Test with pagination
        page1 = await get_conversation_messages(
            db_session,
            test_conversation.id,
            skip=0,
            limit=2
        )
        assert len(page1) == 2

        page2 = await get_conversation_messages(
            db_session,
            test_conversation.id,
            skip=2,
            limit=2
        )
        assert len(page2) >= 1
        if len(page2) > 0:
            assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_thread_with_messages(self, db_session, test_thread, test_user):
        """Test get_thread_with_messages function."""
        # Add messages to thread
        for i in range(5):
            message = Message(
                conversation_id=test_thread.conversation_id,
                user_id=test_user.id if i % 2 == 0 else None,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Thread message {i}",
                thread_id=test_thread.id
            )
            db_session.add(message)
        await db_session.commit()

        # Get thread with messages
        thread = await get_thread_with_messages(
            db_session,
            test_thread.id
        )

        # Verify thread
        assert thread is not None
        assert thread.id == test_thread.id
        assert thread.conversation_id == test_thread.conversation_id
        assert len(thread.messages) >= 5

        # Test with pagination
        thread_page1 = await get_thread_with_messages(
            db_session,
            test_thread.id,
            skip=0,
            limit=3
        )
        assert thread_page1 is not None
        assert len(thread_page1.messages) == 3

        thread_page2 = await get_thread_with_messages(
            db_session,
            test_thread.id,
            skip=3,
            limit=3
        )
        assert thread_page2 is not None
        assert len(thread_page2.messages) >= 2
        if len(thread_page2.messages) > 0:
            assert thread_page1.messages[0].id != thread_page2.messages[0].id

        # Test non-existent thread
        non_existent = await get_thread_with_messages(
            db_session,
            "non-existent-id"
        )
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_get_conversation_files(self, db_session, test_conversation, test_user):
        """Test get_conversation_files function."""
        # Add files to conversation
        for i in range(5):
            file = File(
                filename=f"testfile{i}.txt",
                original_filename=f"original{i}.txt",
                content_type="text/plain",
                size=100,
                path=f"/tmp/testfile{i}.txt",
                user_id=test_user.id,
                conversation_id=test_conversation.id,
                analyzed=i % 2 == 0,
                analysis_result={"summary": f"Test file {i}"} if i % 2 == 0 else None
            )
            db_session.add(file)
        await db_session.commit()

        # Get files without analysis
        files_no_analysis = await get_conversation_files(
            db_session,
            test_conversation.id,
            include_analysis=False
        )
        assert len(files_no_analysis) >= 5
        # Analysis results should be excluded
        for file in files_no_analysis:
            assert not hasattr(file, 'analysis_result') or file.analysis_result is None

        # Get files with analysis
        files_with_analysis = await get_conversation_files(
            db_session,
            test_conversation.id,
            include_analysis=True
        )
        assert len(files_with_analysis) >= 5
        # Some files should have analysis results
        has_analysis = False
        for file in files_with_analysis:
            if file.analyzed and file.analysis_result is not None:
                has_analysis = True
                break
        assert has_analysis is True

        # Test pagination
        page1 = await get_conversation_files(
            db_session,
            test_conversation.id,
            skip=0,
            limit=3
        )
        assert len(page1) == 3

        page2 = await get_conversation_files(
            db_session,
            test_conversation.id,
            skip=3,
            limit=3
        )
        assert len(page2) >= 2
        if len(page2) > 0:
            assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_models(self, db_session):
        """Test optimized get_models function."""
        # Create test models
        providers = ["test", "openai", "anthropic"]
        for i, provider in enumerate(providers):
            model = Model(
                id=f"{provider}-model-{i}",
                name=f"{provider.capitalize()} Model {i}",
                provider=provider,
                is_active=i % 2 == 0,
                context_window=4096
            )
            db_session.add(model)
            
            # Create tags for each model
            tag = Tag(name=f"{provider}-tag")
            db_session.add(tag)
            await db_session.commit()
            await db_session.refresh(tag)
            
            model.tags.append(tag)
        
        await db_session.commit()

        # Get all models
        all_models = await get_models(db_session)
        assert len(all_models) >= 3
        
        # Check that tags were eager loaded
        for model in all_models:
            assert hasattr(model, 'tags')
            if len(model.tags) > 0:
                assert model.tags[0].name is not None

        # Test filtering by provider
        openai_models = await get_models(
            db_session,
            filters={"provider": "openai"}
        )
        assert len(openai_models) >= 1
        for model in openai_models:
            assert model.provider == "openai"

        # Test filtering by active status
        active_models = await get_models(
            db_session,
            filters={"is_active": True}
        )
        assert len(active_models) >= 1
        for model in active_models:
            assert model.is_active is True

        # Test filtering by local status
        local_models = await get_models(
            db_session,
            filters={"is_local": True}
        )
        for model in local_models:
            assert model.provider == "ollama"

        # Test pagination
        page1 = await get_models(db_session, skip=0, limit=2)
        assert len(page1) == 2

        page2 = await get_models(db_session, skip=2, limit=2)
        assert len(page2) >= 1
        if len(page2) > 0:
            assert page1[0].id != page2[0].id