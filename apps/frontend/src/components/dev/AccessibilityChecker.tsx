import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { AlertTriangle, CheckCircle, XCircle, Eye } from 'lucide-react';

interface AccessibilityIssue {
  id: string;
  impact: 'minor' | 'moderate' | 'serious' | 'critical';
  description: string;
  help: string;
  helpUrl: string;
  nodes: Array<{
    target: string[];
    html: string;
  }>;
}

interface AccessibilityCheckerProps {
  enabled?: boolean;
}

export function AccessibilityChecker({ enabled = false }: AccessibilityCheckerProps) {
  const [issues, setIssues] = useState<AccessibilityIssue[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [lastScan, setLastScan] = useState<Date | null>(null);
  const [showChecker, setShowChecker] = useState(enabled);

  const runAccessibilityScan = async () => {
    if (typeof window === 'undefined' || !window.axe) {
      console.error('axe-core not loaded');
      return;
    }

    setIsScanning(true);
    try {
      const results = await window.axe.run();
      setIssues(results.violations);
      setLastScan(new Date());
    } catch (error) {
      console.error('Accessibility scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    // Load axe-core in development
    if (process.env.NODE_ENV === 'development' && showChecker) {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.0/axe.min.js';
      script.onload = () => {
        console.log('axe-core loaded');
        runAccessibilityScan();
      };
      document.head.appendChild(script);

      return () => {
        document.head.removeChild(script);
      };
    }
  }, [showChecker]);

  if (process.env.NODE_ENV !== 'development' || !showChecker) {
    return null;
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'critical':
        return 'destructive';
      case 'serious':
        return 'destructive';
      case 'moderate':
        return 'warning';
      case 'minor':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'critical':
      case 'serious':
        return <XCircle className="w-4 h-4" />;
      case 'moderate':
        return <AlertTriangle className="w-4 h-4" />;
      case 'minor':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-lg">
      <Card className="shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Accessibility Checker
            </CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowChecker(false)}
            >
              Hide
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Button
                onClick={runAccessibilityScan}
                disabled={isScanning}
                size="sm"
              >
                {isScanning ? 'Scanning...' : 'Run Scan'}
              </Button>
              {lastScan && (
                <span className="text-sm text-muted-foreground">
                  Last scan: {lastScan.toLocaleTimeString()}
                </span>
              )}
            </div>

            {issues.length === 0 && lastScan && (
              <Alert>
                <CheckCircle className="w-4 h-4" />
                <AlertDescription>
                  No accessibility issues found! Great job!
                </AlertDescription>
              </Alert>
            )}

            {issues.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium">
                  Found {issues.length} accessibility issue{issues.length !== 1 ? 's' : ''}
                </div>
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {issues.map((issue) => (
                    <Alert key={issue.id} variant="default" className="p-3">
                      <div className="flex items-start gap-2">
                        {getImpactIcon(issue.impact)}
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <Badge variant={getImpactColor(issue.impact)}>
                              {issue.impact}
                            </Badge>
                            <span className="font-medium text-sm">{issue.id}</span>
                          </div>
                          <p className="text-sm">{issue.description}</p>
                          <p className="text-xs text-muted-foreground">{issue.help}</p>
                          <div className="text-xs">
                            <span className="font-medium">Affected: </span>
                            {issue.nodes.map((node, i) => (
                              <code key={i} className="text-xs bg-muted px-1 rounded">
                                {node.target.join(' ')}
                              </code>
                            ))}
                          </div>
                          <a
                            href={issue.helpUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-primary hover:underline"
                          >
                            Learn more →
                          </a>
                        </div>
                      </div>
                    </Alert>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-2 border-t">
              <div className="space-y-2 text-sm">
                <h4 className="font-medium">Quick Checklist:</h4>
                <div className="space-y-1">
                  <label className="flex items-center gap-2">
                    <Checkbox />
                    <span>All images have alt text</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox />
                    <span>Forms have proper labels</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox />
                    <span>Color contrast meets WCAG AA</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox />
                    <span>Keyboard navigation works</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox />
                    <span>ARIA attributes are correct</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Add to window for development
declare global {
  interface Window {
    axe: any;
  }
}