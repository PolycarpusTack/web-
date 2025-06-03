// Additional pipeline configuration types

export interface PipelineStepConfig {
  // Common fields
  type?: string;
  timeout?: number;
  
  // LLM Step Config
  model_id?: string;
  prompt?: string;
  system_prompt?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
  response_format?: 'text' | 'json';
  stream?: boolean;
  
  // Code Step Config
  code?: string;
  language?: string;
  memory_limit?: number;
  packages?: string[];
  
  // API Step Config
  url?: string;
  method?: string;
  headers?: Array<{ key: string; value: string }>;
  body?: string;
  body_type?: 'json' | 'text' | 'form';
  auth?: {
    type: 'none' | 'bearer' | 'basic' | 'api_key';
    token?: string;
    username?: string;
    password?: string;
    api_key?: string;
    header_name?: string;
  };
  follow_redirects?: boolean;
  validate_ssl?: boolean;
  
  // Transform Step Config
  mappings?: Array<{
    id: string;
    sourceField: string;
    targetField: string;
    transformation?: string;
    type: 'direct' | 'function' | 'expression';
    description?: string;
  }>;
  filter_conditions?: Array<{
    field: string;
    operator: string;
    value: string;
    type: string;
  }>;
  source_path?: string;
  target_key?: string;
  custom_expression?: string;
  
  // Condition Step Config
  condition_mode?: 'simple' | 'complex' | 'expression';
  conditions?: Array<{
    id: string;
    field: string;
    operator: string;
    value: string;
    type: string;
    description?: string;
  }>;
  logical_operator?: 'AND' | 'OR';
  branches?: Array<{
    condition: string;
    steps: string[];
    description?: string;
  }>;
  default_branch?: string;
  test_data?: any;
}

export interface ValidationError {
  message: string;
  severity: 'error' | 'warning';
  step_id?: string;
  step_name?: string;
  field?: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}