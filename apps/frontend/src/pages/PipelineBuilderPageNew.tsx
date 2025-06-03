import React, { useState, useCallback, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { 
  Save, 
  Play, 
  Settings, 
  FileText, 
  Download, 
  Upload, 
  AlertCircle,
  CheckCircle,
  Clock,
  DollarSign
} from 'lucide-react';

import PipelineBuilder from '@/components/pipeline/PipelineBuilder';
import { usePipelineExecution } from '@/hooks/usePipelineExecution';
import { PipelineDefinition, ValidationResult, ExecutionStatus } from '@/types/pipeline';

export const PipelineBuilderPageNew: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Pipeline state
  const [pipeline, setPipeline] = useState<PipelineDefinition>({
    id: `pipeline_${Date.now()}`,
    name: 'Untitled Pipeline',
    description: '',
    steps: [],
    connections: [],
    variables: {},
    settings: {},
    version: '1.0'
  });

  // UI state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Pipeline execution
  const {
    isExecuting,
    currentExecution,
    stepExecutions,
    error: executionError,
    executeAsync,
    cancelExecution,
    validatePipeline,
    progress,
    totalCost,
    totalTokens,
    executionTime
  } = usePipelineExecution({
    onExecutionComplete: (execution) => {
      console.log('Pipeline execution completed:', execution);
    },
    onExecutionError: (error) => {
      console.error('Pipeline execution error:', error);
    },
    onStepComplete: (stepExecution) => {
      console.log('Step completed:', stepExecution);
    }
  });

  // Load pipeline from URL params or localStorage
  useEffect(() => {
    const pipelineId = searchParams.get('id');
    if (pipelineId) {
      // Load pipeline from API or localStorage
      const savedPipeline = localStorage.getItem(`pipeline_${pipelineId}`);
      if (savedPipeline) {
        try {
          setPipeline(JSON.parse(savedPipeline));
        } catch (error) {
          console.error('Failed to load pipeline:', error);
        }
      }
    }
  }, [searchParams]);

  // Handle pipeline changes
  const handlePipelineChange = useCallback((newPipeline: PipelineDefinition) => {
    setPipeline(newPipeline);
    setHasUnsavedChanges(true);
    
    // Validate pipeline on change
    validatePipeline(newPipeline).then(setValidationResult);
  }, [validatePipeline]);

  // Handle pipeline execution
  const handleExecute = useCallback(async () => {
    if (!validationResult?.valid) {
      const result = await validatePipeline(pipeline);
      setValidationResult(result);
      if (!result.valid) {
        return;
      }
    }

    try {
      await executeAsync(pipeline, pipeline.variables, { debugMode: true });
    } catch (error) {
      console.error('Execution failed:', error);
    }
  }, [pipeline, validationResult, validatePipeline, executeAsync]);

  // Handle save
  const handleSave = useCallback(() => {
    // Save to localStorage for now (would be API in real app)
    localStorage.setItem(`pipeline_${pipeline.id}`, JSON.stringify(pipeline));
    setHasUnsavedChanges(false);
    setIsSaveDialogOpen(false);
    
    // Update URL
    const newUrl = new URL(window.location.href);
    newUrl.searchParams.set('id', pipeline.id);
    window.history.replaceState({}, '', newUrl.toString());
  }, [pipeline]);

  // Handle export
  const handleExport = useCallback(() => {
    const dataStr = JSON.stringify(pipeline, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `${pipeline.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }, [pipeline]);

  // Handle import
  const handleImport = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedPipeline = JSON.parse(e.target?.result as string);
          setPipeline({
            ...importedPipeline,
            id: `pipeline_${Date.now()}` // Generate new ID
          });
          setHasUnsavedChanges(true);
        } catch (error) {
          console.error('Failed to import pipeline:', error);
        }
      };
      reader.readAsText(file);
    }
  }, []);

  const getExecutionStatus = () => {
    if (!currentExecution) return null;
    
    const statusColors: Record<ExecutionStatus, string> = {
      [ExecutionStatus.PENDING]: 'bg-yellow-100 text-yellow-800',
      [ExecutionStatus.RUNNING]: 'bg-blue-100 text-blue-800',
      [ExecutionStatus.COMPLETED]: 'bg-green-100 text-green-800',
      [ExecutionStatus.FAILED]: 'bg-red-100 text-red-800',
      [ExecutionStatus.CANCELLED]: 'bg-gray-100 text-gray-800',
      [ExecutionStatus.PAUSED]: 'bg-purple-100 text-purple-800',
    };

    return (
      <Badge className={statusColors[currentExecution.status] || 'bg-gray-100 text-gray-800'}>
        {currentExecution.status}
      </Badge>
    );
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">{pipeline.name}</h1>
            {hasUnsavedChanges && (
              <Badge variant="outline" className="text-xs">
                Unsaved changes
              </Badge>
            )}
            {getExecutionStatus()}
          </div>
          
          <div className="flex items-center gap-2">
            {/* Execution Stats */}
            {currentExecution && (
              <div className="flex items-center gap-4 text-sm text-gray-600 mr-4">
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {Math.round(executionTime)}s
                </div>
                <div className="flex items-center gap-1">
                  <DollarSign className="h-4 w-4" />
                  ${totalCost.toFixed(4)}
                </div>
                <div>
                  {totalTokens.toLocaleString()} tokens
                </div>
                <div>
                  {Math.round(progress)}% complete
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsSettingsOpen(true)}
            >
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>

            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => document.getElementById('import-input')?.click()}
              >
                <Upload className="h-4 w-4 mr-2" />
                Import
              </Button>
              <input
                id="import-input"
                type="file"
                accept=".json"
                onChange={handleImport}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>

            {isExecuting ? (
              <Button
                variant="outline"
                size="sm"
                onClick={cancelExecution}
              >
                Cancel
              </Button>
            ) : (
              <Button
                onClick={handleExecute}
                disabled={!validationResult?.valid || pipeline.steps.length === 0}
                size="sm"
              >
                <Play className="h-4 w-4 mr-2" />
                Execute
              </Button>
            )}

            <Dialog open={isSaveDialogOpen} onOpenChange={setIsSaveDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="default" size="sm">
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Save Pipeline</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="name">Pipeline Name</Label>
                    <Input
                      id="name"
                      value={pipeline.name}
                      onChange={(e) => setPipeline(prev => ({ ...prev, name: e.target.value }))}
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      rows={3}
                      value={pipeline.description || ''}
                      onChange={(e) => setPipeline(prev => ({ ...prev, description: e.target.value }))}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsSaveDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave}>
                    Save Pipeline
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Status Bar */}
        {(executionError || validationResult) && (
          <div className="mt-3">
            {executionError && (
              <Alert className="border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-red-800">
                  {executionError}
                </AlertDescription>
              </Alert>
            )}
            
            {validationResult && !validationResult.valid && (
              <Alert className="border-yellow-200 bg-yellow-50">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-yellow-800">
                  {validationResult.errors.length} validation error(s) found
                </AlertDescription>
              </Alert>
            )}

            {validationResult && validationResult.valid && !executionError && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4" />
                <AlertDescription className="text-green-800">
                  Pipeline is valid and ready to execute
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1">
        <PipelineBuilder
          pipeline={pipeline}
          onChange={handlePipelineChange}
          onExecute={handleExecute}
          onSave={() => setIsSaveDialogOpen(true)}
          isExecuting={isExecuting}
          validationResult={validationResult || undefined}
        />
      </div>

      {/* Settings Dialog */}
      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Pipeline Settings</DialogTitle>
          </DialogHeader>
          
          <Tabs defaultValue="general" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="general">General</TabsTrigger>
              <TabsTrigger value="variables">Variables</TabsTrigger>
              <TabsTrigger value="execution">Execution</TabsTrigger>
            </TabsList>
            
            <TabsContent value="general" className="space-y-4">
              <div>
                <Label htmlFor="pipeline-name">Name</Label>
                <Input
                  id="pipeline-name"
                  value={pipeline.name}
                  onChange={(e) => setPipeline(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="pipeline-description">Description</Label>
                <Textarea
                  id="pipeline-description"
                  rows={3}
                  value={pipeline.description || ''}
                  onChange={(e) => setPipeline(prev => ({ ...prev, description: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="pipeline-version">Version</Label>
                <Input
                  id="pipeline-version"
                  value={pipeline.version}
                  onChange={(e) => setPipeline(prev => ({ ...prev, version: e.target.value }))}
                />
              </div>
            </TabsContent>
            
            <TabsContent value="variables" className="space-y-4">
              <div>
                <Label>Pipeline Variables (JSON)</Label>
                <Textarea
                  rows={8}
                  value={JSON.stringify(pipeline.variables, null, 2)}
                  onChange={(e) => {
                    try {
                      const variables = JSON.parse(e.target.value);
                      setPipeline(prev => ({ ...prev, variables }));
                    } catch (error) {
                      // Invalid JSON, don't update
                    }
                  }}
                  className="font-mono"
                />
              </div>
            </TabsContent>
            
            <TabsContent value="execution" className="space-y-4">
              <div>
                <Label>Execution Settings (JSON)</Label>
                <Textarea
                  rows={8}
                  value={JSON.stringify(pipeline.settings, null, 2)}
                  onChange={(e) => {
                    try {
                      const settings = JSON.parse(e.target.value);
                      setPipeline(prev => ({ ...prev, settings }));
                    } catch (error) {
                      // Invalid JSON, don't update
                    }
                  }}
                  className="font-mono"
                />
              </div>
            </TabsContent>
          </Tabs>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSettingsOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PipelineBuilderPageNew;