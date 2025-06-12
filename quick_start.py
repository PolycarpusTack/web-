#!/usr/bin/env python
"""
Quick fix script to start the Web+ application with proper configuration.
"""
import os
import sys
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_root, "apps", "backend")
    frontend_dir = os.path.join(project_root, "apps", "frontend")
    
    # Step 1: Initialize database if needed
    logger.info("Checking database...")
    db_path = os.path.join(backend_dir, "web_plus.db")
    if not os.path.exists(db_path):
        logger.info("Database not found, initializing...")
        subprocess.run([sys.executable, "init_db_sqlite.py"], cwd=project_root)
    
    # Step 2: Start backend on port 8002
    logger.info("Starting backend on port 8002...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
        cwd=backend_dir
    )
    
    # Wait for backend to start
    time.sleep(5)
    
    # Step 3: Start frontend
    logger.info("Starting frontend...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )
    
    logger.info("Web+ is starting up...")
    logger.info("Backend: http://localhost:8002")
    logger.info("Frontend: http://localhost:5173")
    
    try:
        # Keep running until interrupted
        backend_process.wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()
