"""
Cost tracking and usage monitoring for AI providers.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from .types import ProviderType, TokenUsage

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Individual usage record."""
    timestamp: datetime
    provider: ProviderType
    model: str
    operation: str  # 'text_generation', 'embedding', 'image_generation', etc.
    tokens_used: int = 0
    cost: float = 0.0
    user_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageMetrics:
    """Aggregated usage metrics."""
    provider: ProviderType
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


@dataclass
class BudgetAlert:
    """Budget alert configuration."""
    name: str
    threshold_amount: float
    threshold_type: str  # 'daily', 'weekly', 'monthly'
    alert_percentage: float = 80.0  # Alert at 80% of threshold
    is_active: bool = True
    last_alert_sent: Optional[datetime] = None


class CostTracker:
    """Track costs and usage across all AI providers."""
    
    def __init__(self):
        self._usage_records: List[UsageRecord] = []
        self._budget_alerts: List[BudgetAlert] = []
        self._provider_pricing: Dict[str, Dict[str, Dict[str, float]]] = {}
        self._last_cleanup = datetime.utcnow()
        
        # Initialize with known pricing (per 1K tokens)
        self._initialize_pricing()
    
    def _initialize_pricing(self):
        """Initialize known pricing for major providers."""
        # OpenAI pricing (as of 2024)
        self._provider_pricing['openai'] = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-32k': {'input': 0.06, 'output': 0.12},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
            'text-embedding-ada-002': {'input': 0.0001, 'output': 0.0},
            'text-embedding-3-small': {'input': 0.00002, 'output': 0.0},
            'text-embedding-3-large': {'input': 0.00013, 'output': 0.0},
        }
        
        # Anthropic pricing
        self._provider_pricing['anthropic'] = {
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
            'claude-2.1': {'input': 0.008, 'output': 0.024},
            'claude-2.0': {'input': 0.008, 'output': 0.024},
            'claude-instant': {'input': 0.0008, 'output': 0.0024},
        }
        
        # Google AI pricing
        self._provider_pricing['google'] = {
            'gemini-pro': {'input': 0.00025, 'output': 0.0005},
            'gemini-pro-vision': {'input': 0.00025, 'output': 0.0005},
            'text-bison': {'input': 0.001, 'output': 0.001},
            'chat-bison': {'input': 0.001, 'output': 0.001},
            'textembedding-gecko': {'input': 0.0001, 'output': 0.0},
        }
    
    def record_usage(
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Record usage and calculate cost."""
        
        # Calculate cost
        cost = self.calculate_cost(provider, model, input_tokens, output_tokens)
        
        # Create usage record
        record = UsageRecord(
            timestamp=datetime.utcnow(),
            provider=provider,
            model=model,
            operation=operation,
            tokens_used=tokens_used or (input_tokens + output_tokens),
            cost=cost,
            user_id=user_id,
            pipeline_id=pipeline_id,
            execution_id=execution_id,
            metadata=metadata or {}
        )
        
        self._usage_records.append(record)
        
        # Check budget alerts
        self._check_budget_alerts()
        
        # Periodic cleanup
        if datetime.utcnow() - self._last_cleanup > timedelta(hours=1):
            self._cleanup_old_records()
        
        return cost
    
    def calculate_cost(
        self,
        provider: ProviderType,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> float:
        """Calculate cost based on token usage."""
        provider_key = provider.value
        
        if provider_key not in self._provider_pricing:
            logger.warning(f"No pricing data for provider: {provider_key}")
            return 0.0
        
        pricing = self._provider_pricing[provider_key].get(model)
        if not pricing:
            logger.warning(f"No pricing data for model: {model}")
            return 0.0
        
        # Calculate cost per 1K tokens
        input_cost = (input_tokens / 1000) * pricing.get('input', 0.0)
        output_cost = (output_tokens / 1000) * pricing.get('output', 0.0)
        
        return input_cost + output_cost
    
    def get_usage_metrics(
        self,
        provider: Optional[ProviderType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        pipeline_id: Optional[str] = None
    ) -> UsageMetrics:
        """Get usage metrics for specified criteria."""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Filter records
        filtered_records = []
        for record in self._usage_records:
            if start_date <= record.timestamp <= end_date:
                if provider and record.provider != provider:
                    continue
                if user_id and record.user_id != user_id:
                    continue
                if pipeline_id and record.pipeline_id != pipeline_id:
                    continue
                filtered_records.append(record)
        
        if not filtered_records:
            return UsageMetrics(
                provider=provider or ProviderType.OPENAI,
                period_start=start_date,
                period_end=end_date
            )
        
        # Calculate metrics
        total_requests = len(filtered_records)
        total_tokens = sum(r.tokens_used for r in filtered_records)
        total_cost = sum(r.cost for r in filtered_records)
        
        models_used = defaultdict(int)
        operations = defaultdict(int)
        cost_by_model = defaultdict(float)
        cost_by_operation = defaultdict(float)
        
        for record in filtered_records:
            models_used[record.model] += 1
            operations[record.operation] += 1
            cost_by_model[record.model] += record.cost
            cost_by_operation[record.operation] += record.cost
        
        return UsageMetrics(
            provider=provider or filtered_records[0].provider,
            period_start=start_date,
            period_end=end_date,
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=total_cost,
            average_cost_per_request=total_cost / total_requests if total_requests > 0 else 0.0,
            average_tokens_per_request=total_tokens / total_requests if total_requests > 0 else 0.0,
            models_used=dict(models_used),
            operations=dict(operations),
            cost_by_model=dict(cost_by_model),
            cost_by_operation=dict(cost_by_operation)
        )
    
    def get_daily_costs(self, days: int = 30) -> Dict[str, float]:
        """Get daily cost breakdown for the last N days."""
        end_date = datetime.utcnow().replace(hour=23, minute=59, second=59)
        start_date = end_date - timedelta(days=days)
        
        daily_costs = defaultdict(float)
        
        for record in self._usage_records:
            if start_date <= record.timestamp <= end_date:
                day_key = record.timestamp.strftime('%Y-%m-%d')
                daily_costs[day_key] += record.cost
        
        return dict(daily_costs)
    
    def add_budget_alert(self, alert: BudgetAlert):
        """Add a budget alert."""
        self._budget_alerts.append(alert)
    
    def _check_budget_alerts(self):
        """Check if any budget thresholds are exceeded."""
        current_time = datetime.utcnow()
        
        for alert in self._budget_alerts:
            if not alert.is_active:
                continue
            
            # Calculate period based on threshold type
            if alert.threshold_type == 'daily':
                start_date = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            elif alert.threshold_type == 'weekly':
                days_since_monday = current_time.weekday()
                start_date = (current_time - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif alert.threshold_type == 'monthly':
                start_date = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                continue
            
            # Calculate current spending
            current_spending = sum(
                r.cost for r in self._usage_records
                if start_date <= r.timestamp <= current_time
            )
            
            # Check if alert threshold is exceeded
            alert_threshold = alert.threshold_amount * (alert.alert_percentage / 100)
            
            if current_spending >= alert_threshold:
                # Check if we already sent an alert recently
                if (alert.last_alert_sent is None or 
                    current_time - alert.last_alert_sent > timedelta(hours=1)):
                    
                    self._send_budget_alert(alert, current_spending)
                    alert.last_alert_sent = current_time
    
    def _send_budget_alert(self, alert: BudgetAlert, current_spending: float):
        """Send budget alert (placeholder for notification system)."""
        logger.warning(
            f"Budget alert '{alert.name}': Current spending ${current_spending:.2f} "
            f"exceeds {alert.alert_percentage}% of ${alert.threshold_amount} threshold"
        )
    
    def _cleanup_old_records(self):
        """Remove records older than 90 days."""
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        old_count = len(self._usage_records)
        self._usage_records = [
            r for r in self._usage_records 
            if r.timestamp >= cutoff_date
        ]
        
        removed_count = old_count - len(self._usage_records)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old usage records")
        
        self._last_cleanup = datetime.utcnow()
    
    def export_usage_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Export usage data for analysis."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        exported_data = []
        for record in self._usage_records:
            if start_date <= record.timestamp <= end_date:
                exported_data.append({
                    'timestamp': record.timestamp.isoformat(),
                    'provider': record.provider.value,
                    'model': record.model,
                    'operation': record.operation,
                    'tokens_used': record.tokens_used,
                    'cost': record.cost,
                    'user_id': record.user_id,
                    'pipeline_id': record.pipeline_id,
                    'execution_id': record.execution_id,
                    'metadata': record.metadata
                })
        
        return exported_data
    
    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by cost/usage."""
        user_stats = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'requests': 0})
        
        for record in self._usage_records:
            if record.user_id:
                user_stats[record.user_id]['cost'] += record.cost
                user_stats[record.user_id]['tokens'] += record.tokens_used
                user_stats[record.user_id]['requests'] += 1
        
        # Sort by cost
        sorted_users = sorted(
            user_stats.items(),
            key=lambda x: x[1]['cost'],
            reverse=True
        )
        
        return [
            {'user_id': user_id, **stats}
            for user_id, stats in sorted_users[:limit]
        ]