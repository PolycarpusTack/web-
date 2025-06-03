"""
Database module for the web-plus application.
Provides database models, CRUD operations, and initialization.
"""

from db.database import (
    get_db,
    Base,
    async_engine,
    sync_engine,
    async_session_maker,
    sync_session_maker,
    get_async_session,
    get_sync_db,
)
