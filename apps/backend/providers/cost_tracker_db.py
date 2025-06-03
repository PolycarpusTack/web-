"""
Database-backed cost tracking and usage monitoring for AI providers.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from .types import ProviderType, TokenUsage
from core.cache import cache_manager, CacheNamespaces

logger = logging.getLogger(__name__)


@dataclass
class UsageMetrics:
    """Aggregated usage metrics."""
    provider: Optional[ProviderType]
    period_start: datetime
    period_end: datetime
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_cost_per_request: float = 0.0
    average_tokens_per_request: float = 0.0
    models_used: Dict[str, int] = field(default_factory=dict)
    operations: Dict[str, int] = field(default_factory=dict)
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    cost_by_operation: Dict[str, float] = field(default_factory=dict)


class DatabaseCostTracker:
    """Database-backed cost tracker for AI provider usage."""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self._provider_pricing: Dict[str, Dict[str, Dict[str, float]]] = {}
        
        # Initialize with known pricing (per 1K tokens)
        self._initialize_pricing()
    
    def _initialize_pricing(self):
        """Initialize known pricing for major providers."""
        # OpenAI pricing (as of 2024)
        self._provider_pricing['openai'] = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-32k': {'input': 0.06, 'output': 0.12},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
            'gpt-4-vision-preview': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
            'text-embedding-ada-002': {'input': 0.0001, 'output': 0.0},
            'text-embedding-3-small': {'input': 0.00002, 'output': 0.0},
            'text-embedding-3-large': {'input': 0.00013, 'output': 0.0},
            'dall-e-3': {'input': 0.0, 'output': 0.0},  # Special pricing for images
            'dall-e-2': {'input': 0.0, 'output': 0.0},  # Special pricing for images
        }
        
        # Anthropic pricing
        self._provider_pricing['anthropic'] = {
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
            'claude-2.1': {'input': 0.008, 'output': 0.024},
            'claude-2.0': {'input': 0.008, 'output': 0.024},
            'claude-instant-1.2': {'input': 0.0008, 'output': 0.0024},
        }
        
        # Google AI pricing
        self._provider_pricing['google'] = {
            'gemini-pro': {'input': 0.00025, 'output': 0.0005},
            'gemini-pro-vision': {'input': 0.00025, 'output': 0.0005},
            'gemini-1.5-pro': {'input': 0.00125, 'output': 0.00375},
            'text-bison': {'input': 0.001, 'output': 0.001},
            'chat-bison': {'input': 0.001, 'output': 0.001},
            'textembedding-gecko': {'input': 0.0001, 'output': 0.0},
        }
        
        # Cohere pricing
        self._provider_pricing['cohere'] = {
            'command-r-plus': {'input': 0.003, 'output': 0.015},
            'command-r': {'input': 0.0005, 'output': 0.0015},
            'command': {'input': 0.0015, 'output': 0.002},
            'command-light': {'input': 0.0003, 'output': 0.0006},
            'embed-english-v3.0': {'input': 0.0001, 'output': 0.0},
            'embed-multilingual-v3.0': {'input': 0.0001, 'output': 0.0},
        }
        
        # Ollama pricing (local models are free)
        self._provider_pricing['ollama'] = {
            # All Ollama models are free since they run locally
            'default': {'input': 0.0, 'output': 0.0},
        }
        
        # HuggingFace pricing (varies by model)
        self._provider_pricing['huggingface'] = {
            'default': {'input': 0.0, 'output': 0.0},  # Most are free
        }
    
    async def record_usage(
        self,
        provider: ProviderType,
        model: str,
        operation: str,
        tokens_used: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        user_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        request_id: Optional[str] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Record usage and calculate cost."""
        
        # Calculate cost
        cost = self.calculate_cost(provider, model, input_tokens, output_tokens)
        
        # Record to database if database session is available
        if self.db:
            try:
                from db.crud import create_usage_record
                await create_usage_record(
                    db=self.db,
                    user_id=user_id or "system",
                    provider_type=provider.value,
                    model_id=model,
                    operation=operation,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    pipeline_id=pipeline_id,
                    execution_id=execution_id,
                    request_id=request_id,
                    response_time=response_time,
                    metadata=metadata or {}
                )
                logger.debug(f"Recorded usage: {provider.value}/{model} - ${cost:.6f}")
            except Exception as e:
                logger.error(f"Failed to record usage to database: {e}")
        
        return cost
    
    def calculate_cost(
        self,
        provider: ProviderType,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> float:
        """Calculate cost based on provider, model, and token usage."""
        
        provider_key = provider.value.lower()
        
        # Get pricing for provider and model
        if provider_key not in self._provider_pricing:
            logger.warning(f"No pricing info for provider: {provider_key}")
            return 0.0
        
        model_pricing = None
        provider_models = self._provider_pricing[provider_key]
        
        # Try exact match first
        if model in provider_models:
            model_pricing = provider_models[model]
        else:
            # Try partial match for model families
            for model_key in provider_models:
                if model_key in model.lower() or model.lower().startswith(model_key):
                    model_pricing = provider_models[model_key]
                    break
        
        if not model_pricing:
            logger.warning(f"No pricing info for model: {provider_key}/{model}")
            # Use default pricing as fallback
            model_pricing = {'input': 0.001, 'output': 0.002}
        
        # Calculate cost (pricing is per 1K tokens)
        input_cost = (input_tokens / 1000) * model_pricing.get('input', 0.0)
        output_cost = (output_tokens / 1000) * model_pricing.get('output', 0.0)
        
        total_cost = input_cost + output_cost
        
        logger.debug(
            f"Cost calculation for {provider_key}/{model}: "
            f"input={input_tokens}*{model_pricing.get('input', 0.0)/1000:.6f} = ${input_cost:.6f}, "
            f"output={output_tokens}*{model_pricing.get('output', 0.0)/1000:.6f} = ${output_cost:.6f}, "
            f"total=${total_cost:.6f}"
        )
        
        return total_cost
    
    async def get_usage_metrics(
        self,
        provider: Optional[ProviderType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> UsageMetrics:
        """Get usage metrics for a time period."""
        
        # Generate cache key
        cache_key = f"usage_metrics_{provider.value if provider else 'all'}_{user_id or 'all'}_{start_date}_{end_date}"
        cached_metrics = await cache_manager.get(CacheNamespaces.ANALYTICS, cache_key)
        if cached_metrics is not None:
            logger.debug(f"Cache hit for usage metrics: {cache_key}")
            return cached_metrics
        
        if not self.db:
            logger.warning("No database session available for metrics")
            return UsageMetrics(
                provider=provider,
                period_start=start_date or datetime.utcnow() - timedelta(days=30),
                period_end=end_date or datetime.utcnow()
            )
        
        try:
            from db.crud import get_usage_summary
            
            summary = await get_usage_summary(
                db=self.db,
                user_id=user_id or "system",
                provider_type=provider.value if provider else None,
                start_date=start_date,
                end_date=end_date
            )
            
            metrics = UsageMetrics(
                provider=provider,
                period_start=start_date or datetime.utcnow() - timedelta(days=30),
                period_end=end_date or datetime.utcnow(),
                total_requests=summary.get('total_requests', 0),
                total_tokens=summary.get('total_tokens', 0),
                total_cost=summary.get('total_cost', 0.0),
                average_cost_per_request=summary.get('average_cost_per_request', 0.0),
                average_tokens_per_request=summary.get('average_tokens_per_request', 0.0),
                models_used=summary.get('models_used', {}),
                operations=summary.get('operations', {}),
                cost_by_model=summary.get('cost_by_model', {}),
                cost_by_operation=summary.get('cost_by_operation', {})
            )
            
            # Cache the metrics with 5 minute TTL
            await cache_manager.set(CacheNamespaces.ANALYTICS, cache_key, metrics, ttl=300)
            logger.debug(f"Cached usage metrics: {cache_key}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get usage metrics: {e}")
            return UsageMetrics(
                provider=provider,
                period_start=start_date or datetime.utcnow() - timedelta(days=30),
                period_end=end_date or datetime.utcnow()
            )
    
    async def get_daily_costs(self, days: int = 30, user_id: Optional[str] = None) -> Dict[str, float]:
        """Get daily cost breakdown."""
        
        # Generate cache key
        cache_key = f"daily_costs_{days}_{user_id or 'all'}"
        cached_costs = await cache_manager.get(CacheNamespaces.ANALYTICS, cache_key)
        if cached_costs is not None:
            logger.debug(f"Cache hit for daily costs: {cache_key}")
            return cached_costs
        
        if not self.db:
            return {}
        
        try:
            from db.crud import get_usage_records
            from sqlalchemy import func, select
            from db.models import UsageRecord
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get daily aggregated costs
            query = select(
                func.date(UsageRecord.created_at).label('date'),
                func.sum(UsageRecord.cost).label('daily_cost')
            ).where(
                UsageRecord.created_at >= start_date
            )
            
            if user_id:
                query = query.where(UsageRecord.user_id == user_id)
            
            query = query.group_by(func.date(UsageRecord.created_at))
            
            result = await self.db.execute(query)
            
            daily_costs = {}
            for row in result:
                date_str = row.date.strftime('%Y-%m-%d')
                daily_costs[date_str] = float(row.daily_cost or 0.0)
            
            # Cache the daily costs with 1 hour TTL
            await cache_manager.set(CacheNamespaces.ANALYTICS, cache_key, daily_costs, ttl=3600)
            logger.debug(f"Cached daily costs: {cache_key}")
            
            return daily_costs
            
        except Exception as e:
            logger.error(f"Failed to get daily costs: {e}")
            return {}
    
    async def check_budget_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Check if any budget alerts should be triggered."""
        
        if not self.db:
            return []
        
        try:
            from db.crud import get_user_budget_alerts, get_usage_summary
            
            # Get user's budget alerts
            alerts = await get_user_budget_alerts(self.db, user_id)
            triggered_alerts = []
            
            for alert in alerts:
                if not alert.is_active:
                    continue
                
                # Calculate period start based on alert period
                if alert.period == 'daily':
                    period_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                elif alert.period == 'weekly':
                    today = datetime.utcnow()
                    period_start = today - timedelta(days=today.weekday())
                    period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
                elif alert.period == 'monthly':
                    today = datetime.utcnow()
                    period_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    continue
                
                # Get usage for this period
                usage = await get_usage_summary(
                    db=self.db,
                    user_id=user_id,
                    provider_type=alert.provider_type,
                    start_date=period_start,
                    end_date=datetime.utcnow()
                )
                
                current_cost = usage.get('total_cost', 0.0)
                
                # Check if threshold is exceeded
                if current_cost >= alert.threshold_amount:
                    triggered_alerts.append({
                        'alert_id': alert.id,
                        'alert_name': alert.alert_name,
                        'threshold': alert.threshold_amount,
                        'current_cost': current_cost,
                        'period': alert.period,
                        'provider_type': alert.provider_type
                    })
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Failed to check budget alerts: {e}")
            return []
    
    async def get_provider_pricing(self, provider: ProviderType, model: str) -> Dict[str, float]:
        """Get pricing information for a specific provider and model."""
        # Generate cache key
        cache_key = f"pricing_{provider.value}_{model}"
        cached_pricing = await cache_manager.get(CacheNamespaces.ANALYTICS, cache_key)
        if cached_pricing is not None:
            logger.debug(f"Cache hit for pricing: {cache_key}")
            return cached_pricing
        
        provider_key = provider.value.lower()
        
        if provider_key not in self._provider_pricing:
            pricing = {'input': 0.0, 'output': 0.0}
            # Cache the pricing with 24 hour TTL (pricing doesn't change often)
            await cache_manager.set(CacheNamespaces.ANALYTICS, cache_key, pricing, ttl=86400)
            logger.debug(f"Cached pricing: {cache_key}")
            return pricing
        
        provider_models = self._provider_pricing[provider_key]
        
        # Try exact match first
        if model in provider_models:
            pricing = provider_models[model]
        else:
            # Try partial match
            pricing = None
            for model_key in provider_models:
                if model_key in model.lower() or model.lower().startswith(model_key):
                    pricing = provider_models[model_key]
                    break
            
            if pricing is None:
                pricing = {'input': 0.0, 'output': 0.0}
        
        # Cache the pricing with 24 hour TTL
        await cache_manager.set(CacheNamespaces.ANALYTICS, cache_key, pricing, ttl=86400)
        logger.debug(f"Cached pricing: {cache_key}")
        
        return pricing


# Global cost tracker instance
_cost_tracker = None


def get_cost_tracker(db: Optional[AsyncSession] = None) -> DatabaseCostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None or (_cost_tracker.db is None and db is not None):
        _cost_tracker = DatabaseCostTracker(db)
    return _cost_tracker


# Legacy compatibility - keep the old class name for backwards compatibility
CostTracker = DatabaseCostTracker