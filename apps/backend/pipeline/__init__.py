"""
Code Factory Pipeline Module.

This module contains the implementation of the pipeline system, including
database models, CRUD operations, execution engine, and API endpoints.
"""

from fastapi import APIRouter
from .router import router as pipeline_router

# Export the router for inclusion in the main application
router = pipeline_router