"""
Test environment setup script for Web+ backend.

This script installs the required dependencies for testing and sets up
the test environment.
"""

import subprocess
import sys
import os


def install_dependencies():
    """Install required dependencies for testing."""
    print("Installing test dependencies...")
    
    # Basic requirements
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    ])
    
    # Test dependencies
    test_packages = [
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "faker>=19.13.0",
        "asgi-lifespan>=2.1.0"
    ]
    
    subprocess.check_call([
        sys.executable, "-m", "pip", "install"
    ] + test_packages)
    
    print("Dependencies installed successfully.")


def setup_test_db():
    """Set up test database."""
    print("Setting up test database...")
    
    # Create test database directory if it doesn't exist
    os.makedirs("./tests/db", exist_ok=True)
    
    print("Test environment setup complete.")


def main():
    """Run the setup process."""
    print("Setting up Web+ test environment...")
    
    install_dependencies()
    setup_test_db()
    
    print("Test environment setup complete.")
    print("Run tests with: make test-cov")


if __name__ == "__main__":
    main()