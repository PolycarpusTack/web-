import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Zap,
  Clock,
  Cpu,
  Download,
  RefreshCw,
  Activity,
  AlertTriangle
} from 'lucide-react';

interface AnalyticsData {
  time_range: string;
  start_date: string;
  end_date: string;
  overview: {
    total_messages: number;
    total_tokens: number;
    total_cost: number;
    unique_users: number;
    active_models: number;
    avg_tokens_per_message: number;
    avg_cost_per_message: number;
  };
  usage_trends: Array<{
    timestamp: string;
    usage_count: number;
    token_count: number;
    cost: number;
    unique_users: number;
  }>;
  model_metrics: Array<{
    model_id: string;
    model_name: string;
    provider: string;
    total_usage: number;
    unique_users: number;
    total_tokens: number;
    total_cost: number;
    avg_response_time: number;
    error_rate: number;
    last_used: string;
    trend_direction: 'up' | 'down' | 'stable';
    trend_percentage: number;
  }>;
  cost_breakdown: Array<{
    model_id: string;
    model_name: string;
    input_cost: number;
    output_cost: number;
    total_cost: number;
    percentage_of_total: number;
  }>;
  performance_metrics: Array<{
    model_id: string;
    model_name: string;
    avg_response_time: number;
    p95_response_time: number;
    throughput: number;
    error_rate: number;
    availability: number;
  }>;
  top_models: Array<{
    rank: number;
    model_id: string;
    model_name: string;
    provider: string;
    usage_count: number;
    total_tokens: number;
    total_cost: number;
  }>;
  user_analytics: {
    total_active_users: number;
    top_users: Array<{
      user_id: string;
      username: string;
      message_count: number;
      total_tokens: number;
    }>;
  };
  comparison_data?: {
    previous_period: any;
    changes: {
      total_messages: number;
      total_tokens: number;
      total_cost: number;
      unique_users: number;
    };
  };
}

interface ModelAnalyticsDashboardProps {
  className?: string;
}

const TIME_RANGES = [
  { value: 'hour', label: 'Last Hour' },
  { value: 'day', label: 'Last Day' },
  { value: 'week', label: 'Last Week' },
  { value: 'month', label: 'Last Month' },
  { value: 'quarter', label: 'Last Quarter' },
  { value: 'year', label: 'Last Year' },
];

const CHART_COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1',
  '#d084d0', '#ffb347', '#87ceeb', '#dda0dd', '#98fb98'
];

export const ModelAnalyticsDashboard: React.FC<ModelAnalyticsDashboardProps> = ({ className }) => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('day');
  const [realTimeEnabled, setRealTimeEnabled] = useState(false);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [includeComparison, setIncludeComparison] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);
  
  const { toast } = useToast();
  
  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/analytics/models', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          time_range: timeRange,
          model_ids: selectedModels.length > 0 ? selectedModels : undefined,
          include_comparison: includeComparison,
          metrics: ['usage_count', 'token_count', 'cost', 'duration', 'user_count']
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.status}`);
      }
      
      const analyticsData = await response.json();
      setData(analyticsData);
      
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      setError('Failed to load analytics data. Please try again.');
      toast({
        title: "Analytics Error",
        description: "Failed to load analytics data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [timeRange, selectedModels, includeComparison, toast]);
  
  // Load analytics on mount and when filters change
  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);
  
  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchAnalytics]);
  
  // Real-time WebSocket connection
  useEffect(() => {
    if (realTimeEnabled) {
      const ws = new WebSocket('/api/analytics/models/live');
      
      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        if (update.type === 'analytics_update') {
          // Update only overview metrics for real-time
          setData(prev => prev ? {
            ...prev,
            overview: { ...prev.overview, ...update.data.overview }
          } : null);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        toast({
          title: "Real-time Connection Lost",
          description: "Switching to manual refresh mode",
          variant: "destructive",
        });
        setRealTimeEnabled(false);
      };
      
      return () => {
        ws.close();
      };
    }
  }, [realTimeEnabled, toast]);
  
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(value);
  };
  
  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };
  
  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };
  
  const getTrendIcon = (direction: string) => {
    if (direction === 'up') return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (direction === 'down') return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Activity className="h-4 w-4 text-gray-500" />;
  };
  
  const exportData = async (format: 'json' | 'csv') => {
    try {
      const params = new URLSearchParams({
        time_range: timeRange,
        format,
        ...(selectedModels.length > 0 && { model_ids: selectedModels.join(',') })
      });
      
      const response = await fetch(`/api/analytics/models/export?${params}`);
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({
        title: "Export Complete",
        description: `Analytics data exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Failed to export analytics data",
        variant: "destructive",
      });
    }
  };
  
  if (loading && !data) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-32" />
              </CardHeader>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-36" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-80 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }
  
  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  
  if (!data) return null;
  
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Model Analytics</h2>
          <p className="text-muted-foreground">
            Comprehensive insights into model usage and performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIME_RANGES.map(range => (
                <SelectItem key={range.value} value={range.value}>
                  {range.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAnalytics}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportData('json')}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>
      
      {/* Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Switch
                checked={realTimeEnabled}
                onCheckedChange={setRealTimeEnabled}
              />
              <label className="text-sm font-medium">Real-time updates</label>
            </div>
            
            <div className="flex items-center gap-2">
              <Switch
                checked={autoRefresh}
                onCheckedChange={setAutoRefresh}
              />
              <label className="text-sm font-medium">Auto refresh</label>
            </div>
            
            <div className="flex items-center gap-2">
              <Switch
                checked={includeComparison}
                onCheckedChange={setIncludeComparison}
              />
              <label className="text-sm font-medium">Compare with previous period</label>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(data.overview.total_messages)}</div>
            {data.comparison_data && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                {getTrendIcon(data.comparison_data.changes.total_messages >= 0 ? 'up' : 'down')}
                {formatPercentage(data.comparison_data.changes.total_messages)}
                <span>from last period</span>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(data.overview.total_tokens)}</div>
            {data.comparison_data && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                {getTrendIcon(data.comparison_data.changes.total_tokens >= 0 ? 'up' : 'down')}
                {formatPercentage(data.comparison_data.changes.total_tokens)}
                <span>from last period</span>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.overview.total_cost)}</div>
            {data.comparison_data && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                {getTrendIcon(data.comparison_data.changes.total_cost >= 0 ? 'up' : 'down')}
                {formatPercentage(data.comparison_data.changes.total_cost)}
                <span>from last period</span>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(data.overview.unique_users)}</div>
            {data.comparison_data && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                {getTrendIcon(data.comparison_data.changes.unique_users >= 0 ? 'up' : 'down')}
                {formatPercentage(data.comparison_data.changes.unique_users)}
                <span>from last period</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Charts */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">Usage Trends</TabsTrigger>
          <TabsTrigger value="models">Model Performance</TabsTrigger>
          <TabsTrigger value="costs">Cost Analysis</TabsTrigger>
          <TabsTrigger value="users">User Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage Over Time</CardTitle>
              <CardDescription>Message count, tokens, and cost trends</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data.usage_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value, name) => [
                      name === 'cost' ? formatCurrency(Number(value)) : formatNumber(Number(value)),
                      String(name).replace('_', ' ').toUpperCase()
                    ]}
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="usage_count"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="Messages"
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="token_count"
                    stroke="#82ca9d"
                    strokeWidth={2}
                    name="Tokens"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="cost"
                    stroke="#ffc658"
                    strokeWidth={2}
                    name="Cost"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>User Activity</CardTitle>
              <CardDescription>Unique users over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={data.usage_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value) => [formatNumber(Number(value)), 'Unique Users']}
                  />
                  <Area
                    type="monotone"
                    dataKey="unique_users"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Models by Usage</CardTitle>
              <CardDescription>Most frequently used models</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.top_models.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="model_name"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      formatNumber(Number(value)),
                      String(name).replace('_', ' ').toUpperCase()
                    ]}
                  />
                  <Legend />
                  <Bar dataKey="usage_count" fill="#8884d8" name="Usage Count" />
                  <Bar dataKey="total_tokens" fill="#82ca9d" name="Total Tokens" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Model Performance Metrics</CardTitle>
              <CardDescription>Response time vs throughput</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.performance_metrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="model_name" />
                  <YAxis />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white p-3 border rounded shadow">
                            <p className="font-medium">{label}</p>
                            <p>Response Time: {data.avg_response_time.toFixed(2)}s</p>
                            <p>Throughput: {data.throughput.toFixed(1)} req/min</p>
                            <p>Error Rate: {(data.error_rate * 100).toFixed(2)}%</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="avg_response_time" fill="#8884d8" />
                  <Bar dataKey="throughput" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="costs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cost Breakdown by Model</CardTitle>
              <CardDescription>Distribution of costs across models</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.cost_breakdown.slice(0, 8)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="model_name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [formatCurrency(Number(value)), 'Total Cost']}
                  />
                  <Legend />
                  <Bar dataKey="total_cost" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Input vs Output Costs</CardTitle>
              <CardDescription>Breakdown of input and output token costs</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.cost_breakdown.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="model_name"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [formatCurrency(Number(value)), 'Cost']}
                  />
                  <Legend />
                  <Bar dataKey="input_cost" stackId="a" fill="#8884d8" name="Input Cost" />
                  <Bar dataKey="output_cost" stackId="a" fill="#82ca9d" name="Output Cost" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Users by Activity</CardTitle>
              <CardDescription>Most active users in the selected period</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.user_analytics.top_users.map((user, index) => (
                  <div key={user.user_id} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary">#{index + 1}</Badge>
                      <div>
                        <div className="font-medium">{user.username}</div>
                        <div className="text-sm text-muted-foreground">
                          {formatNumber(user.message_count)} messages
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{formatNumber(user.total_tokens)} tokens</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};