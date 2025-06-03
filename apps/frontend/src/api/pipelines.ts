import { authApi as api } from '../lib/api';

// Types
export interface Pipeline {
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
  config?: {
    input_schema?: Record<string, unknown>;
    output_schema?: Record<string, unknown>;
    [key: string]: unknown;
  };
}

export interface PipelineStep {
  id: string;
  pipeline_id: string;
  name: string;
  description: string;
  type: string;
  order: number;
  config: Record<string, unknown>;
  input_mapping: Record<string, unknown>;
  output_mapping: Record<string, unknown>;
  is_enabled: boolean;
  timeout: number | null;
  retry_config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface PipelineExecution {
  id: string;
  pipeline_id: string;
  user_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  input_parameters: Record<string, unknown>;
  results: Record<string, unknown> | null;
  error: string | null;
  duration_ms: number | null;
  logs: Record<string, unknown>[] | null;
  metadata: Record<string, unknown>;
  step_executions: StepExecution[];
}

export interface StepExecution {
  id: string;
  pipeline_execution_id: string;
  step_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown> | null;
  error: string | null;
  logs: Record<string, unknown>[] | null;
  duration_ms: number | null;
  metrics: Record<string, unknown> | null;
  model_id: string | null;
  step: PipelineStep;
}

export interface CreatePipelineRequest {
  name: string;
  description?: string;
  is_public?: boolean;
  tags?: string[];
  config?: Record<string, unknown>;
}

export interface UpdatePipelineRequest {
  name?: string;
  description?: string;
  is_public?: boolean;
  tags?: string[];
  config?: Record<string, unknown>;
  is_active?: boolean;
  version?: string;
}

export interface CreatePipelineStepRequest {
  name: string;
  type: string;
  order: number;
  config: Record<string, unknown>;
  description?: string;
  input_mapping?: Record<string, unknown>;
  output_mapping?: Record<string, unknown>;
  is_enabled?: boolean;
  timeout?: number;
  retry_config?: Record<string, unknown> | null;
}

export interface UpdatePipelineStepRequest {
  name?: string;
  description?: string;
  type?: string;
  order?: number;
  config?: Record<string, unknown>;
  input_mapping?: Record<string, unknown>;
  output_mapping?: Record<string, unknown>;
  is_enabled?: boolean;
  timeout?: number;
  retry_config?: Record<string, unknown> | null;
}

export interface ReorderPipelineStepsRequest {
  steps: {
    step_id: string;
    order: number;
  }[];
}

export interface ExecutePipelineRequest {
  input_parameters?: Record<string, unknown>;
}

/**
 * Get all pipelines
 */
export const getPipelines = async (
  tags?: string[],
  include_public: boolean = true,
  skip: number = 0,
  limit: number = 20
): Promise<Pipeline[]> => {
  const queryParams = new URLSearchParams();
  
  if (tags && tags.length > 0) {
    tags.forEach(tag => queryParams.append('tags', tag));
  }
  
  queryParams.append('include_public', include_public.toString());
  queryParams.append('skip', skip.toString());
  queryParams.append('limit', limit.toString());
  
  const response = await api.get<Pipeline[]>(`/api/pipelines?${queryParams.toString()}`);
  return response;
};

/**
 * Get a pipeline by ID
 */
export const getPipeline = async (id: string): Promise<Pipeline> => {
  const response = await api.get<Pipeline>(`/api/pipelines/${id}`);
  return response;
};

/**
 * Create a new pipeline
 */
export const createPipeline = async (data: CreatePipelineRequest): Promise<Pipeline> => {
  const response = await api.post<Pipeline>('/api/pipelines', data);
  return response;
};

/**
 * Update a pipeline
 */
export const updatePipeline = async (id: string, data: UpdatePipelineRequest): Promise<Pipeline> => {
  const response = await api.put<Pipeline>(`/api/pipelines/${id}`, data);
  return response;
};

/**
 * Delete a pipeline
 */
export const deletePipeline = async (id: string): Promise<void> => {
  await api.delete<void>(`/api/pipelines/${id}`);
};

/**
 * Get pipeline steps
 */
export const getPipelineSteps = async (
  pipelineId: string,
  include_disabled: boolean = false
): Promise<PipelineStep[]> => {
  const response = await api.get<PipelineStep[]>(`/api/pipelines/${pipelineId}/steps?include_disabled=${include_disabled}`);
  return response;
};

/**
 * Create a pipeline step
 */
export const createPipelineStep = async (
  pipelineId: string,
  data: CreatePipelineStepRequest
): Promise<PipelineStep> => {
  const response = await api.post<PipelineStep>(`/api/pipelines/${pipelineId}/steps`, data);
  return response;
};

/**
 * Update a pipeline step
 */
export const updatePipelineStep = async (
  pipelineId: string,
  stepId: string,
  data: UpdatePipelineStepRequest
): Promise<PipelineStep> => {
  const response = await api.put<PipelineStep>(`/api/pipelines/${pipelineId}/steps/${stepId}`, data);
  return response;
};

/**
 * Delete a pipeline step
 */
export const deletePipelineStep = async (
  pipelineId: string,
  stepId: string
): Promise<void> => {
  await api.delete<void>(`/api/pipelines/${pipelineId}/steps/${stepId}`);
};

/**
 * Reorder pipeline steps
 */
export const reorderPipelineSteps = async (
  pipelineId: string,
  data: ReorderPipelineStepsRequest
): Promise<{ steps: PipelineStep[] }> => {
  const response = await api.post<{ steps: PipelineStep[] }>(`/api/pipelines/${pipelineId}/steps/reorder`, data);
  return response;
};

/**
 * Execute a pipeline
 */
export const executePipeline = async (
  pipelineId: string,
  data: ExecutePipelineRequest
): Promise<PipelineExecution> => {
  const response = await api.post<PipelineExecution>(`/api/pipelines/${pipelineId}/execute`, data);
  return response;
};

/**
 * Get pipeline executions
 */
export const getPipelineExecutions = async (
  pipelineId?: string,
  status?: string,
  skip: number = 0,
  limit: number = 20,
  include_step_executions: boolean = false
): Promise<PipelineExecution[]> => {
  const queryParams = new URLSearchParams();
  
  if (pipelineId) {
    queryParams.append('pipeline_id', pipelineId);
  }
  
  if (status) {
    queryParams.append('status', status);
  }
  
  queryParams.append('skip', skip.toString());
  queryParams.append('limit', limit.toString());
  queryParams.append('include_step_executions', include_step_executions.toString());
  
  const response = await api.get<PipelineExecution[]>(`/api/pipelines/executions?${queryParams.toString()}`);
  return response;
};

/**
 * Get a specific pipeline execution
 */
export const getPipelineExecution = async (executionId: string): Promise<PipelineExecution> => {
  const response = await api.get<PipelineExecution>(`/api/pipelines/executions/${executionId}`);
  return response;
};