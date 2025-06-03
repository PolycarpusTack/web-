import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  PipelineDefinition, 
  ExecutionEvent, 
  ExecutionStatus, 
  PipelineExecution,
  StepExecution,
  ValidationResult
} from '@/types/pipeline';

interface UsePipelineExecutionOptions {
  onExecutionStart?: (executionId: string) => void;
  onExecutionComplete?: (execution: PipelineExecution) => void;
  onExecutionError?: (error: string) => void;
  onStepComplete?: (stepExecution: StepExecution) => void;
  onStepError?: (stepId: string, error: string) => void;
  autoReconnect?: boolean;
}

interface UsePipelineExecutionReturn {
  // State
  isExecuting: boolean;
  currentExecution: PipelineExecution | null;
  stepExecutions: Record<string, StepExecution>;
  executionEvents: ExecutionEvent[];
  error: string | null;
  
  // Actions
  executeAsync: (
    pipeline: PipelineDefinition, 
    initialVariables?: Record<string, any>,
    options?: { dryRun?: boolean; debugMode?: boolean }
  ) => Promise<void>;
  cancelExecution: () => Promise<void>;
  validatePipeline: (pipeline: PipelineDefinition) => Promise<ValidationResult>;
  clearHistory: () => void;
  
  // Computed values
  progress: number;
  totalCost: number;
  totalTokens: number;
  executionTime: number;
}

export const usePipelineExecution = (
  options: UsePipelineExecutionOptions = {}
): UsePipelineExecutionReturn => {
  const {
    onExecutionStart,
    onExecutionComplete,
    onExecutionError,
    onStepComplete,
    onStepError,
    autoReconnect = true
  } = options;

  // State
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentExecution, setCurrentExecution] = useState<PipelineExecution | null>(null);
  const [stepExecutions, setStepExecutions] = useState<Record<string, StepExecution>>({});
  const [executionEvents, setExecutionEvents] = useState<ExecutionEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Helper functions
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    };
  };

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsExecuting(false);
  }, []);

  const handleExecutionEvent = useCallback((event: ExecutionEvent) => {
    setExecutionEvents(prev => [...prev, event]);
    setError(null);

    switch (event.type) {
      case 'started':
        setCurrentExecution({
          id: event.execution_id,
          pipeline_id: event.pipeline_id!,
          status: ExecutionStatus.RUNNING,
          started_at: new Date().toISOString(),
          total_cost: 0,
          total_tokens: 0,
          steps_completed: 0,
          total_steps: event.total_steps || 0,
          user_id: '' // Will be filled by backend
        });
        onExecutionStart?.(event.execution_id);
        break;

      case 'step_started':
        if (event.step_id) {
          setStepExecutions(prev => ({
            ...prev,
            [event.step_id!]: {
              id: `${event.execution_id}_${event.step_id}`,
              execution_id: event.execution_id,
              step_id: event.step_id!,
              step_name: event.step_name || '',
              status: ExecutionStatus.RUNNING,
              started_at: new Date().toISOString(),
              cost: 0,
              tokens_used: 0,
              metadata: event.metadata || {},
              retry_count: 0
            }
          }));
        }
        break;

      case 'step_completed':
        if (event.step_id) {
          setStepExecutions(prev => ({
            ...prev,
            [event.step_id!]: {
              ...prev[event.step_id!],
              status: ExecutionStatus.COMPLETED,
              completed_at: new Date().toISOString(),
              execution_time: event.execution_time,
              cost: event.cost || 0,
              tokens_used: event.tokens_used || 0,
              output_data: event.result,
              metadata: { ...prev[event.step_id!]?.metadata, ...event.metadata }
            }
          }));

          onStepComplete?.({
            ...stepExecutions[event.step_id],
            status: ExecutionStatus.COMPLETED,
            output_data: event.result,
            cost: event.cost || 0,
            tokens_used: event.tokens_used || 0
          });
        }

        setCurrentExecution(prev => prev ? {
          ...prev,
          steps_completed: event.step_index || prev.steps_completed + 1,
          total_cost: prev.total_cost + (event.cost || 0),
          total_tokens: prev.total_tokens + (event.tokens_used || 0)
        } : null);
        break;

      case 'step_failed':
        if (event.step_id) {
          setStepExecutions(prev => ({
            ...prev,
            [event.step_id!]: {
              ...prev[event.step_id!],
              status: ExecutionStatus.FAILED,
              completed_at: new Date().toISOString(),
              execution_time: event.execution_time,
              error: event.error
            }
          }));

          onStepError?.(event.step_id, event.error || 'Unknown error');
        }
        break;

      case 'completed':
        setCurrentExecution(prev => prev ? {
          ...prev,
          status: ExecutionStatus.COMPLETED,
          completed_at: new Date().toISOString(),
          execution_time: event.execution_time,
          total_cost: event.total_cost || prev.total_cost,
          total_tokens: event.total_tokens || prev.total_tokens,
          final_output: event.final_output,
          steps_completed: event.steps_completed || prev.steps_completed
        } : null);

        setIsExecuting(false);
        
        if (currentExecution) {
          onExecutionComplete?.({
            ...currentExecution,
            status: ExecutionStatus.COMPLETED,
            final_output: event.final_output
          });
        }
        break;

      case 'failed':
        setCurrentExecution(prev => prev ? {
          ...prev,
          status: ExecutionStatus.FAILED,
          completed_at: new Date().toISOString(),
          error: event.error
        } : null);

        setError(event.error || 'Pipeline execution failed');
        setIsExecuting(false);
        onExecutionError?.(event.error || 'Pipeline execution failed');
        break;

      case 'cancelled':
        setCurrentExecution(prev => prev ? {
          ...prev,
          status: ExecutionStatus.CANCELLED,
          completed_at: new Date().toISOString()
        } : null);

        setIsExecuting(false);
        break;

      case 'error':
        setError(event.error || 'Unknown error occurred');
        setIsExecuting(false);
        onExecutionError?.(event.error || 'Unknown error occurred');
        break;
    }
  }, [currentExecution, stepExecutions, onExecutionStart, onExecutionComplete, onExecutionError, onStepComplete, onStepError]);

  const executeAsync = useCallback(async (
    pipeline: PipelineDefinition,
    initialVariables: Record<string, any> = {},
    options: { dryRun?: boolean; debugMode?: boolean } = {}
  ) => {
    cleanup();
    setError(null);
    setExecutionEvents([]);
    setStepExecutions({});
    setCurrentExecution(null);

    if (options.dryRun) {
      // For dry run, just validate
      try {
        const response = await fetch('/api/pipeline/execution/execute', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            pipeline,
            initial_variables: initialVariables,
            dry_run: true,
            debug_mode: options.debugMode || false
          })
        });

        if (!response.ok) {
          throw new Error(`Validation failed: ${response.status}`);
        }

        const result = await response.json();
        return result;
      } catch (error: any) {
        setError(error.message);
        throw error;
      }
    }

    // Real execution with SSE
    setIsExecuting(true);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/pipeline/execution/execute', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          pipeline,
          initial_variables: initialVariables,
          dry_run: false,
          debug_mode: options.debugMode || false
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Execution failed: ${response.status}`);
      }

      // Set up SSE to receive execution events
      const eventSource = new EventSource('/api/pipeline/execution/execute');
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const executionEvent: ExecutionEvent = JSON.parse(event.data);
          handleExecutionEvent(executionEvent);
        } catch (error) {
          console.error('Failed to parse execution event:', error);
        }
      };

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        
        if (autoReconnect && reconnectAttemptsRef.current < 3) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect SSE...');
            // Would retry connection here
          }, 2000 * reconnectAttemptsRef.current);
        } else {
          setError('Connection lost and could not reconnect');
          cleanup();
        }
      };

      eventSource.addEventListener('close', () => {
        cleanup();
      });

    } catch (error: any) {
      if (error.name !== 'AbortError') {
        setError(error.message);
        setIsExecuting(false);
      }
      throw error;
    }
  }, [cleanup, handleExecutionEvent, autoReconnect]);

  const cancelExecution = useCallback(async () => {
    if (!currentExecution) return;

    try {
      const response = await fetch(`/api/pipeline/execution/executions/${currentExecution.id}/cancel`, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        cleanup();
        setCurrentExecution(prev => prev ? { ...prev, status: ExecutionStatus.CANCELLED } : null);
      }
    } catch (error) {
      console.error('Failed to cancel execution:', error);
    }
  }, [currentExecution, cleanup]);

  const validatePipeline = useCallback(async (pipeline: PipelineDefinition): Promise<ValidationResult> => {
    try {
      const response = await fetch('/api/pipeline/execution/validate', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ pipeline })
      });

      if (!response.ok) {
        throw new Error(`Validation request failed: ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      return {
        valid: false,
        errors: [{ message: error.message, severity: 'error' }],
        warnings: []
      };
    }
  }, []);

  const clearHistory = useCallback(() => {
    setExecutionEvents([]);
    setStepExecutions({});
    setCurrentExecution(null);
    setError(null);
  }, []);

  // Computed values
  const progress = currentExecution ? 
    (currentExecution.steps_completed / Math.max(currentExecution.total_steps, 1)) * 100 : 0;

  const totalCost = currentExecution?.total_cost || 0;
  const totalTokens = currentExecution?.total_tokens || 0;
  
  const executionTime = currentExecution ? 
    (currentExecution.completed_at ? 
      new Date(currentExecution.completed_at).getTime() - new Date(currentExecution.started_at).getTime() :
      Date.now() - new Date(currentExecution.started_at).getTime()) / 1000 : 0;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    // State
    isExecuting,
    currentExecution,
    stepExecutions,
    executionEvents,
    error,

    // Actions
    executeAsync,
    cancelExecution,
    validatePipeline,
    clearHistory,

    // Computed values
    progress,
    totalCost,
    totalTokens,
    executionTime
  };
};