import React, { useEffect, useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Activity, Zap, HardDrive, Clock, TrendingUp, AlertTriangle } from 'lucide-react';

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  target?: number;
  status: 'good' | 'warning' | 'critical';
}

interface APICallMetric {
  endpoint: string;
  method: string;
  duration: number;
  status: number;
  timestamp: number;
}

export function PerformanceMonitor() {
  const [isVisible, setIsVisible] = useState(false);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [apiCalls, setApiCalls] = useState<APICallMetric[]>([]);
  const [fps, setFps] = useState(60);
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());

  // Monitor FPS
  useEffect(() => {
    let animationId: number;
    
    const measureFPS = () => {
      frameCountRef.current++;
      const currentTime = performance.now();
      
      if (currentTime >= lastTimeRef.current + 1000) {
        setFps(Math.round((frameCountRef.current * 1000) / (currentTime - lastTimeRef.current)));
        frameCountRef.current = 0;
        lastTimeRef.current = currentTime;
      }
      
      animationId = requestAnimationFrame(measureFPS);
    };
    
    if (isVisible) {
      animationId = requestAnimationFrame(measureFPS);
    }
    
    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [isVisible]);

  // Monitor API calls
  useEffect(() => {
    if (!isVisible) return;

    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const startTime = performance.now();
      const [url, options] = args;
      
      try {
        const response = await originalFetch(...args);
        const duration = performance.now() - startTime;
        
        if (typeof url === 'string' && url.includes('/api/')) {
          setApiCalls(prev => [...prev.slice(-19), {
            endpoint: url,
            method: options?.method || 'GET',
            duration,
            status: response.status,
            timestamp: Date.now()
          }]);
        }
        
        return response;
      } catch (error) {
        const duration = performance.now() - startTime;
        
        if (typeof url === 'string' && url.includes('/api/')) {
          setApiCalls(prev => [...prev.slice(-19), {
            endpoint: url,
            method: options?.method || 'GET',
            duration,
            status: 0,
            timestamp: Date.now()
          }]);
        }
        
        throw error;
      }
    };
    
    return () => {
      window.fetch = originalFetch;
    };
  }, [isVisible]);

  // Update performance metrics
  useEffect(() => {
    if (!isVisible) return;

    const updateMetrics = () => {
      const newMetrics: PerformanceMetric[] = [];
      
      // Memory usage
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const usedMB = memory.usedJSHeapSize / 1024 / 1024;
        const limitMB = memory.jsHeapSizeLimit / 1024 / 1024;
        
        newMetrics.push({
          name: 'Memory Usage',
          value: Math.round(usedMB),
          unit: 'MB',
          target: 200,
          status: usedMB > 500 ? 'critical' : usedMB > 200 ? 'warning' : 'good'
        });
        
        newMetrics.push({
          name: 'Memory Limit',
          value: Math.round(limitMB),
          unit: 'MB',
          status: 'good'
        });
      }
      
      // FPS
      newMetrics.push({
        name: 'FPS',
        value: fps,
        unit: 'fps',
        target: 60,
        status: fps < 30 ? 'critical' : fps < 50 ? 'warning' : 'good'
      });
      
      // Average API response time
      if (apiCalls.length > 0) {
        const avgResponseTime = apiCalls.reduce((sum, call) => sum + call.duration, 0) / apiCalls.length;
        newMetrics.push({
          name: 'Avg API Response',
          value: Math.round(avgResponseTime),
          unit: 'ms',
          target: 200,
          status: avgResponseTime > 500 ? 'critical' : avgResponseTime > 200 ? 'warning' : 'good'
        });
      }
      
      // Navigation timing
      if (performance.timing) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        if (loadTime > 0) {
          newMetrics.push({
            name: 'Page Load Time',
            value: loadTime,
            unit: 'ms',
            target: 1000,
            status: loadTime > 3000 ? 'critical' : loadTime > 1000 ? 'warning' : 'good'
          });
        }
      }
      
      setMetrics(newMetrics);
    };
    
    updateMetrics();
    const interval = setInterval(updateMetrics, 1000);
    
    return () => clearInterval(interval);
  }, [isVisible, fps, apiCalls]);

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  if (!isVisible) {
    return (
      <Button
        className="fixed bottom-4 left-4 z-50"
        size="sm"
        variant="outline"
        onClick={() => setIsVisible(true)}
      >
        <Activity className="w-4 h-4 mr-2" />
        Performance
      </Button>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'destructive';
      case 'warning': return 'secondary';
      case 'good': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'critical': return <AlertTriangle className="w-4 h-4" />;
      case 'warning': return <TrendingUp className="w-4 h-4" />;
      case 'good': return <Zap className="w-4 h-4" />;
      default: return null;
    }
  };

  return (
    <div className="fixed bottom-4 left-4 z-50 w-96">
      <Card className="shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Performance Monitor
            </CardTitle>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setIsVisible(false)}
            >
              ×
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3">
              {metrics.map((metric) => (
                <div key={metric.name} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{metric.name}</span>
                    {getStatusIcon(metric.status)}
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold">{metric.value}</span>
                    <span className="text-sm text-muted-foreground">{metric.unit}</span>
                  </div>
                  {metric.target && (
                    <Progress 
                      value={Math.min((metric.value / metric.target) * 100, 100)} 
                      className="h-1"
                    />
                  )}
                  <Badge variant={getStatusColor(metric.status)} className="text-xs">
                    {metric.status}
                  </Badge>
                </div>
              ))}
            </div>

            {/* Recent API Calls */}
            {apiCalls.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Recent API Calls
                </h4>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {apiCalls.slice(-5).reverse().map((call, index) => (
                    <div key={`${call.timestamp}-${index}`} className="text-xs space-y-1 p-2 bg-muted rounded">
                      <div className="flex items-center justify-between">
                        <span className="font-mono truncate flex-1">
                          {call.method} {call.endpoint.replace(/^.*\/api\//, '/api/')}
                        </span>
                        <Badge 
                          variant={call.duration > 200 ? 'destructive' : 'default'} 
                          className="text-xs ml-2"
                        >
                          {Math.round(call.duration)}ms
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">
                          Status: {call.status || 'Failed'}
                        </span>
                        <span className="text-muted-foreground">
                          {new Date(call.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Performance Tips */}
            <div className="pt-2 border-t">
              <h4 className="text-sm font-medium mb-2">Performance Tips</h4>
              <ul className="text-xs space-y-1 text-muted-foreground">
                {fps < 50 && <li>• Low FPS detected. Check for expensive renders.</li>}
                {metrics.find(m => m.name === 'Memory Usage' && m.status !== 'good') && 
                  <li>• High memory usage. Consider cleaning up unused data.</li>}
                {metrics.find(m => m.name === 'Avg API Response' && m.status !== 'good') && 
                  <li>• Slow API responses. Check backend performance.</li>}
                {metrics.every(m => m.status === 'good') && 
                  <li>• All metrics look good! 🚀</li>}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}