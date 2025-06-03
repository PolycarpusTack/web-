import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle, Check as CheckCircle, ChevronLeft, Clock, Copy, Download, LogOut, Pause, PlayIcon, RefreshCw, X } from "lucide-react";

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

import { getPipeline, executePipeline, getPipelineExecution } from '@/api/pipelines';

// Types
interface Pipeline {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  is_active: boolean;
  is_public: boolean;
  version: string;
  tags: string[];
  steps: PipelineStep[];
}

interface PipelineStep {
  id: string;
  pipeline_id: string;
  name: string;
  description: string;
  type: string;
  order: number;
  config: any;
  input_mapping: Record<string, any>;
  output_mapping: Record<string, any>;
  is_enabled: boolean;
  timeout: number | null;
  retry_config: any;
  created_at: string;
  updated_at: string;
}

interface StepExecution {
  id: string;
  pipeline_execution_id: string;
  step_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  inputs: any;
  outputs: any;
  error: string | null;
  logs: any[] | null;
  duration_ms: number | null;
  metrics: any;
  model_id: string | null;
  step: PipelineStep;
}

interface PipelineExecution {
  id: string;
  pipeline_id: string;
  user_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  input_parameters: any;
  results: any;
  error: string | null;
  duration_ms: number | null;
  logs: any[] | null;
  metadata: any;
  step_executions: StepExecution[];
}

// Step status badge
const StepStatusBadge = ({ status }: { status: string }) => {
  switch (status) {
    case 'completed':
      return (
        <Badge className="bg-emerald-600 text-white">
          <CheckCircle className="h-3 w-3 mr-1" />
          Completed
        </Badge>
      );
    case 'running':
      return (
        <Badge className="bg-blue-600 text-white">
          <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
          Running
        </Badge>
      );
    case 'pending':
      return (
        <Badge className="bg-slate-600 text-white">
          <Clock className="h-3 w-3 mr-1" />
          Pending
        </Badge>
      );
    case 'failed':
      return (
        <Badge className="bg-red-600 text-white">
          <X className="h-3 w-3 mr-1" />
          Failed
        </Badge>
      );
    case 'skipped':
      return (
        <Badge className="bg-amber-600 text-white">
          <LogOut className="h-3 w-3 mr-1" />
          Skipped
        </Badge>
      );
    default:
      return (
        <Badge className="bg-slate-600 text-white">
          {status}
        </Badge>
      );
  }
};

// Step type icons
const StepTypeIcon = ({ type }: { type: string }) => {
  switch (type) {
    case 'prompt':
      return (
        <div className="bg-purple-600 p-1 rounded-md">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
            <path d="M7.5 1.5C4.5 1.5 1.5 3.5 1.5 7.5C1.5 11.5 4.5 13.5 7.5 13.5C10.5 13.5 13.5 11.5 13.5 7.5C13.5 3.5 10.5 1.5 7.5 1.5ZM7.5 3C9.5 3 10.5 4 10.5 5C10.5 6 9.5 7 7.5 7C5.5 7 4.5 6 4.5 5C4.5 4 5.5 3 7.5 3ZM4.5 9C4.5 8 5.5 7 7.5 7C9.5 7 10.5 8 10.5 9C10.5 10 9.5 11 7.5 11C5.5 11 4.5 10 4.5 9Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </div>
      );
    case 'code':
      return (
        <div className="bg-amber-600 p-1 rounded-md">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
            <path d="M9.96424 2.68571C10.0668 2.42931 9.94209 2.13833 9.6857 2.03577C9.4293 1.93322 9.13832 2.05792 9.03576 2.31432L5.03576 12.3143C4.9332 12.5707 5.05791 12.8617 5.3143 12.9642C5.5707 13.0668 5.86168 12.9421 5.96424 12.6857L9.96424 2.68571ZM3.85355 5.14645C4.04882 5.34171 4.04882 5.65829 3.85355 5.85355L2.20711 7.5L3.85355 9.14645C4.04882 9.34171 4.04882 9.65829 3.85355 9.85355C3.65829 10.0488 3.34171 10.0488 3.14645 9.85355L1.14645 7.85355C0.951184 7.65829 0.951184 7.34171 1.14645 7.14645L3.14645 5.14645C3.34171 4.95118 3.65829 4.95118 3.85355 5.14645ZM11.1464 5.14645C11.3417 4.95118 11.6583 4.95118 11.8536 5.14645L13.8536 7.14645C14.0488 7.34171 14.0488 7.65829 13.8536 7.85355L11.8536 9.85355C11.6583 10.0488 11.3417 10.0488 11.1464 9.85355C10.9512 9.65829 10.9512 9.34171 11.1464 9.14645L12.7929 7.5L11.1464 5.85355C10.9512 5.65829 10.9512 5.34171 11.1464 5.14645Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </div>
      );
    case 'file':
      return (
        <div className="bg-blue-600 p-1 rounded-md">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
            <path d="M3.5 2C3.22386 2 3 2.22386 3 2.5V12.5C3 12.7761 3.22386 13 3.5 13H11.5C11.7761 13 12 12.7761 12 12.5V6H8.5C8.22386 6 8 5.77614 8 5.5V2H3.5ZM9 2.70711L11.2929 5H9V2.70711ZM2 2.5C2 1.67157 2.67157 1 3.5 1H8.5C8.63261 1 8.75979 1.05268 8.85355 1.14645L12.8536 5.14645C12.9473 5.24021 13 5.36739 13 5.5V12.5C13 13.3284 12.3284 14 11.5 14H3.5C2.67157 14 2 13.3284 2 12.5V2.5Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </div>
      );
    case 'api':
      return (
        <div className="bg-green-600 p-1 rounded-md">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
            <path d="M7.49991 0.876892C3.84222 0.876892 0.877075 3.84204 0.877075 7.49972C0.877075 11.1574 3.84222 14.1226 7.49991 14.1226C11.1576 14.1226 14.1227 11.1574 14.1227 7.49972C14.1227 3.84204 11.1576 0.876892 7.49991 0.876892ZM1.82707 7.49972C1.82707 4.36671 4.36689 1.82689 7.49991 1.82689C10.6329 1.82689 13.1727 4.36671 13.1727 7.49972C13.1727 10.6327 10.6329 13.1726 7.49991 13.1726C4.36689 13.1726 1.82707 10.6327 1.82707 7.49972ZM7.50003 4C7.77617 4 8.00003 4.22386 8.00003 4.5V7H9.50003C9.77617 7 10 7.22386 10 7.5C10 7.77614 9.77617 8 9.50003 8H7.50003C7.22389 8 7.00003 7.77614 7.00003 7.5V4.5C7.00003 4.22386 7.22389 4 7.50003 4Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </div>
      );
    case 'condition':
      return (
        <div className="bg-orange-600 p-1 rounded-md">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
            <path d="M7.14645 2.14645C7.34171 1.95118 7.65829 1.95118 7.85355 2.14645L11.8536 6.14645C12.0488 6.34171 12.0488 6.65829 11.8536 6.85355C11.6583 7.04882 11.3417 7.04882 11.1464 6.85355L7.5 3.20711L3.85355 6.85355C3.65829 7.04882 3.34171 7.04882 3.14645 6.85355C2.95118 6.65829 2.95118 6.34171 3.14645 6.14645L7.14645 2.14645ZM7.85355 12.8536C7.65829 13.0488 7.34171 13.0488 7.14645 12.8536L3.14645 8.85355C2.95118 8.65829 2.95118 8.34171 3.14645 8.14645C3.34171 7.95118 3.65829 7.95118 3.85355 8.14645L7.5 11.7929L11.1464 8.14645C11.3417 7.95118 11.6583 7.95118 11.8536 8.14645C12.0488 8.34171 12.0488 8.65829 11.8536 8.85355L7.85355 12.8536Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </div>
      );
    case 'transform':
      return (
        <div className="bg-pink-600 p-1 rounded-md">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
            <path d="M5.5 15H4L4 1H5.5L5.5 15ZM11 15H9.5L9.5 1H11L11 15ZM7.5 1H8.95V15H7.5V1ZM1 1H2.5V15H1V1ZM13 1H14.5V15H13V1Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </div>
      );
    default:
      return (
        <div className="bg-slate-600 p-1 rounded-md">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
            <path d="M7.49991 0.876892C3.84222 0.876892 0.877075 3.84204 0.877075 7.49972C0.877075 11.1574 3.84222 14.1226 7.49991 14.1226C11.1576 14.1226 14.1227 11.1574 14.1227 7.49972C14.1227 3.84204 11.1576 0.876892 7.49991 0.876892ZM1.82707 7.49972C1.82707 4.36671 4.36689 1.82689 7.49991 1.82689C10.6329 1.82689 13.1727 4.36671 13.1727 7.49972C13.1727 10.6327 10.6329 13.1726 7.49991 13.1726C4.36689 13.1726 1.82707 10.6327 1.82707 7.49972ZM7.50003 4C7.77617 4 8.00003 4.22386 8.00003 4.5V7H9.50003C9.77617 7 10 7.22386 10 7.5C10 7.77614 9.77617 8 9.50003 8H7.50003C7.22389 8 7.00003 7.77614 7.00003 7.5V4.5C7.00003 4.22386 7.22389 4 7.50003 4Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </div>
      );
  }
};

// JSON Viewer component
const JsonViewer = ({ data, title }: { data: any, title?: string }) => {
  const [copied, setCopied] = useState(false);
  
  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      {title && (
        <div className="flex justify-between items-center px-4 py-2 border-b border-slate-700 bg-slate-900">
          <div className="font-medium text-slate-200">{title}</div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-8 w-8 p-0 text-slate-400 hover:text-slate-100"
                  onClick={copyToClipboard}
                >
                  {copied ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Copy to clipboard</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}
      <ScrollArea className="max-h-80 p-4">
        <pre className="text-slate-300 text-sm font-mono whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </pre>
      </ScrollArea>
    </div>
  );
};

// Pipeline Execution Page Component
const PipelineExecutionPage = () => {
  const { id, executionId } = useParams<{ id: string, executionId?: string }>();
  const navigate = useNavigate();
  
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [execution, setExecution] = useState<PipelineExecution | null>(null);
  const [inputParameters, setInputParameters] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [pollingTimeout, setPollingTimeout] = useState<NodeJS.Timeout | null>(null);
  
  // Refs
  const inputsRef = useRef<Record<string, any>>({});
  
  // Fetch pipeline data
  useEffect(() => {
    const fetchPipeline = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const data = await getPipeline(id);
        setPipeline(data);
        
        // Initialize inputs based on pipeline config
        if (data.config && data.config.input_schema) {
          const initialInputs: Record<string, any> = {};
          Object.entries(data.config.input_schema).forEach(([key, value]) => {
            initialInputs[key] = '';
          });
          setInputParameters(initialInputs);
          inputsRef.current = initialInputs;
        }
      } catch (error) {
        console.error('Failed to fetch pipeline:', error);
        toast({
          title: "Failed to load pipeline",
          description: "There was an error loading the pipeline. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchPipeline();
  }, [id]);
  
  // Fetch execution data if executionId is provided
  useEffect(() => {
    const fetchExecution = async () => {
      if (!executionId) return;
      
      try {
        setLoading(true);
        const data = await getPipelineExecution(executionId);
        setExecution(data);
        
        // If execution is still running, poll for updates
        if (data.status === 'running' || data.status === 'pending') {
          startPolling(executionId);
        }
      } catch (error) {
        console.error('Failed to fetch execution:', error);
        toast({
          title: "Failed to load execution",
          description: "There was an error loading the execution data. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };
    
    if (executionId) {
      fetchExecution();
    } else {
      setLoading(false);
    }
    
    return () => {
      // Clear any polling timeouts when component unmounts
      if (pollingTimeout) {
        clearTimeout(pollingTimeout);
      }
    };
  }, [executionId]);
  
  // Start polling for execution updates
  const startPolling = (execId: string) => {
    if (pollingTimeout) {
      clearTimeout(pollingTimeout);
    }
    
    const pollTimeout = setTimeout(async () => {
      try {
        const data = await getPipelineExecution(execId);
        setExecution(data);
        
        // Continue polling if still running
        if (data.status === 'running' || data.status === 'pending') {
          startPolling(execId);
        }
      } catch (error) {
        console.error('Error polling execution:', error);
        // Retry polling even on error
        startPolling(execId);
      }
    }, 2000);
    
    setPollingTimeout(pollTimeout);
  };
  
  // Update input parameter
  const updateInputParameter = (key: string, value: any) => {
    setInputParameters((prev) => ({
      ...prev,
      [key]: value
    }));
    inputsRef.current[key] = value;
  };
  
  // Execute the pipeline
  const executePipelineHandler = async () => {
    if (!pipeline) return;
    
    try {
      setExecuting(true);
      
      // Execute pipeline
      const executionData = await executePipeline(pipeline.id, {
        input_parameters: inputsRef.current
      });
      
      // Set execution and start polling
      setExecution(executionData);
      startPolling(executionData.id);
      
      // Navigate to execution page
      navigate(`/pipelines/${pipeline.id}/executions/${executionData.id}`);
      
      toast({
        title: "Pipeline execution started",
        description: "Your pipeline is now running.",
      });
    } catch (error) {
      console.error('Failed to execute pipeline:', error);
      toast({
        title: "Failed to execute pipeline",
        description: "There was an error starting the pipeline execution. Please try again.",
        variant: "destructive"
      });
    } finally {
      setExecuting(false);
    }
  };
  
  // Get the progress percentage of execution
  const getProgressPercentage = () => {
    if (!execution || !pipeline) return 0;
    
    const totalSteps = pipeline.steps.filter(s => s.is_enabled).length;
    if (totalSteps === 0) return 0;
    
    const completedSteps = execution.step_executions.filter(
      s => s.status === 'completed' || s.status === 'skipped'
    ).length;
    
    return (completedSteps / totalSteps) * 100;
  };
  
  // Render loading state
  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-screen-2xl">
        <div className="flex items-center mb-8">
          <Button 
            variant="ghost" 
            size="sm" 
            className="mr-4 text-slate-400"
            onClick={() => navigate(`/pipelines/${id}`)}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <div className="flex-1">
            <Skeleton className="h-8 w-1/3 bg-slate-700 mb-1" />
            <Skeleton className="h-4 w-1/2 bg-slate-700" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <Skeleton className="h-10 w-full bg-slate-700 mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full bg-slate-700" />
              ))}
            </div>
          </div>
          
          <div className="lg:col-span-2">
            <Skeleton className="h-10 w-full bg-slate-700 mb-4" />
            <Skeleton className="h-64 w-full bg-slate-700" />
          </div>
        </div>
      </div>
    );
  }
  
  // Render when pipeline not found
  if (!pipeline) {
    return (
      <div className="container mx-auto py-8 px-4 text-center">
        <h1 className="text-2xl font-bold text-slate-200 mb-4">Pipeline Not Found</h1>
        <p className="text-slate-400 mb-6">The pipeline you're looking for doesn't exist or you don't have access to it.</p>
        <Button 
          onClick={() => navigate('/pipelines')}
          className="bg-cyan-600 hover:bg-cyan-700 text-white"
        >
          Back to Pipelines
        </Button>
      </div>
    );
  }
  
  // Render execution form if no execution is active
  if (!execution) {
    return (
      <div className="container mx-auto py-4 px-4 max-w-screen-2xl">
        {/* Header */}
        <div className="flex items-center mb-6">
          <Button 
            variant="ghost" 
            size="sm" 
            className="mr-4 text-slate-400 hover:text-slate-100 hover:bg-slate-800"
            onClick={() => navigate(`/pipelines/${pipeline.id}`)}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-50">{pipeline.name}</h1>
            <p className="text-slate-400">{pipeline.description || 'No description'}</p>
          </div>
        </div>
        
        {/* Execution Form */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100">Pipeline Steps</CardTitle>
                <CardDescription className="text-slate-400">
                  Steps that will be executed in order
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {pipeline.steps
                  .sort((a, b) => a.order - b.order)
                  .map((step) => (
                    <div key={step.id} className="flex items-start space-x-3">
                      <StepTypeIcon type={step.type} />
                      <div>
                        <div className="font-medium text-slate-200">{step.name}</div>
                        <div className="text-sm text-slate-400">{step.description || 'No description'}</div>
                      </div>
                    </div>
                  ))}
                
                {pipeline.steps.length === 0 && (
                  <div className="text-center py-6 text-slate-400">
                    No steps defined in this pipeline.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          
          <div className="lg:col-span-2">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100">Execute Pipeline</CardTitle>
                <CardDescription className="text-slate-400">
                  Configure input parameters and run the pipeline
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="text-slate-200 font-medium mb-4">Input Parameters</h3>
                  
                  {Object.keys(inputParameters).length === 0 ? (
                    <div className="bg-slate-900 border border-slate-700 rounded-md p-4">
                      <div className="flex items-start space-x-3">
                        <AlertCircle className="h-5 w-5 text-slate-400 mt-0.5" />
                        <div>
                          <h4 className="text-slate-300 font-medium">No Input Parameters Required</h4>
                          <p className="text-slate-400 text-sm">
                            This pipeline doesn't require any input parameters. You can execute it directly.
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {Object.entries(inputParameters).map(([key, value]) => (
                        <div key={key}>
                          <Label className="text-slate-300 mb-1">{key}</Label>
                          <Textarea 
                            className="bg-slate-900 border-slate-700 text-slate-200" 
                            placeholder={`Enter value for ${key}`}
                            value={value}
                            onChange={(e) => updateInputParameter(key, e.target.value)}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="flex justify-end mt-6">
                  <Button 
                    className="bg-cyan-600 hover:bg-cyan-700 text-white"
                    onClick={executePipelineHandler}
                    disabled={executing}
                  >
                    {executing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        <PlayIcon className="h-4 w-4 mr-2" />
                        Execute Pipeline
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }
  
  // Render execution details
  return (
    <div className="container mx-auto py-4 px-4 max-w-screen-2xl">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            size="sm" 
            className="mr-4 text-slate-400 hover:text-slate-100 hover:bg-slate-800"
            onClick={() => navigate(`/pipelines/${pipeline.id}`)}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-50">{pipeline.name}</h1>
            <p className="text-slate-400">{pipeline.description || 'No description'}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <StepStatusBadge status={execution.status} />
          {execution.status === 'running' && (
            <Button 
              variant="outline" 
              size="sm" 
              className="border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-slate-100"
            >
              <Pause className="h-4 w-4 mr-1" />
              Cancel
            </Button>
          )}
        </div>
      </div>
      
      {/* Execution Progress */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <div className="text-sm text-slate-400">Execution Progress</div>
          <div className="text-sm text-slate-400">
            {execution.status === 'completed' ? '100%' : `${Math.round(getProgressPercentage())}%`}
          </div>
        </div>
        <Progress 
          value={getProgressPercentage()} 
          className="h-2 bg-slate-700"
        />
      </div>
      
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step Executions */}
        <div className="lg:col-span-1">
          <h2 className="text-lg font-medium text-slate-100 mb-4">Step Executions</h2>
          
          <div className="space-y-3">
            {pipeline.steps
              .sort((a, b) => a.order - b.order)
              .map((step) => {
                // Find the step execution for this step
                const stepExecution = execution.step_executions.find(se => se.step_id === step.id);
                
                // Skip disabled steps
                if (!step.is_enabled) return null;
                
                return (
                  <Card 
                    key={step.id} 
                    className={`bg-slate-800 border-slate-700 ${
                      stepExecution?.status === 'running' ? 'border-cyan-600' : ''
                    }`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start space-x-3">
                        <StepTypeIcon type={step.type} />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-slate-200 truncate">{step.name}</div>
                          <div className="text-sm text-slate-400 truncate">{step.description || 'No description'}</div>
                          
                          {stepExecution ? (
                            <div className="mt-2 flex items-center justify-between">
                              <StepStatusBadge status={stepExecution.status} />
                              
                              {stepExecution.duration_ms && (
                                <div className="text-xs text-slate-400">
                                  {(stepExecution.duration_ms / 1000).toFixed(1)}s
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="mt-2">
                              <StepStatusBadge status="pending" />
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
          </div>
        </div>
        
        {/* Execution Details */}
        <div className="lg:col-span-2">
          <Tabs defaultValue="results">
            <TabsList className="bg-slate-800 border-slate-700 w-full sm:w-auto">
              <TabsTrigger 
                value="results" 
                className="data-[state=active]:bg-slate-900 data-[state=active]:text-white"
              >
                Results
              </TabsTrigger>
              <TabsTrigger 
                value="inputs" 
                className="data-[state=active]:bg-slate-900 data-[state=active]:text-white"
              >
                Inputs
              </TabsTrigger>
              <TabsTrigger 
                value="details" 
                className="data-[state=active]:bg-slate-900 data-[state=active]:text-white"
              >
                Details
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="results" className="mt-4 space-y-4">
              {execution.status === 'running' || execution.status === 'pending' ? (
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-6 text-center">
                    <RefreshCw className="h-10 w-10 text-cyan-600 animate-spin mx-auto mb-3" />
                    <h3 className="text-slate-200 text-lg mb-1">Execution in Progress</h3>
                    <p className="text-slate-400">
                      The pipeline is currently running. Results will appear here when complete.
                    </p>
                  </CardContent>
                </Card>
              ) : execution.status === 'failed' ? (
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-red-500 flex items-center">
                      <X className="h-5 w-5 mr-2" />
                      Execution Failed
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {execution.error ? (
                      <div className="bg-slate-900 border border-slate-700 rounded-md p-4 text-red-400 font-mono text-sm">
                        {execution.error}
                      </div>
                    ) : (
                      <p className="text-slate-400">
                        The pipeline execution failed. Check the step details for more information.
                      </p>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <>
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-emerald-500 flex items-center">
                        <CheckCircle className="h-5 w-5 mr-2" />
                        Execution Completed
                      </CardTitle>
                      {execution.duration_ms && (
                        <CardDescription className="text-slate-400">
                          Completed in {(execution.duration_ms / 1000).toFixed(1)} seconds
                        </CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      {execution.results ? (
                        <JsonViewer data={execution.results} title="Results" />
                      ) : (
                        <p className="text-slate-400">
                          No results were returned from this pipeline execution.
                        </p>
                      )}
                    </CardContent>
                  </Card>
                  
                  <div className="flex justify-end space-x-2">
                    <Button 
                      variant="outline" 
                      className="border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-slate-100"
                      onClick={() => {
                        // Download results as JSON
                        const blob = new Blob(
                          [JSON.stringify(execution.results, null, 2)], 
                          { type: 'application/json' }
                        );
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `pipeline-${pipeline.id}-results.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download Results
                    </Button>
                    
                    <Button 
                      className="bg-cyan-600 hover:bg-cyan-700 text-white"
                      onClick={() => {
                        navigate(`/pipelines/${pipeline.id}/run`);
                      }}
                    >
                      <PlayIcon className="h-4 w-4 mr-1" />
                      Run Again
                    </Button>
                  </div>
                </>
              )}
            </TabsContent>
            
            <TabsContent value="inputs" className="mt-4">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100">Input Parameters</CardTitle>
                </CardHeader>
                <CardContent>
                  {execution.input_parameters && Object.keys(execution.input_parameters).length > 0 ? (
                    <JsonViewer data={execution.input_parameters} />
                  ) : (
                    <p className="text-slate-400">
                      No input parameters were provided for this execution.
                    </p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="details" className="mt-4 space-y-4">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100">Execution Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-slate-400">Execution ID</Label>
                      <div className="text-slate-200 font-mono text-sm">{execution.id}</div>
                    </div>
                    
                    <div>
                      <Label className="text-slate-400">Status</Label>
                      <div><StepStatusBadge status={execution.status} /></div>
                    </div>
                    
                    <div>
                      <Label className="text-slate-400">Started At</Label>
                      <div className="text-slate-200">
                        {new Date(execution.started_at).toLocaleString()}
                      </div>
                    </div>
                    
                    {execution.completed_at && (
                      <div>
                        <Label className="text-slate-400">Completed At</Label>
                        <div className="text-slate-200">
                          {new Date(execution.completed_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                    
                    {execution.duration_ms && (
                      <div>
                        <Label className="text-slate-400">Duration</Label>
                        <div className="text-slate-200">
                          {(execution.duration_ms / 1000).toFixed(2)} seconds
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
              
              {execution.logs && execution.logs.length > 0 && (
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-slate-100">Execution Logs</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-80 rounded-md border border-slate-700 bg-slate-900 p-4">
                      <div className="font-mono text-sm text-slate-300 whitespace-pre-wrap">
                        {execution.logs.map((log, i) => (
                          <div key={i} className="mb-1">
                            {log.timestamp && (
                              <span className="text-slate-500">[{new Date(log.timestamp).toLocaleTimeString()}] </span>
                            )}
                            <span>{log.message || JSON.stringify(log)}</span>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default PipelineExecutionPage;