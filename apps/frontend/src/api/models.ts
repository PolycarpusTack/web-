// src/api/models.ts
import { authSafeFetch } from "./ollama";
import { APIResponse } from "@/lib/shared-utils";

export interface Model {
  id: string;
  name: string;
  description?: string;
  type: string;
  status: 'available' | 'running' | 'stopped' | 'error';
  size?: number;
  capabilities?: string[];
  created_at: string;
  updated_at?: string;
}

export interface ModelsResponse {
  models: Model[];
}

export const getModels = async (): Promise<APIResponse<Model[]>> => {
  return authSafeFetch<Model[]>('/api/models');
};

export const getModel = async (modelId: string): Promise<APIResponse<Model>> => {
  return authSafeFetch<Model>(`/api/models/${modelId}`);
};

export const startModel = async (modelId: string): Promise<APIResponse<{message: string}>> => {
  return authSafeFetch<{message: string}>(`/api/models/${modelId}/start`, {
    method: 'POST'
  });
};

export const stopModel = async (modelId: string): Promise<APIResponse<{message: string}>> => {
  return authSafeFetch<{message: string}>(`/api/models/${modelId}/stop`, {
    method: 'POST'
  });
};