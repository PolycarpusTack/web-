
#!/usr/bin/env python
"""
Basic script to start the frontend and backend separately.
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    # Get the base directory
    base_dir = Path(__file__).resolve().parent
    
    # Start backend in a separate process
    print("Starting backend...")
    backend_dir = base_dir / "apps" / "backend"
    backend_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Check if backend started successfully
    if backend_process.poll() is not None:
        # Process exited, print error
        stderr = backend_process.stderr.read()
        print(f"Error starting backend: {stderr}")
        return
    
    print("Backend started successfully!")
    print("API available at http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    
    # Start frontend in a separate process
    print("\nStarting frontend...")
    frontend_dir = base_dir / "apps" / "frontend"
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for frontend to start
    time.sleep(3)
    
    # Check if frontend started successfully
    if frontend_process.poll() is not None:
        # Process exited, print error
        stderr = frontend_process.stderr.read()
        print(f"Error starting frontend: {stderr}")
        # Kill backend process
        backend_process.terminate()
        return
    
    print("Frontend started successfully!")
    print("Web UI available at http://localhost:5173")
    
    print("\nPress Ctrl+C to stop both services...")
    
    try:
        # Keep running until user interrupts
        while True:
            # Print some backend output
            backend_line = backend_process.stdout.readline()
            if backend_line:
                print(f"[Backend] {backend_line.strip()}")
                
            # Print some frontend output
            frontend_line = frontend_process.stdout.readline()
            if frontend_line:
                print(f"[Frontend] {frontend_line.strip()}")
                
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("Services stopped!")

if __name__ == "__main__":
    main()
