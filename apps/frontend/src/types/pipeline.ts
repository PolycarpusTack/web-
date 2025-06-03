// Pipeline execution types and interfaces

export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused'
}

export enum StepType {
  LLM = 'llm',
  CODE = 'code',
  API = 'api',
  TRANSFORM = 'transform',
  CONDITION = 'condition',
  MERGE = 'merge',
  INPUT = 'input',
  OUTPUT = 'output'
}

export interface ExecutionContext {
  variables: Record<string, any>;
  metadata: Record<string, any>;
  execution_id: string;
  user_id: string;
  step_index: number;
  total_steps: number;
  start_time: string;
}

export interface StepResult {
  success: boolean;
  output?: any;
  error?: string;
  execution_time: number;
  metadata: Record<string, any>;
  cost: number;
  tokens_used: number;
}

export interface PipelineStep {
  id: string;
  name: string;
  type: StepType;
  config: Record<string, any>;
  inputs: string[];
  outputs: string[];
  depends_on: string[];
  retry_count: number;
  timeout: number;
  enabled: boolean;
  
  // UI specific properties
  position?: { x: number; y: number };
  size?: { width: number; height: number };
  selected?: boolean;
}

export interface PipelineConnection {
  id: string;
  source_step_id: string;
  target_step_id: string;
  source_output: string;
  target_input: string;
  label?: string;
}

export interface PipelineDefinition {
  id: string;
  name: string;
  description?: string;
  steps: PipelineStep[];
  connections: PipelineConnection[];
  variables: Record<string, any>;
  settings: Record<string, any>;
  version: string;
  
  // Metadata
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  tags?: string[];
  is_template?: boolean;
  is_public?: boolean;
}

export interface PipelineExecution {
  id: string;
  pipeline_id: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  execution_time?: number;
  total_cost: number;
  total_tokens: number;
  steps_completed: number;
  total_steps: number;
  final_output?: any;
  error?: string;
  user_id: string;
}

export interface StepExecution {
  id: string;
  execution_id: string;
  step_id: string;
  step_name: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  execution_time?: number;
  cost: number;
  tokens_used: number;
  input_data?: any;
  output_data?: any;
  error?: string;
  metadata: Record<string, any>;
  retry_count: number;
}

// Execution event types for real-time updates
export interface ExecutionEvent {
  type: 'started' | 'step_started' | 'step_completed' | 'step_failed' | 'completed' | 'failed' | 'cancelled' | 'error';
  execution_id: string;
  pipeline_id?: string;
  step_id?: string;
  step_name?: string;
  step_index?: number;
  total_steps?: number;
  result?: any;
  execution_time?: number;
  cost?: number;
  tokens_used?: number;
  metadata?: Record<string, any>;
  error?: string;
  details?: any;
  final_output?: any;
  total_cost?: number;
  total_tokens?: number;
  steps_completed?: number;
}

// Step configuration interfaces
export interface LLMStepConfig {
  model_id: string;
  prompt: string;
  max_tokens: number;
  temperature: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  system_prompt?: string;
  response_format?: 'text' | 'json';
}

export interface CodeStepConfig {
  code: string;
  language: 'python' | 'javascript';
  timeout?: number;
  memory_limit?: number;
  packages?: string[];
}

export interface APIStepConfig {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retry_count?: number;
  auth?: {
    type: 'bearer' | 'basic' | 'api_key';
    token?: string;
    username?: string;
    password?: string;
    api_key?: string;
    header_name?: string;
  };
}

export interface TransformStepConfig {
  type: 'extract' | 'filter' | 'format' | 'aggregate' | 'sort';
  source_path?: string;
  target_key?: string;
  fields?: string[];
  condition?: {
    field: string;
    operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'contains';
    value: any;
  };
  format?: string;
  aggregation?: {
    function: 'sum' | 'avg' | 'count' | 'min' | 'max';
    field: string;
  };
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface ConditionStepConfig {
  condition: {
    field: string;
    operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'contains' | 'exists';
    value: any;
  };
  true_branch: string[];  // Step IDs to execute if condition is true
  false_branch: string[]; // Step IDs to execute if condition is false
}

// Pipeline template interfaces
export interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  author: string;
  rating: number;
  usage_count: number;
  pipeline: PipelineDefinition;
  parameters: PipelineParameter[];
  created_at: string;
  updated_at: string;
  is_featured: boolean;
}

export interface PipelineParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'textarea';
  label: string;
  description?: string;
  default_value?: any;
  required: boolean;
  options?: Array<{ value: any; label: string }>;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

// Validation interfaces
export interface ValidationError {
  step_id?: string;
  step_name?: string;
  field?: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
}

export interface ValidationError {
  message: string;
  severity: 'error' | 'warning' | 'info';
  step_id?: string;
  step_name?: string;
  field?: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}

// Analytics interfaces
export interface PipelineAnalytics {
  pipeline_id: string;
  executions_count: number;
  success_rate: number;
  average_execution_time: number;
  total_cost: number;
  total_tokens: number;
  most_used_steps: Array<{
    step_type: StepType;
    count: number;
    percentage: number;
  }>;
  error_patterns: Array<{
    error_type: string;
    count: number;
    percentage: number;
  }>;
  performance_trends: Array<{
    date: string;
    execution_time: number;
    cost: number;
  }>;
}

// UI state interfaces
export interface PipelineEditorState {
  pipeline: PipelineDefinition;
  selected_steps: string[];
  selected_connections: string[];
  zoom: number;
  viewport: { x: number; y: number };
  is_executing: boolean;
  execution_id?: string;
  validation_result?: ValidationResult;
  unsaved_changes: boolean;
}

export interface StepPaletteItem {
  type: StepType;
  name: string;
  description: string;
  icon: string;
  category: string;
  default_config: Record<string, any>;
}

// Utility types
export type StepConfig = 
  | LLMStepConfig 
  | CodeStepConfig 
  | APIStepConfig 
  | TransformStepConfig 
  | ConditionStepConfig;

export type PipelineEventHandler = (event: ExecutionEvent) => void;

export interface PipelineExecutionOptions {
  initial_variables?: Record<string, any>;
  dry_run?: boolean;
  debug_mode?: boolean;
  step_breakpoints?: string[];
}

// Export utility functions for type checking
export const isLLMStep = (step: PipelineStep): step is PipelineStep & { config: LLMStepConfig } => {
  return step.type === StepType.LLM;
};

export const isCodeStep = (step: PipelineStep): step is PipelineStep & { config: CodeStepConfig } => {
  return step.type === StepType.CODE;
};

export const isAPIStep = (step: PipelineStep): step is PipelineStep & { config: APIStepConfig } => {
  return step.type === StepType.API;
};

export const isTransformStep = (step: PipelineStep): step is PipelineStep & { config: TransformStepConfig } => {
  return step.type === StepType.TRANSFORM;
};

export const isConditionStep = (step: PipelineStep): step is PipelineStep & { config: ConditionStepConfig } => {
  return step.type === StepType.CONDITION;
};