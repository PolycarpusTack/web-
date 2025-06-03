from passlib.context import CryptContext
import re
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordStrength(BaseModel):
    """Model for password strength evaluation."""
    strength: str  # "weak", "medium", "strong", "very-strong"
    score: int  # 0-100
    issues: list[str] = []
    suggestions: list[str] = []
    passes_requirements: bool

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def evaluate_password_strength(password: str) -> PasswordStrength:
    """
    Evaluate the strength of a password.
    
    Args:
        password: The password to evaluate
        
    Returns:
        PasswordStrength object with the evaluation
    """
    issues = []
    suggestions = []
    score = 0
    
    # Length check (up to 50 points)
    length_score = min(len(password) * 5, 50)
    score += length_score
    
    if len(password) < 8:
        issues.append("Password is too short")
        suggestions.append("Use at least 8 characters")
    
    # Complexity checks (up to 50 points)
    has_lowercase = bool(re.search(r"[a-z]", password))
    has_uppercase = bool(re.search(r"[A-Z]", password))
    has_digits = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    
    complexity_score = (has_lowercase + has_uppercase + has_digits + has_special) * 12.5
    score += complexity_score
    
    if not has_lowercase:
        issues.append("No lowercase letters")
        suggestions.append("Include lowercase letters (a-z)")
    
    if not has_uppercase:
        issues.append("No uppercase letters")
        suggestions.append("Include uppercase letters (A-Z)")
    
    if not has_digits:
        issues.append("No numbers")
        suggestions.append("Include numbers (0-9)")
    
    if not has_special:
        issues.append("No special characters")
        suggestions.append("Include special characters (!@#$%^&*)")
    
    # Common patterns check
    common_patterns = [
        "123", "1234", "12345", "123456", "654321", 
        "password", "qwerty", "admin", "welcome",
        "abc", "abcd", "abcde"
    ]
    
    for pattern in common_patterns:
        if pattern.lower() in password.lower():
            issues.append(f"Contains common pattern: '{pattern}'")
            suggestions.append("Avoid common patterns and sequences")
            score -= 10
            break
    
    # Determine strength level
    if score < 30:
        strength = "weak"
    elif score < 60:
        strength = "medium"
    elif score < 80:
        strength = "strong"
    else:
        strength = "very-strong"
    
    # Calculate if it passes minimum requirements
    passes_requirements = (
        len(password) >= 8 and
        has_lowercase and
        has_uppercase and
        has_digits and
        score >= 50
    )
    
    return PasswordStrength(
        strength=strength,
        score=max(0, int(score)),  # Ensure score is not negative
        issues=issues,
        suggestions=suggestions,
        passes_requirements=passes_requirements
    )
