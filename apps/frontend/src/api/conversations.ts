// src/api/conversations.ts
import type {
  Conversation,
  Message,
  MessageThread,
  ConversationCreateRequest,
  ChatCompletionRequest,
  ChatCompletionResponse,
  ConversationsListResponse,
  ApiResponse
} from '@/types/api-definitions';
import { api } from '@/api';

// Re-export types for backward compatibility
export type { 
  Conversation, 
  Message, 
  MessageThread,
  ChatCompletionRequest,
  ChatCompletionResponse 
};

// Alias for backward compatibility
export type ConversationListResponse = ConversationsListResponse;
export type CreateConversationRequest = ConversationCreateRequest;

// Additional types not in api-definitions
export interface CreateThreadRequest {
  conversation_id: string;
  title?: string;
  parent_thread_id?: string;
}

export interface ThreadListResponse {
  threads: MessageThread[];
}

// Import the apiClient directly for low-level access
import { apiClient } from '@/lib/api-client';

// Conversations API - wraps the centralized API client for backward compatibility
export const conversationsApi = {
  // Get all conversations
  getAll: async (modelId?: string, _signal?: AbortSignal): Promise<ApiResponse<ConversationListResponse>> => {
    const params = modelId ? { model_id: modelId } : undefined;
    const response = await api.conversations.list(params);
    // The API returns ConversationsListResponse directly, wrap it in ApiResponse
    return {
      success: true,
      data: response as unknown as ConversationListResponse
    };
  },
  
  // Get conversation by ID
  getById: async (id: string, _signal?: AbortSignal): Promise<ApiResponse<Conversation>> => {
    return api.conversations.getById(id);
  },
  
  // Create a new conversation
  create: async (data: CreateConversationRequest, _signal?: AbortSignal): Promise<ApiResponse<Conversation>> => {
    return api.conversations.create(data);
  },
  
  // Send a message (chat completion)
  sendMessage: async (data: ChatCompletionRequest, _signal?: AbortSignal): Promise<ApiResponse<ChatCompletionResponse>> => {
    const response = await api.conversations.sendMessage(data);
    // The API returns ChatCompletionResponse directly, wrap it in ApiResponse
    return {
      success: true,
      data: response as unknown as ChatCompletionResponse
    };
  },

  // Thread related API endpoints
  threads: {
    // Create a new thread
    create: async (data: CreateThreadRequest, _signal?: AbortSignal): Promise<ApiResponse<MessageThread>> => {
      return apiClient.post<ApiResponse<MessageThread>>('/chat/threads', data);
    },

    // Get thread by ID
    getById: async (id: string, _signal?: AbortSignal): Promise<ApiResponse<MessageThread>> => {
      return apiClient.get<ApiResponse<MessageThread>>(`/chat/threads/${id}`);
    },

    // Get threads for a conversation
    getByConversation: async (conversationId: string, _signal?: AbortSignal): Promise<ApiResponse<ThreadListResponse>> => {
      return apiClient.get<ApiResponse<ThreadListResponse>>(`/chat/conversations/${conversationId}/threads`);
    },

    // Send a message to a thread
    sendMessage: async (threadId: string, data: ChatCompletionRequest, _signal?: AbortSignal): Promise<ApiResponse<ChatCompletionResponse>> => {
      return apiClient.post<ApiResponse<ChatCompletionResponse>>(`/chat/threads/${threadId}/completions`, data);
    }
  }
};