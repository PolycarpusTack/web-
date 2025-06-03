/**
 * Centralized API module for Web+ Application
 * This module consolidates all API calls using the centralized ApiClient
 */

import { apiClient } from '@/lib/api-client';
import type {
  // Auth types
  LoginRequest,
  UserRegistrationRequest,
  AuthTokenResponse,
  RefreshTokenRequest,
  PasswordChangeRequest,
  UserProfileUpdateRequest,
  ApiKeyCreateRequest,
  ApiKeyCreateResponse,
  ApiKey,
  
  // Model types
  AvailableModelsResponse,
  ModelActionRequest,
  ModelActionResponse,
  Model,
  
  // Conversation types
  ConversationCreateRequest,
  ChatCompletionRequest,
  ChatCompletionResponse,
  Conversation,
  Message,
  ConversationListParams,
  ConversationsListResponse,
  
  // File types
  FileUploadResponse,
  FileInfoResponse,
  FileListParams,
  File as FileInfo,
  
  // Pipeline types
  Pipeline,
  PipelineCreateRequest,
  PipelineUpdateRequest,
  PipelineListParams,
  PipelineStep,
  PipelineStepCreateRequest,
  PipelineStepUpdateRequest,
  PipelineStepReorderRequest,
  PipelineExecutionRequest,
  PipelineExecution,
  PipelineExecutionListParams,
  
  // Common types
  ApiResponse,
  PaginatedResponse,
  User,
  HealthCheckResponse
} from '@/types/api-definitions';

// Re-export the apiClient for direct access if needed
export { apiClient };

/**
 * Authentication API
 */
export const authApi = {
  login: (data: LoginRequest) => 
    apiClient.post<ApiResponse<AuthTokenResponse>>('/auth/login', data),
    
  register: (data: UserRegistrationRequest) => 
    apiClient.post<ApiResponse<AuthTokenResponse>>('/auth/register', data),
    
  refresh: (data: RefreshTokenRequest) => 
    apiClient.post<ApiResponse<AuthTokenResponse>>('/auth/refresh', data),
    
  logout: () => 
    apiClient.post<ApiResponse<void>>('/auth/logout'),
    
  getCurrentUser: () => 
    apiClient.get<ApiResponse<User>>('/auth/me'),
    
  updateProfile: (data: UserProfileUpdateRequest) => 
    apiClient.put<ApiResponse<User>>('/auth/profile', data),
    
  changePassword: (data: PasswordChangeRequest) => 
    apiClient.post<ApiResponse<void>>('/auth/change-password', data),
    
  // API Keys
  createApiKey: (data: ApiKeyCreateRequest) => 
    apiClient.post<ApiResponse<ApiKeyCreateResponse>>('/auth/api-keys', data),
    
  listApiKeys: () => 
    apiClient.get<ApiResponse<ApiKey[]>>('/auth/api-keys'),
    
  revokeApiKey: (id: string) => 
    apiClient.delete<ApiResponse<void>>(`/auth/api-keys/${id}`)
};

/**
 * Models API
 */
export const modelsApi = {
  getAvailable: () => 
    apiClient.get<AvailableModelsResponse>('/models/available'),
    
  getById: (id: string) => 
    apiClient.get<ApiResponse<Model>>(`/models/${id}`),
    
  start: (data: ModelActionRequest) => 
    apiClient.post<ModelActionResponse>('/models/start', data),
    
  stop: (data: ModelActionRequest) => 
    apiClient.post<ModelActionResponse>('/models/stop', data),
    
  getStatus: (id: string) => 
    apiClient.get<ApiResponse<{ status: string }>>(`/models/${id}/status`)
};

/**
 * Conversations API
 */
export const conversationsApi = {
  create: (data: ConversationCreateRequest) => 
    apiClient.post<ApiResponse<Conversation>>('/conversations', data),
    
  list: (params?: ConversationListParams) => {
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const url = queryString ? `/conversations?${queryString}` : '/conversations';
    return apiClient.get<ConversationsListResponse>(url);
  },
    
  getById: (id: string) => 
    apiClient.get<ApiResponse<Conversation>>(`/conversations/${id}`),
    
  update: (id: string, data: Partial<Conversation>) => 
    apiClient.patch<ApiResponse<Conversation>>(`/conversations/${id}`, data),
    
  delete: (id: string) => 
    apiClient.delete<ApiResponse<void>>(`/conversations/${id}`),
    
  sendMessage: (data: ChatCompletionRequest) => 
    apiClient.post<ChatCompletionResponse>('/chat/completions', data)
};

/**
 * Files API
 */
export const filesApi = {
  upload: (file: File, conversationId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }
    return apiClient.post<ApiResponse<FileUploadResponse>>('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
    
  uploadMultiple: (files: File[], conversationId?: string) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }
    return apiClient.post<ApiResponse<FileUploadResponse[]>>('/files/upload-multiple', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
    
  list: (params?: FileListParams) => {
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const url = queryString ? `/files?${queryString}` : '/files';
    return apiClient.get<ApiResponse<PaginatedResponse<FileInfo>>>(url);
  },
    
  getById: (id: string) => 
    apiClient.get<ApiResponse<FileInfo>>(`/files/${id}`),
    
  delete: (id: string) => 
    apiClient.delete<ApiResponse<void>>(`/files/${id}`),
    
  getInfo: () => 
    apiClient.get<ApiResponse<FileInfoResponse>>('/files/info'),
    
  analyze: (id: string) => 
    apiClient.post<ApiResponse<FileInfo>>(`/files/${id}/analyze`)
};

/**
 * Pipelines API
 */
export const pipelinesApi = {
  create: (data: PipelineCreateRequest) => 
    apiClient.post<ApiResponse<Pipeline>>('/pipelines', data),
    
  list: (params?: PipelineListParams) => {
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const url = queryString ? `/pipelines?${queryString}` : '/pipelines';
    return apiClient.get<ApiResponse<PaginatedResponse<Pipeline>>>(url);
  },
    
  getById: (id: string) => 
    apiClient.get<ApiResponse<Pipeline>>(`/pipelines/${id}`),
    
  update: (id: string, data: PipelineUpdateRequest) => 
    apiClient.patch<ApiResponse<Pipeline>>(`/pipelines/${id}`, data),
    
  delete: (id: string) => 
    apiClient.delete<ApiResponse<void>>(`/pipelines/${id}`),
    
  // Pipeline Steps
  createStep: (pipelineId: string, data: PipelineStepCreateRequest) => 
    apiClient.post<ApiResponse<PipelineStep>>(`/pipelines/${pipelineId}/steps`, data),
    
  updateStep: (pipelineId: string, stepId: string, data: PipelineStepUpdateRequest) => 
    apiClient.patch<ApiResponse<PipelineStep>>(`/pipelines/${pipelineId}/steps/${stepId}`, data),
    
  deleteStep: (pipelineId: string, stepId: string) => 
    apiClient.delete<ApiResponse<void>>(`/pipelines/${pipelineId}/steps/${stepId}`),
    
  reorderSteps: (pipelineId: string, data: PipelineStepReorderRequest) => 
    apiClient.post<ApiResponse<PipelineStep[]>>(`/pipelines/${pipelineId}/steps/reorder`, data),
    
  // Pipeline Execution
  execute: (pipelineId: string, data: PipelineExecutionRequest) => 
    apiClient.post<ApiResponse<PipelineExecution>>(`/pipelines/${pipelineId}/execute`, data),
    
  listExecutions: (params?: PipelineExecutionListParams) => {
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const url = queryString ? `/pipeline-executions?${queryString}` : '/pipeline-executions';
    return apiClient.get<ApiResponse<PaginatedResponse<PipelineExecution>>>(url);
  },
    
  getExecution: (executionId: string) => 
    apiClient.get<ApiResponse<PipelineExecution>>(`/pipeline-executions/${executionId}`)
};

/**
 * System API
 */
export const systemApi = {
  health: () => 
    apiClient.get<HealthCheckResponse>('/health'),
    
  version: () => 
    apiClient.get<ApiResponse<{ version: string, build: string }>>('/version')
};

// Export all APIs as a single object for convenience
export const api = {
  auth: authApi,
  models: modelsApi,
  conversations: conversationsApi,
  files: filesApi,
  pipelines: pipelinesApi,
  system: systemApi
};