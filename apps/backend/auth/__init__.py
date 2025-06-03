"""
Authentication module for the web-plus application.
Provides user authentication, authorization, and password management.
"""

from auth.jwt import (
    get_current_user,
    get_current_active_user,
    get_current_superuser
)
from auth.password import hash_password, verify_password
