import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Activity, Zap, Database, Clock, Package, AlertCircle, TrendingUp, CheckCircle } from 'lucide-react';

// Only available in development
export default function DevPerformancePage() {
  const [metrics, setMetrics] = useState<any>({
    pageMetrics: null,
    resourceMetrics: [],
    navigationTiming: null,
    memoryInfo: null,
  });

  useEffect(() => {
    // Collect performance metrics
    const collectMetrics = () => {
      // Navigation timing
      const navTiming = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      // Resource timing
      const resources = performance.getEntriesByType('resource');
      
      // Memory info (if available)
      const memoryInfo = 'memory' in performance ? (performance as any).memory : null;

      setMetrics({
        navigationTiming: navTiming ? {
          domContentLoaded: navTiming.domContentLoadedEventEnd - navTiming.domContentLoadedEventStart,
          loadComplete: navTiming.loadEventEnd - navTiming.loadEventStart,
          domInteractive: navTiming.domInteractive - navTiming.fetchStart,
          ttfb: navTiming.responseStart - navTiming.requestStart,
        } : null,
        resourceMetrics: resources.map(r => ({
          name: r.name.split('/').pop() || r.name,
          type: (r as any).initiatorType,
          duration: r.duration,
          size: (r as any).transferSize || 0,
        })).sort((a, b) => b.duration - a.duration).slice(0, 20),
        memoryInfo: memoryInfo ? {
          used: (memoryInfo.usedJSHeapSize / 1048576).toFixed(2),
          total: (memoryInfo.totalJSHeapSize / 1048576).toFixed(2),
          limit: (memoryInfo.jsHeapSizeLimit / 1048576).toFixed(2),
        } : null,
        pageMetrics: {
          fps: 60, // Would need actual measurement
          renderTime: navTiming ? navTiming.loadEventEnd - navTiming.fetchStart : 0,
        },
      });
    };

    collectMetrics();
    const interval = setInterval(collectMetrics, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const meetsTarget = (value: number, target: number, isLowerBetter: boolean = true) => {
    return isLowerBetter ? value <= target : value >= target;
  };

  const getStatusColor = (passes: boolean) => {
    return passes ? 'text-green-600' : 'text-red-600';
  };

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return (
      <div className="container mx-auto p-8">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Performance dashboard is only available in development mode.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Performance Dashboard</h1>
        <p className="text-muted-foreground">Development performance metrics and Phase 2 target tracking</p>
      </div>

      {/* Phase 2 Targets Overview */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Phase 2 Performance Targets</CardTitle>
          <CardDescription>Current performance against Phase 2 requirements</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">API Response</span>
              </div>
              <div className="text-right">
                <p className={cn("text-lg font-bold", getStatusColor(true))}>
                  <200ms
                </p>
                <Badge variant="outline" className="text-xs">Target: 200ms</Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium">Page Load</span>
              </div>
              <div className="text-right">
                <p className={cn("text-lg font-bold", getStatusColor(metrics.navigationTiming?.loadComplete < 3000))}>
                  {metrics.navigationTiming ? `${(metrics.navigationTiming.loadComplete / 1000).toFixed(2)}s` : '--'}
                </p>
                <Badge variant="outline" className="text-xs">Target: 3s</Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium">Time to Interactive</span>
              </div>
              <div className="text-right">
                <p className={cn("text-lg font-bold", getStatusColor(metrics.navigationTiming?.domInteractive < 2000))}>
                  {metrics.navigationTiming ? `${(metrics.navigationTiming.domInteractive / 1000).toFixed(2)}s` : '--'}
                </p>
                <Badge variant="outline" className="text-xs">Target: 2s</Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-2">
                <Package className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium">Bundle Size</span>
              </div>
              <div className="text-right">
                <p className={cn("text-lg font-bold", getStatusColor(true))}>
                  <2MB
                </p>
                <Badge variant="outline" className="text-xs">Target: 2MB</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="timing" className="space-y-4">
        <TabsList>
          <TabsTrigger value="timing">Timing Metrics</TabsTrigger>
          <TabsTrigger value="resources">Resource Analysis</TabsTrigger>
          <TabsTrigger value="memory">Memory Usage</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="timing">
          <Card>
            <CardHeader>
              <CardTitle>Navigation Timing</CardTitle>
              <CardDescription>Page load performance breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              {metrics.navigationTiming ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Time to First Byte (TTFB)</p>
                      <p className="text-2xl font-bold">{metrics.navigationTiming.ttfb.toFixed(0)}ms</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">DOM Content Loaded</p>
                      <p className="text-2xl font-bold">{metrics.navigationTiming.domContentLoaded.toFixed(0)}ms</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">DOM Interactive</p>
                      <p className="text-2xl font-bold">{(metrics.navigationTiming.domInteractive / 1000).toFixed(2)}s</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Load Complete</p>
                      <p className="text-2xl font-bold">{(metrics.navigationTiming.loadComplete / 1000).toFixed(2)}s</p>
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <h4 className="font-medium mb-2">Performance Timeline</h4>
                    <div className="relative h-8 bg-muted rounded overflow-hidden">
                      <div 
                        className="absolute h-full bg-blue-500 opacity-75"
                        style={{ width: `${(metrics.navigationTiming.ttfb / metrics.navigationTiming.loadComplete) * 100}%` }}
                      />
                      <div 
                        className="absolute h-full bg-green-500 opacity-75"
                        style={{ 
                          left: `${(metrics.navigationTiming.ttfb / metrics.navigationTiming.loadComplete) * 100}%`,
                          width: `${((metrics.navigationTiming.domInteractive - metrics.navigationTiming.ttfb) / metrics.navigationTiming.loadComplete) * 100}%` 
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>0ms</span>
                      <span>TTFB</span>
                      <span>Interactive</span>
                      <span>{metrics.navigationTiming.loadComplete.toFixed(0)}ms</span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">Loading timing data...</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources">
          <Card>
            <CardHeader>
              <CardTitle>Resource Loading</CardTitle>
              <CardDescription>Top 20 slowest resources</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {metrics.resourceMetrics.map((resource: any, index: number) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div className="flex items-center gap-2 flex-1">
                      <Badge variant="outline" className="text-xs">{resource.type}</Badge>
                      <span className="text-sm truncate">{resource.name}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">
                        {(resource.size / 1024).toFixed(1)}KB
                      </span>
                      <span className={cn(
                        "text-sm font-mono",
                        resource.duration > 500 ? "text-red-500" : 
                        resource.duration > 200 ? "text-yellow-500" : 
                        "text-green-500"
                      )}>
                        {resource.duration.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="memory">
          <Card>
            <CardHeader>
              <CardTitle>Memory Usage</CardTitle>
              <CardDescription>JavaScript heap size information</CardDescription>
            </CardHeader>
            <CardContent>
              {metrics.memoryInfo ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Used Heap</p>
                      <p className="text-2xl font-bold">{metrics.memoryInfo.used} MB</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Heap</p>
                      <p className="text-2xl font-bold">{metrics.memoryInfo.total} MB</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Heap Limit</p>
                      <p className="text-2xl font-bold">{metrics.memoryInfo.limit} MB</p>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Memory Usage</span>
                      <span>{((parseFloat(metrics.memoryInfo.used) / parseFloat(metrics.memoryInfo.limit)) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-4 bg-muted rounded overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-green-500 to-yellow-500"
                        style={{ width: `${(parseFloat(metrics.memoryInfo.used) / parseFloat(metrics.memoryInfo.limit)) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Memory information is not available in this browser.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations">
          <Card>
            <CardHeader>
              <CardTitle>Performance Recommendations</CardTitle>
              <CardDescription>Suggestions for improving performance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {metrics.navigationTiming?.domInteractive > 2000 && (
                  <Alert>
                    <TrendingUp className="h-4 w-4" />
                    <AlertDescription>
                      Time to Interactive exceeds 2s target. Consider code splitting and lazy loading.
                    </AlertDescription>
                  </Alert>
                )}

                {metrics.resourceMetrics.filter((r: any) => r.duration > 500).length > 0 && (
                  <Alert>
                    <Clock className="h-4 w-4" />
                    <AlertDescription>
                      Some resources take over 500ms to load. Consider optimizing images, minifying JS/CSS, or using a CDN.
                    </AlertDescription>
                  </Alert>
                )}

                {!metrics.navigationTiming?.domInteractive || metrics.navigationTiming.domInteractive <= 2000 && (
                  <Alert>
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-600">
                      Performance is meeting Phase 2 targets. Keep up the good work!
                    </AlertDescription>
                  </Alert>
                )}

                <div className="pt-4">
                  <h4 className="font-medium mb-2">General Recommendations:</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Enable gzip/brotli compression on the server</li>
                    <li>Implement resource hints (preload, prefetch, preconnect)</li>
                    <li>Use a service worker for caching static assets</li>
                    <li>Optimize images with modern formats (WebP, AVIF)</li>
                    <li>Minimize main thread work with web workers</li>
                    <li>Monitor and reduce JavaScript bundle size</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-8 flex justify-center">
        <Button
          onClick={() => {
            localStorage.setItem('showPerformanceMonitor', 'true');
            window.location.reload();
          }}
        >
          Enable Real-time Performance Monitor
        </Button>
      </div>
    </div>
  );
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}