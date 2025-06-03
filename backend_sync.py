"""
Simple starter script for Web+ backend, using synchronous SQLite connection.
This is a workaround for SQLAlchemy dialect issues.
"""
import os
import sys
import logging
import subprocess
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Get the backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(os.path.dirname(script_dir), "apps", "backend")
    
    logger.info(f"Backend directory: {backend_dir}")
    
    # Add the backend directory to Python path
    sys.path.insert(0, backend_dir)
    
    try:
        # Import and initialize the database
        logger.info("Initializing database using synchronous connection...")
        from db.database_sync import init_db_sync
        init_db_sync()
        logger.info("Database initialization complete")
        
        # Start the FastAPI server using uvicorn directly
        logger.info("Starting FastAPI server...")
        os.chdir(backend_dir)
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"Error importing database module: {e}")
        logger.error("Make sure you're running this script from the project root directory")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
