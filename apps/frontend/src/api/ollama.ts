/**
 * Ollama API client for Web+ Application
 * Handles model management and API calls with authentication
 */

import { safeFetch } from '@/lib/shared-utils';
import { ApiResponse, Model } from '@/types';

/**
 * Enhanced version of safeFetch that adds authentication headers
 */
export const authSafeFetch = async <T = any>(
  url: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  // Get the token from localStorage
  const authTokens = localStorage.getItem('auth_tokens');
  let token: string | null = null;
  
  if (authTokens) {
    try {
      const parsed = JSON.parse(authTokens);
      token = parsed.access_token;
    } catch (error) {
      console.warn('Failed to parse auth tokens:', error);
    }
  }
  
  // Merge headers with auth token if available
  const headers: HeadersInit = {
    ...options.headers,
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
  
  return safeFetch<T>(url, { ...options, headers });
};

/**
 * Model management API responses
 */
interface ModelsResponse {
  models: Model[];
  cache_hit: boolean;
}

interface ModelActionResponse {
  success: boolean;
  message: string;
  model_id: string;
}

/**
 * Fetch all available models
 */
export const fetchModels = async (): Promise<ModelsResponse> => {
  const result = await authSafeFetch<ModelsResponse>('/api/models/available');
  
  if (result.success && result.data) {
    return result.data;
  } else {
    console.error('Error fetching models:', result.error);
    throw new Error(`Failed to fetch models: ${result.error}`);
  }
};

/**
 * Start a specific model
 */
export const startModel = async (modelId: string): Promise<ModelActionResponse> => {
  const result = await authSafeFetch<ModelActionResponse>('/api/models/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId })
  });
  
  if (result.success && result.data) {
    return result.data;
  } else {
    console.error(`Error starting model ${modelId}:`, result.error);
    throw new Error(`Failed to start model: ${result.error}`);
  }
};

/**
 * Stop a specific model
 */
export const stopModel = async (modelId: string): Promise<ModelActionResponse> => {
  const result = await authSafeFetch<ModelActionResponse>('/api/models/stop', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId })
  });
  
  if (result.success && result.data) {
    return result.data;
  } else {
    console.error(`Error stopping model ${modelId}:`, result.error);
    throw new Error(`Failed to stop model: ${result.error}`);
  }
};

/**
 * API client object with organized methods
 */
export const api = {
  models: {
    getAll: fetchModels,
    start: startModel,
    stop: stopModel
  }
};

export default api;