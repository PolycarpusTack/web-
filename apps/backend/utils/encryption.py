"""
Secure encryption utilities for provider credentials.

This module provides encryption and decryption functionality for sensitive data
like API keys and provider credentials.
"""

import os
import base64
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """Handles encryption and decryption of provider credentials."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize encryption with a key."""
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Get from environment or generate
            self.key = self._get_or_create_encryption_key()
        
        # Derive Fernet key from the provided key
        self.fernet = self._create_fernet_key(self.key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get encryption key from environment or create a new one."""
        env_key = os.getenv("PROVIDER_ENCRYPTION_KEY")
        if env_key:
            return env_key.encode()
        
        # Generate a new key (in production, this should be stored securely)
        logger.warning(
            "No PROVIDER_ENCRYPTION_KEY found in environment. "
            "Generating a new key. This should be set in production!"
        )
        return Fernet.generate_key()
    
    def _create_fernet_key(self, password: bytes) -> Fernet:
        """Create a Fernet key from password using PBKDF2."""
        # Use a fixed salt for consistency (in production, consider user-specific salts)
        salt = b"webplus_provider_salt_2024"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # Adjust based on security requirements
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credential data."""
        try:
            # Convert to JSON string
            json_str = json.dumps(credentials)
            
            # Encrypt
            encrypted_data = self.fernet.encrypt(json_str.encode())
            
            # Return base64 encoded string for database storage
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credential data."""
        try:
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError(f"Decryption failed: {e}")
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt a single API key."""
        return self.encrypt_credentials({"api_key": api_key})
    
    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """Decrypt a single API key."""
        decrypted = self.decrypt_credentials(encrypted_api_key)
        return decrypted.get("api_key", "")


# Global encryption instance
_encryption_instance = None


def get_encryption() -> CredentialEncryption:
    """Get the global encryption instance."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = CredentialEncryption()
    return _encryption_instance


def encrypt_provider_credentials(provider_type: str, credentials: Dict[str, Any]) -> Dict[str, str]:
    """
    Encrypt provider credentials for database storage.
    
    Args:
        provider_type: The provider type (openai, anthropic, etc.)
        credentials: The credential data to encrypt
        
    Returns:
        Dictionary with encrypted_api_key and encrypted_data fields
    """
    encryption = get_encryption()
    
    # Separate API key from other data
    api_key = credentials.get("api_key", "")
    other_data = {k: v for k, v in credentials.items() if k != "api_key"}
    
    result = {}
    
    # Encrypt API key separately
    if api_key:
        result["encrypted_api_key"] = encryption.encrypt_api_key(api_key)
    
    # Encrypt other data if present
    if other_data:
        result["encrypted_data"] = encryption.encrypt_credentials(other_data)
    
    return result


def decrypt_provider_credentials(encrypted_api_key: str, encrypted_data: Optional[str] = None) -> Dict[str, Any]:
    """
    Decrypt provider credentials from database storage.
    
    Args:
        encrypted_api_key: The encrypted API key
        encrypted_data: Optional encrypted additional data
        
    Returns:
        Dictionary with decrypted credential data
    """
    encryption = get_encryption()
    
    result = {}
    
    # Decrypt API key
    if encrypted_api_key:
        result["api_key"] = encryption.decrypt_api_key(encrypted_api_key)
    
    # Decrypt other data if present
    if encrypted_data:
        other_data = encryption.decrypt_credentials(encrypted_data)
        result.update(other_data)
    
    return result


def validate_credentials(provider_type: str, credentials: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate provider credentials format.
    
    Args:
        provider_type: The provider type
        credentials: The credential data to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = {
        "openai": ["api_key"],
        "anthropic": ["api_key"],
        "google": ["api_key"],
        "cohere": ["api_key"],
        "huggingface": ["api_key"],
        "ollama": [],  # Ollama may not require API key for local instances
    }
    
    if provider_type not in required_fields:
        return False, f"Unknown provider type: {provider_type}"
    
    # Check required fields
    required = required_fields[provider_type]
    for field in required:
        if field not in credentials or not credentials[field]:
            return False, f"Missing required field: {field}"
    
    # Validate API key format (basic checks)
    if "api_key" in credentials:
        api_key = credentials["api_key"]
        if not isinstance(api_key, str) or len(api_key.strip()) < 10:
            return False, "API key appears to be invalid (too short)"
    
    # Provider-specific validation
    if provider_type == "openai":
        api_key = credentials.get("api_key", "")
        if not api_key.startswith(("sk-", "sk-proj-")):
            return False, "OpenAI API key should start with 'sk-' or 'sk-proj-'"
    
    elif provider_type == "anthropic":
        api_key = credentials.get("api_key", "")
        if not api_key.startswith("sk-ant-"):
            return False, "Anthropic API key should start with 'sk-ant-'"
    
    elif provider_type == "google":
        api_key = credentials.get("api_key", "")
        # Google AI API keys typically don't have a specific prefix
        if len(api_key) < 20:
            return False, "Google AI API key appears to be too short"
    
    return True, ""


# Utility function for testing encryption/decryption
def test_encryption():
    """Test encryption and decryption functionality."""
    test_credentials = {
        "api_key": "sk-test-key-12345",
        "organization_id": "org-test",
        "project_id": "proj-test"
    }
    
    print("Testing encryption...")
    
    # Test encryption
    encrypted = encrypt_provider_credentials("openai", test_credentials)
    print(f"Encrypted: {encrypted}")
    
    # Test decryption
    decrypted = decrypt_provider_credentials(
        encrypted.get("encrypted_api_key", ""),
        encrypted.get("encrypted_data")
    )
    print(f"Decrypted: {decrypted}")
    
    # Verify
    assert decrypted == test_credentials, "Encryption/decryption failed!"
    print("✅ Encryption test passed!")


if __name__ == "__main__":
    test_encryption()