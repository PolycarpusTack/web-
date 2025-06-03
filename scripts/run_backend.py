#!/usr/bin/env python
"""
Script to run the backend with database initialization.
This script initializes the database and then starts the FastAPI server.
"""

import os
import sys
import asyncio
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Get the backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(os.path.dirname(script_dir), "apps", "backend")
    
    # Make sure we're in the backend directory
    os.chdir(backend_dir)
    
    # Add the backend directory to the Python path
    sys.path.insert(0, backend_dir)
    
    try:
        # Import and run the database initialization
        logger.info("Initializing database...")
        from db.init_db import init_db
        await init_db()
        logger.info("Database initialization complete")
        
        # Start the FastAPI server using uvicorn
        logger.info("Starting FastAPI server...")
        subprocess.run(["python3", "main.py"], check=True)
        
    except ImportError as e:
        logger.error(f"Error importing database module: {e}")
        logger.error("Make sure you're running this script from the project root directory")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting FastAPI server: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
