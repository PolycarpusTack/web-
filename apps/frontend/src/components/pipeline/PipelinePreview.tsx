import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  Play, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  ChevronRight,
  Code,
  Bot,
  Globe,
  GitBranch,
  Eye,
  Loader2
} from 'lucide-react';

import { 
  PipelineDefinition, 
  PipelineStep, 
  StepType,
  PipelineExecutionOptions 
} from '@/types/pipeline';

interface PipelinePreviewProps {
  pipeline: PipelineDefinition;
  isOpen: boolean;
  onClose: () => void;
  onExecute: (options: PipelineExecutionOptions) => void;
}

interface PreviewData {
  step: PipelineStep;
  estimatedTime: number;
  estimatedCost: number;
  warnings: string[];
  dependencies: string[];
}

export function PipelinePreview({ 
  pipeline, 
  isOpen, 
  onClose, 
  onExecute 
}: PipelinePreviewProps) {
  const [initialVariables, setInitialVariables] = useState<string>('{}');
  const [variableError, setVariableError] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [previewData, setPreviewData] = useState<PreviewData[]>([]);

  const getStepIcon = (type: StepType) => {
    switch (type) {
      case StepType.LLM: return <Bot className="w-4 h-4" />;
      case StepType.CODE: return <Code className="w-4 h-4" />;
      case StepType.API: return <Globe className="w-4 h-4" />;
      case StepType.CONDITION: return <GitBranch className="w-4 h-4" />;
      default: return null;
    }
  };

  const analyzeSteps = () => {
    setIsAnalyzing(true);
    
    // Simulate analysis - in real implementation, this would call an API
    setTimeout(() => {
      const analyzed: PreviewData[] = pipeline.steps.map(step => {
        const warnings: string[] = [];
        const dependencies: string[] = [];
        
        // Check for missing configurations
        if (step.type === StepType.LLM && !step.config.model_id) {
          warnings.push('No model selected');
        }
        if (step.type === StepType.API && !step.config.url) {
          warnings.push('No API URL configured');
        }
        
        // Find dependencies
        pipeline.connections.forEach(conn => {
          if (conn.target_step_id === step.id) {
            const sourceStep = pipeline.steps.find(s => s.id === conn.source_step_id);
            if (sourceStep) {
              dependencies.push(sourceStep.name);
            }
          }
        });
        
        // Estimate time and cost
        let estimatedTime = 1000; // 1 second base
        let estimatedCost = 0;
        
        if (step.type === StepType.LLM) {
          estimatedTime = 3000; // 3 seconds for LLM
          estimatedCost = 0.002; // Example cost
        } else if (step.type === StepType.API) {
          estimatedTime = 2000; // 2 seconds for API
        } else if (step.type === StepType.CODE) {
          estimatedTime = 500; // 0.5 seconds for code
        }
        
        return {
          step,
          estimatedTime,
          estimatedCost,
          warnings,
          dependencies
        };
      });
      
      setPreviewData(analyzed);
      setIsAnalyzing(false);
    }, 1000);
  };

  React.useEffect(() => {
    if (isOpen) {
      analyzeSteps();
    }
  }, [isOpen]);

  const validateVariables = () => {
    try {
      JSON.parse(initialVariables);
      setVariableError('');
      return true;
    } catch (e) {
      setVariableError('Invalid JSON format');
      return false;
    }
  };

  const handleDryRun = () => {
    if (!validateVariables()) return;
    
    const variables = JSON.parse(initialVariables);
    onExecute({
      initial_variables: variables,
      dry_run: true,
      debug_mode: true
    });
  };

  const handleExecute = () => {
    if (!validateVariables()) return;
    
    const variables = JSON.parse(initialVariables);
    onExecute({
      initial_variables: variables,
      dry_run: false,
      debug_mode: false
    });
  };

  const totalEstimatedTime = previewData.reduce((sum, data) => sum + data.estimatedTime, 0);
  const totalEstimatedCost = previewData.reduce((sum, data) => sum + data.estimatedCost, 0);
  const totalWarnings = previewData.reduce((sum, data) => sum + data.warnings.length, 0);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Pipeline Preview: {pipeline.name}</DialogTitle>
          <DialogDescription>
            Review your pipeline configuration and test with sample data before execution
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="flow" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="flow">Flow Analysis</TabsTrigger>
            <TabsTrigger value="variables">Variables</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
          </TabsList>

          <TabsContent value="flow" className="space-y-4">
            <ScrollArea className="h-[400px] pr-4">
              {isAnalyzing ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin mr-2" />
                  <span>Analyzing pipeline...</span>
                </div>
              ) : (
                <div className="space-y-3">
                  {previewData.map((data, index) => (
                    <Card key={data.step.id} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {getStepIcon(data.step.type)}
                            <CardTitle className="text-base">
                              Step {index + 1}: {data.step.name}
                            </CardTitle>
                          </div>
                          <Badge variant="outline">{data.step.type}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {data.dependencies.length > 0 && (
                          <div className="text-sm">
                            <span className="text-muted-foreground">Dependencies: </span>
                            {data.dependencies.join(', ')}
                          </div>
                        )}
                        
                        <div className="flex gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Est. Time: </span>
                            <span>{(data.estimatedTime / 1000).toFixed(1)}s</span>
                          </div>
                          {data.estimatedCost > 0 && (
                            <div>
                              <span className="text-muted-foreground">Est. Cost: </span>
                              <span>${data.estimatedCost.toFixed(4)}</span>
                            </div>
                          )}
                        </div>
                        
                        {data.warnings.length > 0 && (
                          <Alert className="py-2">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription className="text-sm">
                              {data.warnings.join(', ')}
                            </AlertDescription>
                          </Alert>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="variables" className="space-y-4">
            <div className="space-y-2">
              <Label>Initial Variables (JSON)</Label>
              <Textarea
                className="font-mono text-sm"
                rows={10}
                value={initialVariables}
                onChange={(e) => {
                  setInitialVariables(e.target.value);
                  setVariableError('');
                }}
                placeholder='{"input": "Your input data here"}'
              />
              {variableError && (
                <Alert variant="destructive" className="py-2">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{variableError}</AlertDescription>
                </Alert>
              )}
            </div>
            
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Variables can be referenced in your pipeline steps using {`{{variable_name}}`} syntax
              </AlertDescription>
            </Alert>
          </TabsContent>

          <TabsContent value="summary" className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Total Steps</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{pipeline.steps.length}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Est. Duration</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {(totalEstimatedTime / 1000).toFixed(1)}s
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Est. Cost</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${totalEstimatedCost.toFixed(4)}
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {totalWarnings > 0 && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  {totalWarnings} warning{totalWarnings !== 1 ? 's' : ''} found. 
                  Please review the Flow Analysis tab.
                </AlertDescription>
              </Alert>
            )}
            
            {totalWarnings === 0 && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  Pipeline configuration looks good! Ready to execute.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            variant="secondary"
            onClick={handleDryRun}
            disabled={isAnalyzing}
          >
            <Eye className="w-4 h-4 mr-2" />
            Dry Run
          </Button>
          <Button 
            onClick={handleExecute}
            disabled={isAnalyzing || totalWarnings > 0}
          >
            <Play className="w-4 h-4 mr-2" />
            Execute Pipeline
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}