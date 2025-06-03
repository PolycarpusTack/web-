"""
API utility functions for pagination, filtering, and response formatting.
This module provides utilities for common API operations.
"""

from fastapi import Query, Request
from pydantic import BaseModel, Field
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from .error_handling import APIResult
import math

# TypeVar for generic pagination
T = TypeVar('T')

# Pagination models
class PaginationParams:
    """
    Class for handling pagination parameters.
    
    This is used as a dependency in API endpoints to handle pagination.
    """
    
    def __init__(
        self, 
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size

class PaginationMetadata(BaseModel):
    """Metadata for paginated responses."""
    
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel, Generic[T]):
    """A standard response for paginated data."""
    
    items: List[T]
    metadata: PaginationMetadata

# Filtering utilities
def apply_filters(
    query_params: Dict[str, Any],
    allowed_filters: List[str]
) -> Dict[str, Any]:
    """
    Extract and validate filter parameters from query parameters.
    
    Args:
        query_params: Dictionary of query parameters
        allowed_filters: List of allowed filter field names
        
    Returns:
        Dictionary of validated filters
    """
    return {k: v for k, v in query_params.items() if k in allowed_filters and v is not None}

# Common SQL filtering helpers
def generate_like_filters(
    model_class: Any,
    field_name: str,
    value: str
) -> Any:
    """
    Generate a SQL LIKE filter for a text field.
    
    Args:
        model_class: SQLAlchemy model class
        field_name: Field name to filter on
        value: Value to filter by
        
    Returns:
        SQLAlchemy filter condition
    """
    field = getattr(model_class, field_name)
    return field.ilike(f"%{value}%")

# Pagination helpers
async def paginate_query(
    db: AsyncSession,
    query: Any,
    count_query: Any,
    params: PaginationParams,
    model_class: Type[T]
) -> PaginatedResponse[T]:
    """
    Execute a query with pagination and return a standardized response.
    
    Args:
        db: Database session
        query: SQLAlchemy query object
        count_query: SQLAlchemy query object for counting total items
        params: Pagination parameters
        model_class: Pydantic model class for items
        
    Returns:
        Paginated response with items and metadata
    """
    # Apply pagination to the query
    query = query.offset(params.skip).limit(params.page_size)
    
    # Execute the query and count query
    result = await db.execute(query)
    count_result = await db.execute(count_query)
    
    # Get the items and total count
    items = result.scalars().all()
    total_items = count_result.scalar()
    
    # Calculate pagination metadata
    total_pages = math.ceil(total_items / params.page_size) if total_items > 0 else 0
    has_next = params.page < total_pages
    has_prev = params.page > 1
    
    # Create the paginated response
    metadata = PaginationMetadata(
        page=params.page,
        page_size=params.page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
    
    return PaginatedResponse(items=items, metadata=metadata)

# Response formatting
def create_response(
    data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized API response.
    
    Args:
        data: The response data
        metadata: Additional metadata for the response
        message: Optional message
        
    Returns:
        Formatted response dictionary
    """
    response = {"success": True}
    
    if data is not None:
        response["data"] = data
        
    if metadata is not None:
        response["metadata"] = metadata
        
    if message is not None:
        response["message"] = message
        
    return response

# API utility functions
def get_base_url(request: Request) -> str:
    """
    Get the base URL from a request object.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Base URL (scheme + host)
    """
    return f"{request.url.scheme}://{request.url.netloc}"

def generate_pagination_links(
    request: Request,
    metadata: PaginationMetadata
) -> Dict[str, str]:
    """
    Generate pagination links for a response.
    
    Args:
        request: FastAPI request object
        metadata: Pagination metadata
        
    Returns:
        Dictionary of links (self, next, prev, first, last)
    """
    # Get the base URL and query parameters
    base_url = str(request.url).split('?')[0]
    query_params = dict(request.query_params)
    
    # Create links
    links = {
        "self": f"{base_url}?{query_params_to_str(query_params)}"
    }
    
    # Add next link if there is a next page
    if metadata.has_next:
        next_params = query_params.copy()
        next_params["page"] = metadata.page + 1
        links["next"] = f"{base_url}?{query_params_to_str(next_params)}"
    
    # Add prev link if there is a previous page
    if metadata.has_prev:
        prev_params = query_params.copy()
        prev_params["page"] = metadata.page - 1
        links["prev"] = f"{base_url}?{query_params_to_str(prev_params)}"
    
    # Add first and last links
    first_params = query_params.copy()
    first_params["page"] = 1
    links["first"] = f"{base_url}?{query_params_to_str(first_params)}"
    
    last_params = query_params.copy()
    last_params["page"] = metadata.total_pages
    links["last"] = f"{base_url}?{query_params_to_str(last_params)}"
    
    return links

def query_params_to_str(params: Dict[str, Any]) -> str:
    """
    Convert a dictionary of query parameters to a URL query string.
    
    Args:
        params: Dictionary of query parameters
        
    Returns:
        URL query string
    """
    return "&".join(f"{k}={v}" for k, v in params.items())
