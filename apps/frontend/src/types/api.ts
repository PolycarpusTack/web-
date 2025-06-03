// API Types for Web+ Application

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Model-related types
export interface ModelCapabilities {
  text_generation?: boolean;
  chat?: boolean;
  reasoning?: boolean;
  code_generation?: boolean;
  multimodal?: boolean;
  analysis?: boolean;
}

export interface ModelParameters {
  model_type: 'general' | 'code' | 'multimodal' | 'reasoning';
  api_endpoint?: string;
  requires_ollama?: boolean;
  max_context_length?: number;
  [key: string]: any;
}

export interface ModelPricing {
  input_tokens: number;
  output_tokens: number;
  currency: string;
  per_tokens: number;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  description?: string;
  version?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  parameters?: ModelParameters;
  capabilities?: ModelCapabilities;
  context_window: number;
  max_output_tokens?: number;
  pricing?: ModelPricing;
  size?: string;
  tags?: Tag[];
  status?: 'running' | 'stopped' | 'loading' | 'error';
  running?: boolean;
}

export interface Tag {
  id: number;
  name: string;
  description?: string;
}

// User and Auth types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  role: 'user' | 'admin' | 'developer';
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  notifications?: boolean;
  default_model?: string;
  language?: string;
  [key: string]: any;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

// JWT Token payload
export interface JWTPayload {
  sub: string; // user ID
  username: string;
  email: string;
  role: string;
  exp: number;
  iat: number;
}

// Conversation and Message types
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  model_id: string;
  system_prompt?: string;
  meta_data?: Record<string, any>;
  model?: Model;
  messages?: Message[];
  users?: User[];
  files?: File[];
  threads?: MessageThread[];
}

export interface Message {
  id: string;
  conversation_id: string;
  user_id?: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  created_at: string;
  meta_data?: Record<string, any>;
  tokens?: number;
  cost?: number;
  parent_id?: string;
  thread_id?: string;
  user?: User;
  files?: MessageFile[];
  replies?: Message[];
}

export interface MessageThread {
  id: string;
  conversation_id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  creator_id?: string;
  parent_thread_id?: string;
  meta_data?: Record<string, any>;
  messages?: Message[];
  creator?: User;
  child_threads?: MessageThread[];
}

// File types
export interface File {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size: number;
  path: string;
  user_id: string;
  conversation_id?: string;
  created_at: string;
  meta_data?: Record<string, any>;
  is_public: boolean;
  analyzed: boolean;
  analysis_result?: Record<string, any>;
  extracted_text?: string;
  user?: User;
  conversation?: Conversation;
}

export interface MessageFile {
  message_id: string;
  file_id: string;
  message?: Message;
  file?: File;
}

// API Key types
export interface ApiKey {
  id: string;
  key: string;
  name: string;
  user_id: string;
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
  is_active: boolean;
  user?: User;
}

// Chat and streaming types
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  files?: File[];
  timestamp?: string;
}

export interface ChatRequest {
  model_id: string;
  messages: ChatMessage[];
  system_prompt?: string;
  stream?: boolean;
  max_tokens?: number;
  temperature?: number;
  conversation_id?: string;
}

export interface ChatResponse {
  message: Message;
  conversation?: Conversation;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  cost?: number;
}

// Pipeline types (for future use)
export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  steps: PipelineStep[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
  user_id: string;
}

export interface PipelineStep {
  id: string;
  type: 'model' | 'transform' | 'condition' | 'output';
  name: string;
  config: Record<string, any>;
  order: number;
}

// Error types
export interface ApiErrorDetail {
  detail: string;
  code?: string;
  field?: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

// Utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Form types
export interface FormState {
  isSubmitting: boolean;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
}

// Component prop types
export interface ComponentWithChildren {
  children: React.ReactNode;
}

export interface ComponentWithClassName {
  className?: string;
}

export interface ComponentWithLoading {
  loading?: boolean;
}

export interface ComponentWithError {
  error?: string | null;
}

// Event handler types
export type EventHandler<T = HTMLElement> = (event: React.SyntheticEvent<T>) => void;
export type ChangeHandler = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
export type ClickHandler = (event: React.MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => void;
export type SubmitHandler = (event: React.FormEvent<HTMLFormElement>) => void;

// Generic utility types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type Nullable<T> = T | null;
export type ID = string | number;