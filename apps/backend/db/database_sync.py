"""
Modified database module for Web+ with SQLite dialect fallback.
"""
import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment or use default SQLite database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "web_plus.db")
logger.info(f"Database path: {db_path}")

# Use standard SQLite connection string (not async)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
logger.info(f"Using database URL: {DATABASE_URL}")

# Create a synchronous engine
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    future=True
)

# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Create base class for declarative models
Base = declarative_base()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Helper function to get a database session
def get_db():
    """
    Gets a database session.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Synchronous version of database initialization
def init_db_sync():
    """Initialize the database synchronously."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
