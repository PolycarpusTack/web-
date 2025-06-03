"""
Model Analytics API

This module provides comprehensive analytics for AI model usage including
real-time metrics, usage trends, cost analysis, and performance data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from db.database import get_db
from db.models import Model, Conversation, Message, User
from auth.jwt import get_current_user


class TimeRange(str, Enum):
    HOUR = "hour"
    DAY = "day" 
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


class MetricType(str, Enum):
    USAGE_COUNT = "usage_count"
    TOKEN_COUNT = "token_count"
    COST = "cost"
    DURATION = "duration"
    USER_COUNT = "user_count"
    ERROR_RATE = "error_rate"


@dataclass
class TimeSeriesPoint:
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = None


class AnalyticsRequest(BaseModel):
    time_range: TimeRange = Field(TimeRange.DAY, description="Time range for analytics")
    start_date: Optional[datetime] = Field(None, description="Start date for custom range")
    end_date: Optional[datetime] = Field(None, description="End date for custom range")
    model_ids: Optional[List[str]] = Field(None, description="Filter by specific models")
    user_ids: Optional[List[str]] = Field(None, description="Filter by specific users")
    metrics: List[MetricType] = Field([MetricType.USAGE_COUNT], description="Metrics to include")
    group_by: Optional[str] = Field(None, description="Group results by field")
    include_comparison: bool = Field(False, description="Include comparison with previous period")


class ModelUsageMetrics(BaseModel):
    model_id: str
    model_name: str
    provider: str
    total_usage: int
    unique_users: int
    total_tokens: int
    total_cost: float
    avg_response_time: float
    error_rate: float
    last_used: Optional[datetime]
    trend_direction: str  # "up", "down", "stable"
    trend_percentage: float


class UsageTrend(BaseModel):
    timestamp: datetime
    usage_count: int
    token_count: int
    cost: float
    unique_users: int


class CostBreakdown(BaseModel):
    model_id: str
    model_name: str
    input_cost: float
    output_cost: float
    total_cost: float
    percentage_of_total: float


class PerformanceMetric(BaseModel):
    model_id: str
    model_name: str
    avg_response_time: float
    p95_response_time: float
    throughput: float  # requests per minute
    error_rate: float
    availability: float


class AnalyticsResponse(BaseModel):
    time_range: TimeRange
    start_date: datetime
    end_date: datetime
    overview: Dict[str, Any]
    usage_trends: List[UsageTrend]
    model_metrics: List[ModelUsageMetrics]
    cost_breakdown: List[CostBreakdown]
    performance_metrics: List[PerformanceMetric]
    top_models: List[Dict[str, Any]]
    user_analytics: Dict[str, Any]
    comparison_data: Optional[Dict[str, Any]] = None


class ModelAnalyticsEngine:
    """Analytics engine for model usage and performance data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_analytics(self, request: AnalyticsRequest) -> AnalyticsResponse:
        """Get comprehensive analytics data."""
        start_date, end_date = self._calculate_date_range(request)
        
        # Run analytics queries in parallel
        overview_task = self._get_overview_metrics(start_date, end_date, request.model_ids)
        usage_trends_task = self._get_usage_trends(start_date, end_date, request.model_ids)
        model_metrics_task = self._get_model_metrics(start_date, end_date, request.model_ids)
        cost_breakdown_task = self._get_cost_breakdown(start_date, end_date, request.model_ids)
        performance_task = self._get_performance_metrics(start_date, end_date, request.model_ids)
        top_models_task = self._get_top_models(start_date, end_date, request.model_ids)
        user_analytics_task = self._get_user_analytics(start_date, end_date, request.model_ids)
        
        results = await asyncio.gather(
            overview_task,
            usage_trends_task, 
            model_metrics_task,
            cost_breakdown_task,
            performance_task,
            top_models_task,
            user_analytics_task
        )
        
        overview, usage_trends, model_metrics, cost_breakdown, performance_metrics, top_models, user_analytics = results
        
        # Get comparison data if requested
        comparison_data = None
        if request.include_comparison:
            comparison_data = await self._get_comparison_data(start_date, end_date, request)
        
        return AnalyticsResponse(
            time_range=request.time_range,
            start_date=start_date,
            end_date=end_date,
            overview=overview,
            usage_trends=usage_trends,
            model_metrics=model_metrics,
            cost_breakdown=cost_breakdown,
            performance_metrics=performance_metrics,
            top_models=top_models,
            user_analytics=user_analytics,
            comparison_data=comparison_data
        )
    
    def _calculate_date_range(self, request: AnalyticsRequest) -> tuple[datetime, datetime]:
        """Calculate start and end dates based on time range."""
        now = datetime.utcnow()
        
        if request.time_range == TimeRange.CUSTOM:
            if not request.start_date or not request.end_date:
                raise HTTPException(400, "start_date and end_date required for custom range")
            return request.start_date, request.end_date
        
        if request.time_range == TimeRange.HOUR:
            start_date = now - timedelta(hours=1)
        elif request.time_range == TimeRange.DAY:
            start_date = now - timedelta(days=1)
        elif request.time_range == TimeRange.WEEK:
            start_date = now - timedelta(weeks=1)
        elif request.time_range == TimeRange.MONTH:
            start_date = now - timedelta(days=30)
        elif request.time_range == TimeRange.QUARTER:
            start_date = now - timedelta(days=90)
        elif request.time_range == TimeRange.YEAR:
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=1)
        
        return start_date, now
    
    async def _get_overview_metrics(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> Dict[str, Any]:
        """Get high-level overview metrics."""
        # Base query for messages in date range
        base_query = select(Message).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )
        
        if model_ids:
            # Join with conversations to filter by model
            base_query = base_query.join(Conversation).where(Conversation.model_id.in_(model_ids))
        
        # Total messages
        total_messages_result = await self.db.execute(
            select(func.count(Message.id)).select_from(base_query.subquery())
        )
        total_messages = total_messages_result.scalar() or 0
        
        # Total tokens
        total_tokens_result = await self.db.execute(
            select(func.sum(Message.tokens)).select_from(base_query.subquery())
        )
        total_tokens = total_tokens_result.scalar() or 0
        
        # Total cost
        total_cost_result = await self.db.execute(
            select(func.sum(Message.cost)).select_from(base_query.subquery())
        )
        total_cost = total_cost_result.scalar() or 0.0
        
        # Unique users
        unique_users_result = await self.db.execute(
            select(func.count(func.distinct(Message.user_id))).select_from(base_query.subquery())
        )
        unique_users = unique_users_result.scalar() or 0
        
        # Active models
        active_models_query = select(func.count(func.distinct(Conversation.model_id))).select_from(
            Message.join(Conversation).where(
                and_(
                    Message.created_at >= start_date,
                    Message.created_at <= end_date
                )
            )
        )
        if model_ids:
            active_models_query = active_models_query.where(Conversation.model_id.in_(model_ids))
        
        active_models_result = await self.db.execute(active_models_query)
        active_models = active_models_result.scalar() or 0
        
        return {
            "total_messages": total_messages,
            "total_tokens": int(total_tokens),
            "total_cost": float(total_cost),
            "unique_users": unique_users,
            "active_models": active_models,
            "avg_tokens_per_message": int(total_tokens / total_messages) if total_messages > 0 else 0,
            "avg_cost_per_message": float(total_cost / total_messages) if total_messages > 0 else 0.0,
        }
    
    async def _get_usage_trends(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> List[UsageTrend]:
        """Get usage trends over time."""
        # Group by hour for recent data, by day for longer periods
        time_diff = end_date - start_date
        if time_diff <= timedelta(days=2):
            date_trunc = "hour"
            interval = timedelta(hours=1)
        elif time_diff <= timedelta(days=31):
            date_trunc = "day"
            interval = timedelta(days=1)
        else:
            date_trunc = "week"
            interval = timedelta(weeks=1)
        
        # Build query with date truncation
        # Note: This uses PostgreSQL syntax - for SQLite, we'd need a different approach
        query = select(
            func.date_trunc(date_trunc, Message.created_at).label('period'),
            func.count(Message.id).label('usage_count'),
            func.sum(Message.tokens).label('token_count'),
            func.sum(Message.cost).label('cost'),
            func.count(func.distinct(Message.user_id)).label('unique_users')
        ).select_from(Message)
        
        if model_ids:
            query = query.join(Conversation).where(Conversation.model_id.in_(model_ids))
        
        query = query.where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).group_by(func.date_trunc(date_trunc, Message.created_at)).order_by('period')
        
        try:
            result = await self.db.execute(query)
            trends = []
            
            for row in result:
                trends.append(UsageTrend(
                    timestamp=row.period,
                    usage_count=row.usage_count or 0,
                    token_count=row.token_count or 0,
                    cost=row.cost or 0.0,
                    unique_users=row.unique_users or 0
                ))
            
            return trends
        except Exception:
            # Fallback for SQLite or other databases
            return await self._get_usage_trends_fallback(start_date, end_date, model_ids)
    
    async def _get_usage_trends_fallback(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> List[UsageTrend]:
        """Fallback method for databases that don't support date_trunc."""
        # Simple implementation: get data for each day
        trends = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date < end_date:
            next_date = current_date + timedelta(days=1)
            
            query = select(
                func.count(Message.id).label('usage_count'),
                func.sum(Message.tokens).label('token_count'),
                func.sum(Message.cost).label('cost'),
                func.count(func.distinct(Message.user_id)).label('unique_users')
            ).where(
                and_(
                    Message.created_at >= current_date,
                    Message.created_at < next_date
                )
            )
            
            if model_ids:
                query = query.select_from(Message.join(Conversation)).where(Conversation.model_id.in_(model_ids))
            
            result = await self.db.execute(query)
            row = result.first()
            
            if row:
                trends.append(UsageTrend(
                    timestamp=current_date,
                    usage_count=row.usage_count or 0,
                    token_count=row.token_count or 0,
                    cost=row.cost or 0.0,
                    unique_users=row.unique_users or 0
                ))
            
            current_date = next_date
        
        return trends
    
    async def _get_model_metrics(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> List[ModelUsageMetrics]:
        """Get detailed metrics for each model."""
        query = select(
            Model.id,
            Model.name,
            Model.provider,
            func.count(Message.id).label('total_usage'),
            func.count(func.distinct(Message.user_id)).label('unique_users'),
            func.sum(Message.tokens).label('total_tokens'),
            func.sum(Message.cost).label('total_cost'),
            func.max(Message.created_at).label('last_used')
        ).select_from(
            Model.join(Conversation).join(Message)
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).group_by(Model.id, Model.name, Model.provider)
        
        if model_ids:
            query = query.where(Model.id.in_(model_ids))
        
        result = await self.db.execute(query)
        metrics = []
        
        for row in result:
            # Calculate trend (simplified - would need historical data for real trend)
            trend_direction = "stable"
            trend_percentage = 0.0
            
            metrics.append(ModelUsageMetrics(
                model_id=row.id,
                model_name=row.name,
                provider=row.provider,
                total_usage=row.total_usage or 0,
                unique_users=row.unique_users or 0,
                total_tokens=row.total_tokens or 0,
                total_cost=row.total_cost or 0.0,
                avg_response_time=1.5,  # Mock data - would need actual timing
                error_rate=0.02,  # Mock data
                last_used=row.last_used,
                trend_direction=trend_direction,
                trend_percentage=trend_percentage
            ))
        
        return metrics
    
    async def _get_cost_breakdown(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> List[CostBreakdown]:
        """Get cost breakdown by model."""
        query = select(
            Model.id,
            Model.name,
            func.sum(Message.cost).label('total_cost')
        ).select_from(
            Model.join(Conversation).join(Message)
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).group_by(Model.id, Model.name)
        
        if model_ids:
            query = query.where(Model.id.in_(model_ids))
        
        result = await self.db.execute(query)
        
        # Calculate total cost for percentage
        total_cost = sum(row.total_cost or 0.0 for row in result)
        
        # Re-execute query to get results again
        result = await self.db.execute(query)
        breakdown = []
        
        for row in result:
            cost = row.total_cost or 0.0
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0.0
            
            breakdown.append(CostBreakdown(
                model_id=row.id,
                model_name=row.name,
                input_cost=cost * 0.6,  # Mock split
                output_cost=cost * 0.4,  # Mock split
                total_cost=cost,
                percentage_of_total=percentage
            ))
        
        return sorted(breakdown, key=lambda x: x.total_cost, reverse=True)
    
    async def _get_performance_metrics(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> List[PerformanceMetric]:
        """Get performance metrics for models."""
        # Mock performance data - in a real system, this would come from actual metrics
        query = select(
            Model.id,
            Model.name,
            func.count(Message.id).label('total_requests')
        ).select_from(
            Model.join(Conversation).join(Message)
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).group_by(Model.id, Model.name)
        
        if model_ids:
            query = query.where(Model.id.in_(model_ids))
        
        result = await self.db.execute(query)
        metrics = []
        
        for row in result:
            # Mock performance metrics
            time_diff = (end_date - start_date).total_seconds() / 60  # minutes
            throughput = row.total_requests / time_diff if time_diff > 0 else 0
            
            metrics.append(PerformanceMetric(
                model_id=row.id,
                model_name=row.name,
                avg_response_time=1.2 + (hash(row.id) % 100) / 100,  # Mock data
                p95_response_time=2.1 + (hash(row.id) % 200) / 100,  # Mock data
                throughput=throughput,
                error_rate=0.01 + (hash(row.id) % 5) / 100,  # Mock data
                availability=99.5 + (hash(row.id) % 5) / 10  # Mock data
            ))
        
        return metrics
    
    async def _get_top_models(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Get top models by usage."""
        query = select(
            Model.id,
            Model.name,
            Model.provider,
            func.count(Message.id).label('usage_count'),
            func.sum(Message.tokens).label('total_tokens'),
            func.sum(Message.cost).label('total_cost')
        ).select_from(
            Model.join(Conversation).join(Message)
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).group_by(Model.id, Model.name, Model.provider).order_by(desc('usage_count')).limit(10)
        
        if model_ids:
            query = query.where(Model.id.in_(model_ids))
        
        result = await self.db.execute(query)
        top_models = []
        
        for i, row in enumerate(result):
            top_models.append({
                "rank": i + 1,
                "model_id": row.id,
                "model_name": row.name,
                "provider": row.provider,
                "usage_count": row.usage_count or 0,
                "total_tokens": row.total_tokens or 0,
                "total_cost": row.total_cost or 0.0
            })
        
        return top_models
    
    async def _get_user_analytics(self, start_date: datetime, end_date: datetime, model_ids: Optional[List[str]]) -> Dict[str, Any]:
        """Get user analytics."""
        # Total active users
        query = select(func.count(func.distinct(Message.user_id))).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )
        
        if model_ids:
            query = query.select_from(Message.join(Conversation)).where(Conversation.model_id.in_(model_ids))
        
        total_users_result = await self.db.execute(query)
        total_users = total_users_result.scalar() or 0
        
        # Top users by usage
        top_users_query = select(
            User.id,
            User.username,
            func.count(Message.id).label('message_count'),
            func.sum(Message.tokens).label('total_tokens')
        ).select_from(
            User.join(Message)
        ).where(
            and_(
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).group_by(User.id, User.username).order_by(desc('message_count')).limit(5)
        
        if model_ids:
            top_users_query = top_users_query.join(Conversation).where(Conversation.model_id.in_(model_ids))
        
        top_users_result = await self.db.execute(top_users_query)
        top_users = []
        
        for row in top_users_result:
            top_users.append({
                "user_id": row.id,
                "username": row.username,
                "message_count": row.message_count or 0,
                "total_tokens": row.total_tokens or 0
            })
        
        return {
            "total_active_users": total_users,
            "top_users": top_users
        }
    
    async def _get_comparison_data(self, start_date: datetime, end_date: datetime, request: AnalyticsRequest) -> Dict[str, Any]:
        """Get comparison data for previous period."""
        # Calculate previous period
        period_duration = end_date - start_date
        prev_start = start_date - period_duration
        prev_end = start_date
        
        # Get metrics for previous period
        prev_overview = await self._get_overview_metrics(prev_start, prev_end, request.model_ids)
        curr_overview = await self._get_overview_metrics(start_date, end_date, request.model_ids)
        
        # Calculate percentage changes
        def calc_change(current: float, previous: float) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100
        
        return {
            "previous_period": {
                "start_date": prev_start,
                "end_date": prev_end,
                "metrics": prev_overview
            },
            "changes": {
                "total_messages": calc_change(curr_overview["total_messages"], prev_overview["total_messages"]),
                "total_tokens": calc_change(curr_overview["total_tokens"], prev_overview["total_tokens"]),
                "total_cost": calc_change(curr_overview["total_cost"], prev_overview["total_cost"]),
                "unique_users": calc_change(curr_overview["unique_users"], prev_overview["unique_users"])
            }
        }


# WebSocket manager for real-time updates
class AnalyticsWebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast_update(self, data: Dict[str, Any]):
        for connection in self.active_connections[:]:  # Copy list to avoid modification during iteration
            try:
                await connection.send_json(data)
            except WebSocketDisconnect:
                self.active_connections.remove(connection)
            except Exception:
                self.active_connections.remove(connection)


# Global WebSocket manager
ws_manager = AnalyticsWebSocketManager()


# Router
router = APIRouter(prefix="/api/analytics", tags=["Model Analytics"])


@router.post("/models", response_model=AnalyticsResponse)
async def get_model_analytics(
    request: AnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get comprehensive model analytics with usage trends, cost breakdown,
    and performance metrics.
    """
    analytics_engine = ModelAnalyticsEngine(db)
    return await analytics_engine.get_analytics(request)


@router.get("/models/real-time")
async def get_real_time_metrics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get real-time metrics for dashboard display.
    """
    # Get last hour's data
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    analytics_engine = ModelAnalyticsEngine(db)
    request = AnalyticsRequest(
        time_range=TimeRange.HOUR,
        start_date=start_time,
        end_date=end_time
    )
    
    analytics = await analytics_engine.get_analytics(request)
    
    return {
        "timestamp": end_time.isoformat(),
        "overview": analytics.overview,
        "active_models": len(analytics.model_metrics),
        "current_usage": analytics.overview["total_messages"],
        "current_cost": analytics.overview["total_cost"]
    }


@router.websocket("/models/live")
async def analytics_websocket(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    WebSocket endpoint for real-time analytics updates.
    """
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Wait for client message or timeout
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send periodic update
                real_time_data = await get_real_time_metrics(db)
                await websocket.send_json({
                    "type": "analytics_update",
                    "data": real_time_data
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@router.get("/models/export")
async def export_analytics(
    time_range: TimeRange = Query(TimeRange.DAY),
    format: str = Query("json", regex="^(json|csv|xlsx)$"),
    model_ids: Optional[str] = Query(None, description="Comma-separated model IDs"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Export analytics data in various formats.
    """
    model_ids_list = model_ids.split(",") if model_ids else None
    
    analytics_engine = ModelAnalyticsEngine(db)
    request = AnalyticsRequest(
        time_range=time_range,
        model_ids=model_ids_list
    )
    
    analytics = await analytics_engine.get_analytics(request)
    
    if format == "json":
        return analytics.dict()
    elif format == "csv":
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write model metrics as CSV
        writer.writerow(["Model ID", "Model Name", "Provider", "Usage", "Tokens", "Cost"])
        for metric in analytics.model_metrics:
            writer.writerow([
                metric.model_id,
                metric.model_name,
                metric.provider,
                metric.total_usage,
                metric.total_tokens,
                metric.total_cost
            ])
        
        return {"csv_data": output.getvalue()}
    
    return {"error": "Unsupported format"}