// src/api/files.ts
import { authSafeFetch } from "./ollama";
import { APIResponse } from "@/lib/shared-utils";

// File Types
export interface FileInfo {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size: number;
  created_at: string;
  url: string;
  is_public: boolean;
  metadata?: Record<string, unknown>;
  analyzed?: boolean;
  analysis_result?: Record<string, unknown>;
  extracted_text?: string;
}

export interface FileUploadResponse {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size: number;
  created_at: string;
  url: string;
  is_public: boolean;
  metadata?: Record<string, unknown>;
  analyzed?: boolean;
  analysis_result?: Record<string, unknown>;
  extracted_text?: string;
}

export interface FileListResponse {
  files: FileInfo[];
}

// Re-export for backward compatibility
export type { FileInfo as File };

// File API
export const filesApi = {
  // Upload a single file
  uploadFile: async (
    file: File,
    conversationId?: string,
    description?: string
  ): Promise<APIResponse<FileUploadResponse>> => {
    const formData = new FormData();
    formData.append("file", file as unknown as Blob);
    
    if (conversationId) {
      formData.append("conversation_id", conversationId);
    }
    
    if (description) {
      formData.append("description", description);
    }
    
    return authSafeFetch<FileUploadResponse>(
      "/api/files/upload",
      {
        method: "POST",
        body: formData,
      }
    );
  },
  
  // Upload multiple files to a conversation
  uploadFilesToConversation: async (
    files: File[],
    conversationId: string,
    messageId?: string
  ): Promise<APIResponse<FileUploadResponse[]>> => {
    const formData = new FormData();
    
    // Append each file
    files.forEach(file => {
      formData.append("files", file as unknown as Blob);
    });
    
    // Add message ID if provided
    if (messageId) {
      formData.append("message_id", messageId);
    }
    
    return authSafeFetch<FileUploadResponse[]>(
      `/api/files/upload/conversation/${conversationId}`,
      {
        method: "POST",
        body: formData,
      }
    );
  },
  
  // Get all files for the current user
  getUserFiles: async (conversationId?: string): Promise<APIResponse<FileListResponse>> => {
    const queryParams = conversationId ? `?conversation_id=${conversationId}` : '';
    return authSafeFetch<FileListResponse>(
      `/api/files${queryParams}`
    );
  },
  
  // Get a specific file by ID
  getFileById: async (fileId: string): Promise<Response> => {
    const response = await fetch(`/api/files/${fileId}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`);
    }
    
    return response;
  },
  
  // Get file info but not the actual file
  getFileInfo: async (fileId: string): Promise<APIResponse<FileInfo>> => {
    return authSafeFetch<FileInfo>(
      `/api/files/${fileId}/info`
    );
  },
  
  // Delete a file
  deleteFile: async (fileId: string): Promise<APIResponse<{message: string}>> => {
    return authSafeFetch<{message: string}>(
      `/api/files/${fileId}`,
      {
        method: "DELETE",
      }
    );
  },
  
  // Request file analysis
  analyzeFile: async (fileId: string): Promise<APIResponse<FileInfo>> => {
    return authSafeFetch<FileInfo>(
      `/api/files/${fileId}/analyze`,
      {
        method: "POST"
      }
    );
  },
  
  // Get file analysis results
  getFileAnalysis: async (fileId: string): Promise<APIResponse<FileInfo>> => {
    return authSafeFetch<FileInfo>(
      `/api/files/${fileId}/analysis`
    );
  },
  
  // Get files attached to a message
  getMessageFiles: async (messageId: string): Promise<APIResponse<FileListResponse>> => {
    return authSafeFetch<FileListResponse>(
      `/api/files/message/${messageId}`
    );
  },
  
  // Get file upload info (allowed types, max size)
  getUploadInfo: async (): Promise<APIResponse<{
    allowed_types: string[];
    max_file_size: number;
    max_file_size_mb: number;
  }>> => {
    return authSafeFetch(
      `/api/files/info`
    );
  }
};

// Helper to get a file URL directly
export const getFileUrl = (fileId: string): string => {
  return `/api/files/${fileId}`;
};

// Format file size in human-readable format
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Check if a file is an image
export const isImageFile = (contentType: string): boolean => {
  return contentType.startsWith('image/');
};

// Get a file icon based on its type
export const getFileIcon = (contentType: string): string => {
  if (contentType.startsWith('image/')) {
    return 'image';
  } else if (contentType === 'application/pdf') {
    return 'file-pdf';
  } else if (
    contentType === 'application/msword' || 
    contentType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ) {
    return 'file-text';
  } else if (contentType === 'text/plain' || contentType === 'text/markdown') {
    return 'file-text';
  } else {
    return 'file';
  }
};