"""
Advanced Model Search API

This module provides comprehensive search capabilities for AI models including
full-text search, filtering, sorting, and fuzzy matching.
"""
import re
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from db.database import get_db
from db.models import Model, Tag, model_tag_association
from auth.jwt import get_current_user


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PROVIDER = "provider"
    CONTEXT_WINDOW = "context_window"
    POPULARITY = "popularity"  # Based on usage
    COST = "cost"  # Based on pricing


@dataclass
class SearchFilter:
    """Represents a search filter."""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains
    value: Any


class ModelSearchRequest(BaseModel):
    """Model search request parameters."""
    query: Optional[str] = Field(None, description="Full-text search query")
    provider: Optional[List[str]] = Field(None, description="Filter by providers")
    capabilities: Optional[List[str]] = Field(None, description="Filter by capabilities")
    min_context_window: Optional[int] = Field(None, description="Minimum context window size")
    max_context_window: Optional[int] = Field(None, description="Maximum context window size")
    min_cost: Optional[float] = Field(None, description="Minimum cost per token")
    max_cost: Optional[float] = Field(None, description="Maximum cost per token")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    
    # Sorting
    sort_by: SortField = Field(SortField.NAME, description="Field to sort by")
    sort_direction: SortDirection = Field(SortDirection.ASC, description="Sort direction")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    # Search options
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    include_inactive: bool = Field(False, description="Include inactive models")


class ModelSearchResponse(BaseModel):
    """Model search response."""
    models: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    search_metadata: Dict[str, Any]


class SearchSuggestion(BaseModel):
    """Search suggestion."""
    text: str
    type: str  # "model", "provider", "tag", "capability"
    score: float


class AdvancedModelSearch:
    """Advanced model search engine."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def search_models(self, request: ModelSearchRequest) -> ModelSearchResponse:
        """Perform advanced model search."""
        # Build base query
        query = select(Model).options(selectinload(Model.tags))
        
        # Apply filters
        filters = []
        
        # Text search
        if request.query:
            if request.fuzzy_search:
                text_filter = await self._build_fuzzy_search_filter(request.query)
            else:
                text_filter = await self._build_text_search_filter(request.query)
            filters.append(text_filter)
        
        # Provider filter
        if request.provider:
            filters.append(Model.provider.in_(request.provider))
        
        # Context window filters
        if request.min_context_window:
            filters.append(Model.context_window >= request.min_context_window)
        if request.max_context_window:
            filters.append(Model.context_window <= request.max_context_window)
        
        # Cost filters (extract from pricing JSON)
        if request.min_cost or request.max_cost:
            cost_filter = await self._build_cost_filter(request.min_cost, request.max_cost)
            if cost_filter is not None:
                filters.append(cost_filter)
        
        # Capabilities filter
        if request.capabilities:
            capabilities_filter = await self._build_capabilities_filter(request.capabilities)
            filters.append(capabilities_filter)
        
        # Tags filter
        if request.tags:
            tags_filter = await self._build_tags_filter(request.tags)
            filters.append(tags_filter)
        
        # Active status filter
        if not request.include_inactive:
            filters.append(Model.is_active == True)
        elif request.is_active is not None:
            filters.append(Model.is_active == request.is_active)
        
        # Apply all filters
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count for pagination
        count_query = select(func.count(Model.id)).where(and_(*filters) if filters else True)
        total_count_result = await self.db.execute(count_query)
        total_count = total_count_result.scalar()
        
        # Apply sorting
        query = await self._apply_sorting(query, request.sort_by, request.sort_direction)
        
        # Apply pagination
        offset = (request.page - 1) * request.page_size
        query = query.offset(offset).limit(request.page_size)
        
        # Execute query
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        # Format response
        formatted_models = [await self._format_model(model) for model in models]
        
        total_pages = (total_count + request.page_size - 1) // request.page_size
        
        # Generate search metadata
        search_metadata = await self._generate_search_metadata(request, total_count)
        
        return ModelSearchResponse(
            models=formatted_models,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            search_metadata=search_metadata
        )
    
    async def _build_text_search_filter(self, query_text: str):
        """Build text search filter for exact matching."""
        search_terms = query_text.split()
        conditions = []
        
        for term in search_terms:
            term_conditions = [
                Model.name.ilike(f"%{term}%"),
                Model.description.ilike(f"%{term}%"),
                Model.provider.ilike(f"%{term}%"),
                Model.id.ilike(f"%{term}%")
            ]
            conditions.append(or_(*term_conditions))
        
        return and_(*conditions)
    
    async def _build_fuzzy_search_filter(self, query_text: str):
        """Build fuzzy search filter using similarity matching."""
        # For SQLite, use LIKE with wildcards
        # For PostgreSQL, could use similarity() function
        search_terms = query_text.split()
        conditions = []
        
        for term in search_terms:
            # Create fuzzy patterns
            fuzzy_patterns = [
                f"%{term}%",  # Contains
                f"{term[:-1]}%" if len(term) > 2 else f"%{term}%",  # Missing last char
                f"%{term[1:]}%" if len(term) > 2 else f"%{term}%",  # Missing first char
            ]
            
            term_conditions = []
            for pattern in fuzzy_patterns:
                term_conditions.extend([
                    Model.name.ilike(pattern),
                    Model.description.ilike(pattern),
                    Model.provider.ilike(pattern),
                    Model.id.ilike(pattern)
                ])
            
            conditions.append(or_(*term_conditions))
        
        return or_(*conditions)
    
    async def _build_cost_filter(self, min_cost: Optional[float], max_cost: Optional[float]):
        """Build cost filter from pricing JSON."""
        if not min_cost and not max_cost:
            return None
        
        conditions = []
        
        # Extract cost from pricing JSON - this is database-specific
        # For SQLite, we'll use JSON functions
        if min_cost:
            conditions.append(
                text("CAST(json_extract(pricing, '$.input_cost_per_token') AS REAL) >= :min_cost")
                .params(min_cost=min_cost)
            )
        
        if max_cost:
            conditions.append(
                text("CAST(json_extract(pricing, '$.input_cost_per_token') AS REAL) <= :max_cost")
                .params(max_cost=max_cost)
            )
        
        return and_(*conditions) if len(conditions) > 1 else conditions[0]
    
    async def _build_capabilities_filter(self, capabilities: List[str]):
        """Build capabilities filter from capabilities JSON."""
        conditions = []
        
        for capability in capabilities:
            # Check if capability exists in JSON array
            conditions.append(
                text("json_extract(capabilities, '$') LIKE :capability")
                .params(capability=f'%{capability}%')
            )
        
        return and_(*conditions)
    
    async def _build_tags_filter(self, tags: List[str]):
        """Build tags filter using joins."""
        # Subquery to find models with specified tags
        tag_subquery = (
            select(model_tag_association.c.model_id)
            .select_from(
                model_tag_association.join(Tag, model_tag_association.c.tag_id == Tag.id)
            )
            .where(Tag.name.in_(tags))
            .group_by(model_tag_association.c.model_id)
            .having(func.count(Tag.id) >= len(tags))  # Model must have ALL specified tags
        )
        
        return Model.id.in_(tag_subquery)
    
    async def _apply_sorting(self, query, sort_by: SortField, sort_direction: SortDirection):
        """Apply sorting to query."""
        if sort_by == SortField.NAME:
            order_column = Model.name
        elif sort_by == SortField.CREATED_AT:
            order_column = Model.created_at
        elif sort_by == SortField.UPDATED_AT:
            order_column = Model.updated_at
        elif sort_by == SortField.PROVIDER:
            order_column = Model.provider
        elif sort_by == SortField.CONTEXT_WINDOW:
            order_column = Model.context_window
        elif sort_by == SortField.COST:
            # Sort by cost from pricing JSON
            order_column = text("CAST(json_extract(pricing, '$.input_cost_per_token') AS REAL)")
        elif sort_by == SortField.POPULARITY:
            # For now, use created_at as proxy for popularity
            # In a real system, this would be based on usage statistics
            order_column = Model.created_at
        else:
            order_column = Model.name
        
        if sort_direction == SortDirection.DESC:
            order_column = order_column.desc()
        
        return query.order_by(order_column)
    
    async def _format_model(self, model: Model) -> Dict[str, Any]:
        """Format model for response."""
        return {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "description": model.description,
            "version": model.version,
            "is_active": model.is_active,
            "context_window": model.context_window,
            "max_output_tokens": model.max_output_tokens,
            "capabilities": model.capabilities,
            "pricing": model.pricing,
            "size": model.size,
            "tags": [{"id": tag.id, "name": tag.name} for tag in model.tags] if model.tags else [],
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
    
    async def _generate_search_metadata(self, request: ModelSearchRequest, total_count: int) -> Dict[str, Any]:
        """Generate search metadata for analytics."""
        return {
            "query_text": request.query,
            "filters_applied": {
                "provider": bool(request.provider),
                "capabilities": bool(request.capabilities),
                "context_window": bool(request.min_context_window or request.max_context_window),
                "cost": bool(request.min_cost or request.max_cost),
                "tags": bool(request.tags)
            },
            "sort_by": request.sort_by.value,
            "sort_direction": request.sort_direction.value,
            "fuzzy_search": request.fuzzy_search,
            "results_count": total_count,
            "search_time": datetime.utcnow().isoformat()
        }
    
    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[SearchSuggestion]:
        """Get search suggestions based on partial query."""
        suggestions = []
        
        if len(query) < 2:
            return suggestions
        
        # Model name suggestions
        model_query = select(Model.name, Model.id).where(
            and_(
                Model.name.ilike(f"%{query}%"),
                Model.is_active == True
            )
        ).limit(limit // 3)
        
        model_result = await self.db.execute(model_query)
        for name, model_id in model_result:
            suggestions.append(SearchSuggestion(
                text=name,
                type="model",
                score=self._calculate_suggestion_score(query, name)
            ))
        
        # Provider suggestions
        provider_query = select(Model.provider.distinct()).where(
            Model.provider.ilike(f"%{query}%")
        ).limit(limit // 3)
        
        provider_result = await self.db.execute(provider_query)
        for provider, in provider_result:
            suggestions.append(SearchSuggestion(
                text=provider,
                type="provider",
                score=self._calculate_suggestion_score(query, provider)
            ))
        
        # Tag suggestions
        tag_query = select(Tag.name).where(
            Tag.name.ilike(f"%{query}%")
        ).limit(limit // 3)
        
        tag_result = await self.db.execute(tag_query)
        for tag_name, in tag_result:
            suggestions.append(SearchSuggestion(
                text=tag_name,
                type="tag",
                score=self._calculate_suggestion_score(query, tag_name)
            ))
        
        # Sort by score and return top results
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:limit]
    
    def _calculate_suggestion_score(self, query: str, text: str) -> float:
        """Calculate suggestion relevance score."""
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Exact match gets highest score
        if query_lower == text_lower:
            return 1.0
        
        # Starts with query gets high score
        if text_lower.startswith(query_lower):
            return 0.9
        
        # Contains query gets medium score
        if query_lower in text_lower:
            return 0.7
        
        # Fuzzy match gets lower score
        # Simple implementation: count common characters
        common_chars = len(set(query_lower) & set(text_lower))
        return min(0.5, common_chars / len(query_lower))


# Router
router = APIRouter(prefix="/api/models", tags=["Model Search"])


@router.post("/search", response_model=ModelSearchResponse)
async def search_models(
    request: ModelSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Advanced model search with full-text search, filtering, and sorting.
    
    Features:
    - Full-text search across name, description, provider
    - Filter by provider, capabilities, context window, cost, tags
    - Sort by various fields with direction control
    - Fuzzy matching for typos
    - Pagination support
    """
    search_engine = AdvancedModelSearch(db)
    return await search_engine.search_models(request)


@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get search suggestions for autocomplete.
    
    Returns suggestions for:
    - Model names
    - Providers  
    - Tags
    - Capabilities
    """
    search_engine = AdvancedModelSearch(db)
    suggestions = await search_engine.get_search_suggestions(q, limit)
    return {"suggestions": suggestions}


@router.get("/search/filters")
async def get_available_filters(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get available filter options for the search interface.
    
    Returns:
    - Available providers
    - Available tags
    - Context window range
    - Cost range
    - Capabilities list
    """
    # Get available providers
    provider_query = select(Model.provider.distinct()).where(Model.is_active == True)
    provider_result = await db.execute(provider_query)
    providers = [provider for provider, in provider_result]
    
    # Get available tags
    tag_query = select(Tag.name).order_by(Tag.name)
    tag_result = await db.execute(tag_query)
    tags = [tag for tag, in tag_result]
    
    # Get context window range
    context_query = select(
        func.min(Model.context_window),
        func.max(Model.context_window)
    ).where(and_(Model.is_active == True, Model.context_window.isnot(None)))
    context_result = await db.execute(context_query)
    min_context, max_context = context_result.first()
    
    # Get cost range (from pricing JSON)
    cost_query = select(Model.pricing).where(
        and_(Model.is_active == True, Model.pricing.isnot(None))
    )
    cost_result = await db.execute(cost_query)
    costs = []
    for pricing, in cost_result:
        if pricing and 'input_cost_per_token' in pricing:
            costs.append(pricing['input_cost_per_token'])
    
    min_cost = min(costs) if costs else None
    max_cost = max(costs) if costs else None
    
    # Get common capabilities
    capabilities_query = select(Model.capabilities).where(
        and_(Model.is_active == True, Model.capabilities.isnot(None))
    )
    capabilities_result = await db.execute(capabilities_query)
    all_capabilities = set()
    for capabilities, in capabilities_result:
        if capabilities and isinstance(capabilities, list):
            all_capabilities.update(capabilities)
    
    return {
        "providers": sorted(providers),
        "tags": tags,
        "context_window_range": {
            "min": min_context,
            "max": max_context
        },
        "cost_range": {
            "min": min_cost,
            "max": max_cost
        },
        "capabilities": sorted(list(all_capabilities))
    }