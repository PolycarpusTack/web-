import pytest
import time
import asyncio
from sqlalchemy import text
from db.models import User, APIKey, Model, Tag, Conversation, Message, File, MessageThread
from db.crud import create_user, create_model, create_conversation, add_message
from db.optimized_crud import get_user_conversations, get_conversation_messages


@pytest.mark.slow
@pytest.mark.integration
class TestIndexPerformance:
    """
    These tests evaluate database index performance.
    They create a large dataset and measure query performance.
    """

    async def _create_test_dataset(self, db_session):
        """Create a reasonably sized test dataset for performance testing."""
        # Create test users
        users = []
        for i in range(10):
            user = await create_user(
                db=db_session,
                username=f"perf_user_{i}",
                email=f"perf{i}@example.com",
                hashed_password=f"hashedpw{i}"
            )
            users.append(user)
        
        # Create test models
        models = []
        for i in range(5):
            model = await create_model(
                db=db_session,
                model_data={
                    "id": f"perf-model-{i}",
                    "name": f"Performance Test Model {i}",
                    "provider": f"provider-{i % 3}",
                    "is_active": i % 2 == 0,
                    "context_window": 4096
                }
            )
            models.append(model)
        
        # Create conversations (10 per user, with different models)
        conversations = []
        for user in users:
            for i in range(10):
                model = models[i % len(models)]
                conversation = await create_conversation(
                    db=db_session,
                    model_id=model.id,
                    title=f"Perf Test Conversation {user.username}-{i}"
                )
                # Add user to conversation
                conversation.users.append(user)
                await db_session.commit()
                conversations.append(conversation)
        
        # Create messages (30 per conversation on average)
        for conversation in conversations:
            msg_count = 20 + (hash(conversation.id) % 20)  # 20-40 messages
            user = conversation.users[0]
            for i in range(msg_count):
                role = "user" if i % 2 == 0 else "assistant"
                user_id = user.id if role == "user" else None
                await add_message(
                    db=db_session,
                    conversation_id=conversation.id,
                    role=role,
                    content=f"Performance test message {i} in conversation {conversation.id}",
                    user_id=user_id,
                    tokens=10,
                    cost=0.00001
                )
        
        return users, models, conversations

    @pytest.mark.asyncio
    async def test_conversation_query_performance(self, db_session):
        """Test that querying conversations with indexes is fast."""
        users, models, conversations = await self._create_test_dataset(db_session)
        
        # Get a user with many conversations
        test_user = users[0]
        
        # Measure query time without specific indexes
        start_time = time.time()
        user_conversations = await get_user_conversations(
            db=db_session,
            user_id=test_user.id
        )
        query_time_ms = (time.time() - start_time) * 1000
        
        # Verify we found the expected conversations
        assert len(user_conversations) == 10
        
        # Check performance - should be reasonably fast
        assert query_time_ms < 200, f"Query took {query_time_ms}ms, which exceeds the 200ms threshold"
        
        # Filter by model
        model = models[0]
        start_time = time.time()
        model_conversations = await get_user_conversations(
            db=db_session,
            user_id=test_user.id,
            model_id=model.id
        )
        model_query_time_ms = (time.time() - start_time) * 1000
        
        # Performance should be good with the model_id index
        assert model_query_time_ms < 150, f"Model filtered query took {model_query_time_ms}ms, which exceeds the 150ms threshold"

    @pytest.mark.asyncio
    async def test_message_query_performance(self, db_session):
        """Test that querying messages with indexes is fast."""
        users, models, conversations = await self._create_test_dataset(db_session)
        
        # Get a conversation with many messages
        test_conversation = conversations[0]
        
        # Measure query time
        start_time = time.time()
        messages = await get_conversation_messages(
            db=db_session,
            conversation_id=test_conversation.id
        )
        query_time_ms = (time.time() - start_time) * 1000
        
        # Verify we found at least 20 messages
        assert len(messages) >= 20
        
        # Check performance - should be reasonably fast
        assert query_time_ms < 150, f"Query took {query_time_ms}ms, which exceeds the 150ms threshold"
        
        # Test pagination performance
        start_time = time.time()
        paginated_messages = await get_conversation_messages(
            db=db_session,
            conversation_id=test_conversation.id,
            skip=10,
            limit=10
        )
        pagination_time_ms = (time.time() - start_time) * 1000
        
        # Verify pagination worked
        assert len(paginated_messages) == 10
        
        # Performance should be good with proper indexes
        assert pagination_time_ms < 100, f"Paginated query took {pagination_time_ms}ms, which exceeds the 100ms threshold"

    @pytest.mark.asyncio
    async def test_explain_query_plans(self, db_session):
        """Test that queries are using indexes by examining query plans."""
        users, models, conversations = await self._create_test_dataset(db_session)
        user = users[0]
        conversation = conversations[0]
        
        # For SQLite, we can use EXPLAIN QUERY PLAN to see if indexes are used
        
        # Check user conversations query plan
        result = await db_session.execute(text(
            f"""
            EXPLAIN QUERY PLAN
            SELECT conversations.id FROM conversations
            JOIN user_conversation_association 
                ON conversations.id = user_conversation_association.conversation_id
            WHERE user_conversation_association.user_id = '{user.id}'
            ORDER BY conversations.updated_at DESC
            """
        ))
        plan_rows = result.all()
        plan_text = '\n'.join(str(row) for row in plan_rows)
        
        # In query plans, "SEARCH" instead of "SCAN" generally indicates index usage
        assert "SEARCH" in plan_text, f"Query plan does not show index usage: {plan_text}"
        
        # Check messages query plan
        result = await db_session.execute(text(
            f"""
            EXPLAIN QUERY PLAN
            SELECT messages.id FROM messages
            WHERE messages.conversation_id = '{conversation.id}'
            ORDER BY messages.created_at
            """
        ))
        plan_rows = result.all()
        plan_text = '\n'.join(str(row) for row in plan_rows)
        
        # Check for index usage
        assert "SEARCH" in plan_text, f"Messages query plan does not show index usage: {plan_text}"