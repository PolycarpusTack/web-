# Full Web+ Application Startup Script

import os
import sys
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def start_backend():
    """Start the backend server"""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend")
    
    # Set environment to avoid the shutdown issue
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    logger.info("Starting Web+ Backend on port 8002...")
    
    # Start backend without workers to avoid the shutdown issue
    backend_cmd = [
        sys.executable,
        "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8002",
        "--no-use-colors"  # Avoid color codes in output
    ]
    
    return subprocess.Popen(
        backend_cmd,
        cwd=backend_dir,
        env=env
    )

def start_frontend():
    """Start the frontend server"""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "frontend")
    
    logger.info("Starting Web+ Frontend on port 5173...")
    
    # Start frontend
    frontend_cmd = ["npm", "run", "dev"]
    
    return subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir,
        shell=True
    )

def main():
    logger.info("Starting Web+ Full Application")
    
    # Start backend
    backend_process = start_backend()
    
    # Wait for backend to initialize
    logger.info("Waiting for backend to initialize...")
    time.sleep(10)
    
    # Start frontend
    frontend_process = start_frontend()
    
    logger.info("\n" + "="*50)
    logger.info("Web+ is starting up!")
    logger.info("Backend: http://localhost:8002")
    logger.info("Frontend: http://localhost:5173")
    logger.info("API Docs: http://localhost:8002/docs")
    logger.info("="*50 + "\n")
    
    try:
        # Keep running
        backend_process.wait()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()
