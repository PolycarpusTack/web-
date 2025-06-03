/**
 * Comprehensive TypeScript API Type Definitions for Web+ Application
 * Generated from OpenAPI specification and database models
 * 
 * @version 1.0.0
 * @package @web-plus/api-types
 */

// ===== ENUMS AND CONSTANTS =====

/**
 * User roles in the system
 */
export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  DEVELOPER = 'developer',
  MODERATOR = 'moderator'
}

/**
 * Message roles in conversations
 */
export enum MessageRole {
  SYSTEM = 'system',
  USER = 'user',
  ASSISTANT = 'assistant'
}

/**
 * Model providers
 */
export enum ModelProvider {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  META = 'meta',
  MISTRAL = 'mistral',
  GOOGLE = 'google',
  OLLAMA = 'ollama'
}

/**
 * Model statuses
 */
export enum ModelStatus {
  RUNNING = 'running',
  STOPPED = 'stopped',
  LOADING = 'loading',
  ERROR = 'error',
  UNKNOWN = 'unknown'
}

/**
 * Pipeline execution statuses
 */
export enum PipelineExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

/**
 * Pipeline step types
 */
export enum PipelineStepType {
  INPUT = 'input',
  TRANSFORM = 'transform',
  MODEL = 'model',
  CONDITION = 'condition',
  OUTPUT = 'output',
  CUSTOM = 'custom'
}

/**
 * File content types
 */
export enum FileContentType {
  TEXT_PLAIN = 'text/plain',
  TEXT_MARKDOWN = 'text/markdown',
  APPLICATION_PDF = 'application/pdf',
  APPLICATION_JSON = 'application/json',
  IMAGE_PNG = 'image/png',
  IMAGE_JPEG = 'image/jpeg',
  IMAGE_GIF = 'image/gif',
  APPLICATION_OCTET_STREAM = 'application/octet-stream'
}

// ===== CORE MODEL INTERFACES =====

/**
 * Base interface for all database entities
 */
export interface BaseEntity {
  /** Unique identifier */
  id: string;
  /** Creation timestamp (ISO 8601) */
  created_at: string;
  /** Last update timestamp (ISO 8601) */
  updated_at: string;
}

/**
 * User entity interface
 */
export interface User extends BaseEntity {
  /** Unique username */
  username: string;
  /** User's email address */
  email: string;
  /** User's full display name */
  full_name: string | null;
  /** Whether the user account is active */
  is_active: boolean;
  /** Whether the user's email is verified */
  is_verified: boolean;
  /** User's role in the system */
  role: UserRole;
  /** User preferences and settings */
  preferences: Record<string, any> | null;
}

/**
 * API Key entity interface
 */
export interface ApiKey extends BaseEntity {
  /** The actual API key value (only returned on creation) */
  key?: string;
  /** Human-readable name for the API key */
  name: string;
  /** ID of the user who owns this API key */
  user_id: string;
  /** When the API key expires (ISO 8601) */
  expires_at: string | null;
  /** When the API key was last used (ISO 8601) */
  last_used_at: string | null;
  /** Whether the API key is active */
  is_active: boolean;
  /** User who owns this API key */
  user?: User;
}

/**
 * Model capabilities interface
 */
export interface ModelCapabilities {
  /** Can generate text */
  text_generation?: boolean;
  /** Supports chat/conversation format */
  chat?: boolean;
  /** Has reasoning capabilities */
  reasoning?: boolean;
  /** Can generate code */
  code_generation?: boolean;
  /** Supports multiple input types (text, images, etc.) */
  multimodal?: boolean;
  /** Can analyze and interpret content */
  analysis?: boolean;
  /** Supports function calling */
  function_calling?: boolean;
  /** Supports streaming responses */
  streaming?: boolean;
}

/**
 * Model parameters interface
 */
export interface ModelParameters {
  /** Type categorization of the model */
  model_type: 'general' | 'code' | 'multimodal' | 'reasoning' | 'chat';
  /** API endpoint for external models */
  api_endpoint?: string;
  /** Whether this model requires Ollama */
  requires_ollama?: boolean;
  /** Maximum context length in tokens */
  max_context_length?: number;
  /** Additional model-specific parameters */
  [key: string]: any;
}

/**
 * Model pricing interface
 */
export interface ModelPricing {
  /** Cost per input token */
  input_tokens: number;
  /** Cost per output token */
  output_tokens: number;
  /** Currency code (e.g., 'USD') */
  currency: string;
  /** Number of tokens the price applies to (e.g., 1000) */
  per_tokens: number;
}

/**
 * Tag entity interface
 */
export interface Tag {
  /** Unique tag ID */
  id: number;
  /** Tag name */
  name: string;
  /** Tag description */
  description: string | null;
}

/**
 * AI Model entity interface
 */
export interface Model extends BaseEntity {
  /** Model identifier (e.g., 'gpt-4', 'claude-3-opus') */
  id: string;
  /** Human-readable model name */
  name: string;
  /** Model provider */
  provider: ModelProvider;
  /** Model description */
  description: string | null;
  /** Model version */
  version: string | null;
  /** Whether the model is active */
  is_active: boolean;
  /** Model-specific parameters */
  parameters: ModelParameters | null;
  /** Model capabilities */
  capabilities: ModelCapabilities | null;
  /** Maximum context window in tokens */
  context_window: number;
  /** Maximum output tokens */
  max_output_tokens: number | null;
  /** Pricing information */
  pricing: ModelPricing | null;
  /** Model size (e.g., '3.8 GB') */
  size: string | null;
  /** Current runtime status */
  status?: ModelStatus;
  /** Tags associated with this model */
  tags?: Tag[];
}

/**
 * Conversation entity interface
 */
export interface Conversation extends BaseEntity {
  /** Conversation title */
  title: string;
  /** ID of the model used in this conversation */
  model_id: string;
  /** System prompt for the conversation */
  system_prompt: string | null;
  /** Additional metadata */
  meta_data: Record<string, any> | null;
  /** The model used in this conversation */
  model?: Model;
  /** Messages in this conversation */
  messages?: Message[];
  /** Users participating in this conversation */
  users?: User[];
  /** Files attached to this conversation */
  files?: File[];
  /** Message threads in this conversation */
  threads?: MessageThread[];
  /** Number of messages in conversation (summary field) */
  message_count?: number;
}

/**
 * Message entity interface
 */
export interface Message extends BaseEntity {
  /** ID of the conversation this message belongs to */
  conversation_id: string;
  /** ID of the user who sent this message (null for system/assistant) */
  user_id: string | null;
  /** Role of the message sender */
  role: MessageRole;
  /** Message content */
  content: string;
  /** Additional metadata */
  meta_data: Record<string, any> | null;
  /** Number of tokens in this message */
  tokens: number | null;
  /** Cost of generating this message */
  cost: number | null;
  /** ID of the parent message (for threading) */
  parent_id: string | null;
  /** ID of the thread this message belongs to */
  thread_id: string | null;
  /** The conversation this message belongs to */
  conversation?: Conversation;
  /** The user who sent this message */
  user?: User;
  /** Files attached to this message */
  files?: MessageFile[];
  /** Replies to this message */
  replies?: Message[];
  /** The thread this message belongs to */
  thread?: MessageThread;
}

/**
 * File entity interface
 */
export interface File extends BaseEntity {
  /** Stored filename */
  filename: string;
  /** Original filename as uploaded */
  original_filename: string;
  /** MIME content type */
  content_type: string;
  /** File size in bytes */
  size: number;
  /** Storage path */
  path: string;
  /** ID of the user who uploaded this file */
  user_id: string;
  /** ID of the conversation this file belongs to */
  conversation_id: string | null;
  /** Additional metadata */
  meta_data: Record<string, any> | null;
  /** Whether the file is publicly accessible */
  is_public: boolean;
  /** Whether the file has been analyzed */
  analyzed: boolean;
  /** Results of AI analysis */
  analysis_result: Record<string, any> | null;
  /** Extracted text content */
  extracted_text: string | null;
  /** The user who uploaded this file */
  user?: User;
  /** The conversation this file belongs to */
  conversation?: Conversation;
  /** URL to access the file */
  url?: string;
}

/**
 * Message-File association interface
 */
export interface MessageFile {
  /** ID of the message */
  message_id: string;
  /** ID of the file */
  file_id: string;
  /** The associated message */
  message?: Message;
  /** The associated file */
  file?: File;
}

/**
 * Message Thread entity interface
 */
export interface MessageThread extends BaseEntity {
  /** ID of the conversation this thread belongs to */
  conversation_id: string;
  /** Thread title */
  title: string | null;
  /** ID of the user who created this thread */
  creator_id: string | null;
  /** ID of the parent thread (for nested threads) */
  parent_thread_id: string | null;
  /** Additional metadata */
  meta_data: Record<string, any> | null;
  /** The conversation this thread belongs to */
  conversation?: Conversation;
  /** Messages in this thread */
  messages?: Message[];
  /** The user who created this thread */
  creator?: User;
  /** Child threads */
  child_threads?: MessageThread[];
}

// ===== PIPELINE INTERFACES =====

/**
 * Pipeline retry configuration
 */
export interface PipelineRetryConfig {
  /** Maximum number of retry attempts */
  max_attempts: number;
  /** Delay between retries in milliseconds */
  delay_ms: number;
  /** Whether to use exponential backoff */
  exponential_backoff: boolean;
}

/**
 * Pipeline step interface
 */
export interface PipelineStep extends BaseEntity {
  /** Step name */
  name: string;
  /** Step type */
  type: PipelineStepType;
  /** Execution order */
  order: number;
  /** Step configuration */
  config: Record<string, any>;
  /** Step description */
  description: string | null;
  /** Input data mapping */
  input_mapping: Record<string, any> | null;
  /** Output data mapping */
  output_mapping: Record<string, any> | null;
  /** Whether the step is enabled */
  is_enabled: boolean;
  /** Timeout in seconds */
  timeout: number | null;
  /** Retry configuration */
  retry_config: PipelineRetryConfig | null;
  /** ID of the pipeline this step belongs to */
  pipeline_id: string;
}

/**
 * Pipeline interface
 */
export interface Pipeline extends BaseEntity {
  /** Pipeline name */
  name: string;
  /** Pipeline description */
  description: string | null;
  /** Whether the pipeline is publicly accessible */
  is_public: boolean;
  /** Pipeline tags */
  tags: string[] | null;
  /** Pipeline configuration */
  config: Record<string, any> | null;
  /** Whether the pipeline is active */
  is_active: boolean;
  /** Pipeline version */
  version: string;
  /** ID of the user who owns this pipeline */
  user_id: string;
  /** Steps in this pipeline */
  steps?: PipelineStep[];
}

/**
 * Pipeline execution interface
 */
export interface PipelineExecution extends BaseEntity {
  /** ID of the pipeline being executed */
  pipeline_id: string;
  /** Execution status */
  status: PipelineExecutionStatus;
  /** Input parameters */
  input_parameters: Record<string, any> | null;
  /** Execution result */
  result: Record<string, any> | null;
  /** Error message if execution failed */
  error_message: string | null;
  /** Execution start time */
  started_at: string | null;
  /** Execution completion time */
  completed_at: string | null;
  /** ID of the user who triggered this execution */
  user_id: string;
  /** The pipeline that was executed */
  pipeline?: Pipeline;
}

// ===== API REQUEST/RESPONSE TYPES =====

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T = any> {
  /** Whether the request was successful */
  success: boolean;
  /** Response data (if successful) */
  data?: T;
  /** Error message (if unsuccessful) */
  error?: string;
  /** Additional message */
  message?: string;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  /** Array of items */
  items: T[];
  /** Total number of items */
  total: number;
  /** Current page number */
  page: number;
  /** Items per page */
  per_page: number;
  /** Total number of pages */
  pages: number;
}

/**
 * Standard pagination parameters
 */
export interface PaginationParams {
  /** Number of items to skip */
  skip?: number;
  /** Maximum number of items to return */
  limit?: number;
}

// ===== AUTHENTICATION API TYPES =====

/**
 * User registration request
 */
export interface UserRegistrationRequest {
  /** Desired username */
  username: string;
  /** User's email address */
  email: string;
  /** User's full name */
  full_name?: string;
  /** Password */
  password: string;
  /** Password confirmation */
  password_confirm: string;
}

/**
 * Login request
 */
export interface LoginRequest {
  /** Username or email */
  username: string;
  /** Password */
  password: string;
}

/**
 * Authentication token response
 */
export interface AuthTokenResponse {
  /** JWT access token */
  access_token: string;
  /** Refresh token */
  refresh_token: string;
  /** Token type (usually 'bearer') */
  token_type: string;
  /** Token expiration timestamp */
  expires_at: string;
}

/**
 * Refresh token request
 */
export interface RefreshTokenRequest {
  /** Refresh token */
  refresh_token: string;
}

/**
 * Password change request
 */
export interface PasswordChangeRequest {
  /** Current password */
  current_password: string;
  /** New password */
  new_password: string;
  /** New password confirmation */
  new_password_confirm: string;
}

/**
 * Password reset request
 */
export interface PasswordResetRequest {
  /** Email address */
  email: string;
}

/**
 * User profile update request
 */
export interface UserProfileUpdateRequest {
  /** Updated email */
  email?: string;
  /** Updated full name */
  full_name?: string;
  /** Updated active status */
  is_active?: boolean;
  /** Updated preferences */
  preferences?: Record<string, any>;
}

// ===== API KEY TYPES =====

/**
 * API key creation request
 */
export interface ApiKeyCreateRequest {
  /** Human-readable name for the API key */
  name: string;
  /** Number of days until expiration (optional) */
  expires_in_days?: number;
}

/**
 * API key creation response
 */
export interface ApiKeyCreateResponse extends ApiKey {
  /** The actual API key value (only returned on creation) */
  key: string;
}

// ===== MODEL API TYPES =====

/**
 * Available models response
 */
export interface AvailableModelsResponse {
  /** Array of available models */
  models: Array<Model & {
    /** Current running status */
    status: ModelStatus;
    /** Whether the model is currently running */
    running: boolean;
    /** Additional runtime metadata */
    metadata?: Record<string, any>;
  }>;
  /** Whether this response was served from cache */
  cache_hit: boolean;
}

/**
 * Model action request (start/stop)
 */
export interface ModelActionRequest {
  /** ID of the model to act upon */
  model_id: string;
}

/**
 * Model action response
 */
export interface ModelActionResponse {
  /** Success/error message */
  message: string;
  /** ID of the model */
  model_id: string;
  /** Current status after action */
  status: ModelStatus;
}

// ===== CHAT API TYPES =====

/**
 * Conversation creation request
 */
export interface ConversationCreateRequest {
  /** ID of the model to use */
  model_id: string;
  /** Conversation title */
  title: string;
  /** System prompt (optional) */
  system_prompt?: string;
}

/**
 * Chat completion request
 */
export interface ChatCompletionRequest {
  /** ID of the model to use */
  model_id: string;
  /** User prompt */
  prompt: string;
  /** System prompt (optional) */
  system_prompt?: string;
  /** Model-specific options */
  options?: Record<string, any>;
  /** Whether to stream the response */
  stream: boolean;
  /** ID of existing conversation (optional) */
  conversation_id?: string;
  /** Temperature for response generation */
  temperature?: number;
  /** Maximum tokens to generate */
  max_tokens?: number;
}

/**
 * Token usage information
 */
export interface TokenUsage {
  /** Number of tokens in the prompt */
  prompt_tokens: number;
  /** Number of tokens in the completion */
  completion_tokens: number;
  /** Total tokens used */
  total_tokens: number;
  /** Cost breakdown */
  costs?: {
    /** Cost for input tokens */
    input_cost: number;
    /** Cost for output tokens */
    output_cost: number;
    /** Total cost */
    total_cost: number;
  };
}

/**
 * Chat completion response
 */
export interface ChatCompletionResponse {
  /** Response ID */
  id: string;
  /** Model used */
  model: string;
  /** Creation timestamp */
  created: number;
  /** Generated content */
  content: string;
  /** Processing time in milliseconds */
  processing_time: number;
  /** Token usage information */
  usage: TokenUsage;
  /** ID of the conversation (if applicable) */
  conversation_id?: string;
}

/**
 * Conversation list query parameters
 */
export interface ConversationListParams extends PaginationParams {
  /** Filter by model ID */
  model_id?: string;
}

/**
 * Conversation summary for list responses
 */
export interface ConversationSummary {
  /** Conversation ID */
  id: string;
  /** Conversation title */
  title: string;
  /** Model ID */
  model_id: string;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
  /** Number of messages */
  message_count: number;
}

/**
 * Conversations list response
 */
export interface ConversationsListResponse {
  /** Array of conversation summaries */
  conversations: ConversationSummary[];
}

// ===== FILE API TYPES =====

/**
 * File upload response
 */
export interface FileUploadResponse extends File {
  /** URL to access the file */
  url: string;
}

/**
 * File upload request metadata
 */
export interface FileUploadMetadata {
  /** ID of conversation to associate with */
  conversation_id?: string;
  /** File description */
  description?: string;
  /** ID of message to associate with */
  message_id?: string;
}

/**
 * File info response
 */
export interface FileInfoResponse {
  /** Allowed file types */
  allowed_types: string[];
  /** Maximum file size in bytes */
  max_file_size: number;
  /** Maximum file size in MB */
  max_file_size_mb: number;
}

/**
 * File list query parameters
 */
export interface FileListParams extends PaginationParams {
  /** Filter by conversation ID */
  conversation_id?: string;
}

// ===== PIPELINE API TYPES =====

/**
 * Pipeline creation request
 */
export interface PipelineCreateRequest {
  /** Pipeline name */
  name: string;
  /** Pipeline description */
  description?: string;
  /** Whether the pipeline is public */
  is_public: boolean;
  /** Pipeline tags */
  tags?: string[];
  /** Pipeline configuration */
  config?: Record<string, any>;
}

/**
 * Pipeline update request
 */
export interface PipelineUpdateRequest {
  /** Updated name */
  name?: string;
  /** Updated description */
  description?: string;
  /** Updated public status */
  is_public?: boolean;
  /** Updated tags */
  tags?: string[];
  /** Updated configuration */
  config?: Record<string, any>;
  /** Updated active status */
  is_active?: boolean;
  /** Updated version */
  version?: string;
}

/**
 * Pipeline list query parameters
 */
export interface PipelineListParams extends PaginationParams {
  /** Filter by tags */
  tags?: string[];
  /** Include public pipelines */
  include_public?: boolean;
}

/**
 * Pipeline step creation request
 */
export interface PipelineStepCreateRequest {
  /** Step name */
  name: string;
  /** Step type */
  type: PipelineStepType;
  /** Execution order */
  order: number;
  /** Step configuration */
  config: Record<string, any>;
  /** Step description */
  description?: string;
  /** Input data mapping */
  input_mapping?: Record<string, any>;
  /** Output data mapping */
  output_mapping?: Record<string, any>;
  /** Whether the step is enabled */
  is_enabled: boolean;
  /** Timeout in seconds */
  timeout?: number;
  /** Retry configuration */
  retry_config?: PipelineRetryConfig;
}

/**
 * Pipeline step update request
 */
export type PipelineStepUpdateRequest = Partial<PipelineStepCreateRequest>;

/**
 * Pipeline step reorder request
 */
export interface PipelineStepReorderRequest {
  /** Array of step reorder instructions */
  steps: Array<{
    /** Step ID */
    step_id: string;
    /** New order */
    order: number;
  }>;
}

/**
 * Pipeline execution request
 */
export interface PipelineExecutionRequest {
  /** Input parameters for the pipeline */
  input_parameters?: Record<string, any>;
}

/**
 * Pipeline execution list query parameters
 */
export interface PipelineExecutionListParams extends PaginationParams {
  /** Filter by pipeline ID */
  pipeline_id?: string;
  /** Filter by status */
  status?: PipelineExecutionStatus;
  /** Include step executions */
  include_step_executions?: boolean;
}

// ===== HEALTH CHECK TYPES =====

/**
 * Health check response
 */
export interface HealthCheckResponse {
  /** Overall system status */
  status: 'healthy' | 'unhealthy';
  /** Ollama service status */
  ollama_status: 'available' | 'unavailable' | 'unknown';
}

// ===== WEBSOCKET TYPES =====

/**
 * WebSocket message base interface
 */
export interface WebSocketMessage {
  /** Message type */
  type: string;
  /** Message payload */
  payload?: any;
  /** Message timestamp */
  timestamp: string;
  /** Message ID */
  id?: string;
}

/**
 * Model status update WebSocket message
 */
export interface ModelStatusUpdateMessage extends WebSocketMessage {
  type: 'model_status_update';
  payload: {
    /** Model ID */
    model_id: string;
    /** New status */
    status: ModelStatus;
    /** Additional metadata */
    metadata?: Record<string, any>;
  };
}

// ===== ERROR TYPES =====

/**
 * API error response
 */
export interface ApiErrorResponse {
  /** Error message */
  detail: string;
  /** Error code */
  code?: string;
  /** Field that caused the error */
  field?: string;
}

/**
 * Validation error details
 */
export interface ValidationError {
  /** Field location */
  loc: (string | number)[];
  /** Error message */
  msg: string;
  /** Error type */
  type: string;
}

/**
 * Validation error response
 */
export interface ValidationErrorResponse {
  /** Array of validation errors */
  detail: ValidationError[];
}

// ===== UTILITY TYPES =====

/**
 * Make specific properties optional
 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * Make specific properties required
 */
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

/**
 * Extract the data type from an ApiResponse
 */
export type ExtractApiData<T> = T extends ApiResponse<infer U> ? U : never;

/**
 * Create request type for entity creation
 */
export type CreateRequest<T extends BaseEntity> = Omit<T, keyof BaseEntity>;

/**
 * Create request type for entity updates
 */
export type UpdateRequest<T extends BaseEntity> = Partial<Omit<T, keyof BaseEntity>>;

// ===== TYPE GUARDS =====

/**
 * Type guard for User objects
 */
export function isUser(obj: any): obj is User {
  return obj && typeof obj === 'object' && 
         typeof obj.id === 'string' && 
         typeof obj.username === 'string' && 
         typeof obj.email === 'string';
}

/**
 * Type guard for Model objects
 */
export function isModel(obj: any): obj is Model {
  return obj && typeof obj === 'object' && 
         typeof obj.id === 'string' && 
         typeof obj.name === 'string' && 
         typeof obj.provider === 'string';
}

/**
 * Type guard for Conversation objects
 */
export function isConversation(obj: any): obj is Conversation {
  return obj && typeof obj === 'object' && 
         typeof obj.id === 'string' && 
         typeof obj.title === 'string' && 
         typeof obj.model_id === 'string';
}

/**
 * Type guard for Message objects
 */
export function isMessage(obj: any): obj is Message {
  return obj && typeof obj === 'object' && 
         typeof obj.id === 'string' && 
         typeof obj.conversation_id === 'string' && 
         typeof obj.role === 'string' && 
         typeof obj.content === 'string';
}

/**
 * Type guard for File objects
 */
export function isFile(obj: any): obj is File {
  return obj && typeof obj === 'object' && 
         typeof obj.id === 'string' && 
         typeof obj.filename === 'string' && 
         typeof obj.content_type === 'string';
}

/**
 * Type guard for ApiResponse objects
 */
export function isApiResponse<T>(obj: any): obj is ApiResponse<T> {
  return obj && typeof obj === 'object' && 
         typeof obj.success === 'boolean';
}

/**
 * Type guard for successful ApiResponse
 */
export function isSuccessfulApiResponse<T>(obj: ApiResponse<T>): obj is ApiResponse<T> & { success: true; data: T } {
  return obj.success === true && obj.data !== undefined;
}

/**
 * Type guard for error ApiResponse
 */
export function isErrorApiResponse<T>(obj: ApiResponse<T>): obj is ApiResponse<T> & { success: false; error: string } {
  return obj.success === false && typeof obj.error === 'string';
}

/**
 * Type guard for PaginatedResponse
 */
export function isPaginatedResponse<T>(obj: any): obj is PaginatedResponse<T> {
  return obj && typeof obj === 'object' && 
         Array.isArray(obj.items) && 
         typeof obj.total === 'number' && 
         typeof obj.page === 'number';
}

// All types are already exported at their definition points