"""
Frontend server with API mocking for Web+.
This script starts the frontend and provides mock API responses,
allowing the frontend to function without a real backend.
"""
import os
import sys
import subprocess
import threading
import json
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock data for API responses
MOCK_MODELS = [
    {
        "id": "llama2:7b",
        "name": "Llama 2 7B",
        "size": "3.8 GB",
        "status": "available",
        "running": False,
        "metadata": {"provider": "meta"}
    },
    {
        "id": "codellama:7b",
        "name": "Code Llama 7B",
        "size": "3.8 GB",
        "status": "available",
        "running": False,
        "metadata": {"provider": "meta"}
    },
    {
        "id": "mistral:7b-instruct",
        "name": "Mistral 7B Instruct",
        "size": "4.1 GB",
        "status": "available",
        "running": False,
        "metadata": {"provider": "mistral"}
    },
    {
        "id": "gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "size": "Unknown",
        "status": "available",
        "running": True,
        "metadata": {"provider": "openai"}
    },
    {
        "id": "claude-3-opus",
        "name": "Claude 3 Opus",
        "size": "Unknown",
        "status": "available",
        "running": True,
        "metadata": {"provider": "anthropic"}
    }
]

# Mock API handler
class MockAPIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        # Handle model listing
        if self.path == "/api/models/available":
            self._set_headers()
            response = {
                "models": MOCK_MODELS,
                "cache_hit": False
            }
            self.wfile.write(json.dumps(response).encode())
        # Health check
        elif self.path == "/health":
            self._set_headers()
            response = {
                "status": "healthy", 
                "message": "Mock API is running"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"detail": "Not found"}).encode())
    
    def do_POST(self):
        # Start model
        if self.path == "/api/models/start":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode())
            
            model_id = body.get("model_id")
            
            # Update model status
            for model in MOCK_MODELS:
                if model["id"] == model_id:
                    model["status"] = "running"
                    model["running"] = True
                    break
            
            self._set_headers()
            response = {
                "message": f"Model {model_id} started successfully",
                "model_id": model_id,
                "status": "running"
            }
            self.wfile.write(json.dumps(response).encode())
        
        # Stop model
        elif self.path == "/api/models/stop":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode())
            
            model_id = body.get("model_id")
            
            # Update model status
            for model in MOCK_MODELS:
                if model["id"] == model_id:
                    model["status"] = "available"
                    model["running"] = False
                    break
            
            self._set_headers()
            response = {
                "message": f"Model {model_id} stopped successfully",
                "model_id": model_id,
                "status": "stopped"
            }
            self.wfile.write(json.dumps(response).encode())
        
        # Chat completion
        elif self.path == "/api/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode())
            
            model_id = body.get("model_id", "unknown")
            prompt = body.get("prompt", "")
            
            # Generate a simple response
            response_text = f"This is a mock response from {model_id}. You asked: {prompt}\n\nSince this is running in mock mode without a real backend, I cannot provide actual AI responses. Please start the full backend to use actual LLM functionality."
            
            self._set_headers()
            response = {
                "id": "mock-response-12345",
                "model": model_id,
                "created": int(time.time()),
                "content": response_text,
                "processing_time": 0.5,
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(prompt.split()) + len(response_text.split()),
                    "prompt_cost": 0.0,
                    "completion_cost": 0.0,
                    "total_cost": 0.0
                },
                "conversation_id": None
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"detail": "Not found"}).encode())

def run_mock_api(port=8000):
    """Run the mock API server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, MockAPIHandler)
    logger.info(f"Starting mock API server on http://localhost:{port}")
    httpd.serve_forever()

def start_frontend():
    """Start the frontend development server."""
    # Get the base directory
    base_dir = Path(__file__).resolve().parent
    frontend_dir = base_dir / "apps" / "frontend"
    
    if not frontend_dir.exists():
        logger.error(f"Frontend directory not found: {frontend_dir}")
        return
    
    logger.info(f"Starting frontend from {frontend_dir}")
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    
    # Run npm install
    logger.info("Installing frontend dependencies...")
    subprocess.run(["npm", "install"], check=True)
    
    # Run npm dev
    logger.info("Starting frontend development server...")
    subprocess.run(["npm", "run", "dev"], check=True)

def main():
    """Run the mock API and frontend servers."""
    # Start mock API in a separate thread
    api_thread = threading.Thread(target=run_mock_api)
    api_thread.daemon = True
    api_thread.start()
    
    # Allow time for API server to start
    time.sleep(1)
    
    # Start frontend
    try:
        start_frontend()
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
    except Exception as e:
        logger.error(f"Error starting frontend: {e}")

if __name__ == "__main__":
    main()
