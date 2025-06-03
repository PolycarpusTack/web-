
#!/usr/bin/env python
"""
Simplified script to run the backend with database initialization.
"""
import os
import sys
import logging
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Get the backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(os.path.dirname(script_dir), "apps", "backend")
    
    # Make sure we're in the backend directory
    os.chdir(backend_dir)
    logger.info(f"Changed directory to: {backend_dir}")
    
    # Start the FastAPI server using uvicorn directly
    logger.info("Starting FastAPI server using uvicorn...")
    try:
        subprocess.run(["uvicorn", "main:app", "--reload"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting uvicorn: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
