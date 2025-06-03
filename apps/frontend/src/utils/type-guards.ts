/**
 * Type guard utilities for Web+ Application
 * These functions help with runtime type checking and type narrowing
 */

import type {
  User,
  Model,
  Conversation,
  Message,
  File,
  Pipeline,
  PipelineStep,
  ApiResponse,
  PaginatedResponse,
  MessageRole,
  ModelStatus,
  PipelineExecutionStatus,
  UserRole
} from '@/types/api-definitions';

/**
 * Type guard for User objects
 */
export function isUser(obj: unknown): obj is User {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'username' in obj &&
    'email' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).username === 'string' &&
    typeof (obj as any).email === 'string'
  );
}

/**
 * Type guard for Model objects
 */
export function isModel(obj: unknown): obj is Model {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'name' in obj &&
    'provider' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).name === 'string' &&
    typeof (obj as any).provider === 'string'
  );
}

/**
 * Type guard for Conversation objects
 */
export function isConversation(obj: unknown): obj is Conversation {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'title' in obj &&
    'model_id' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).title === 'string' &&
    typeof (obj as any).model_id === 'string'
  );
}

/**
 * Type guard for Message objects
 */
export function isMessage(obj: unknown): obj is Message {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'conversation_id' in obj &&
    'role' in obj &&
    'content' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).conversation_id === 'string' &&
    typeof (obj as any).role === 'string' &&
    typeof (obj as any).content === 'string'
  );
}

/**
 * Type guard for File objects
 */
export function isFile(obj: unknown): obj is File {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'filename' in obj &&
    'content_type' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).filename === 'string' &&
    typeof (obj as any).content_type === 'string'
  );
}

/**
 * Type guard for Pipeline objects
 */
export function isPipeline(obj: unknown): obj is Pipeline {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'name' in obj &&
    'user_id' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).name === 'string' &&
    typeof (obj as any).user_id === 'string'
  );
}

/**
 * Type guard for PipelineStep objects
 */
export function isPipelineStep(obj: unknown): obj is PipelineStep {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'name' in obj &&
    'type' in obj &&
    'order' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).name === 'string' &&
    typeof (obj as any).type === 'string' &&
    typeof (obj as any).order === 'number'
  );
}

/**
 * Type guard for ApiResponse objects
 */
export function isApiResponse<T = unknown>(obj: unknown): obj is ApiResponse<T> {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'success' in obj &&
    typeof (obj as any).success === 'boolean'
  );
}

/**
 * Type guard for successful ApiResponse
 */
export function isSuccessfulApiResponse<T>(
  obj: ApiResponse<T>
): obj is ApiResponse<T> & { success: true; data: T } {
  return obj.success === true && 'data' in obj;
}

/**
 * Type guard for error ApiResponse
 */
export function isErrorApiResponse<T>(
  obj: ApiResponse<T>
): obj is ApiResponse<T> & { success: false; error: string } {
  return obj.success === false && 'error' in obj && typeof obj.error === 'string';
}

/**
 * Type guard for PaginatedResponse
 */
export function isPaginatedResponse<T>(obj: unknown): obj is PaginatedResponse<T> {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'items' in obj &&
    'total' in obj &&
    'page' in obj &&
    Array.isArray((obj as any).items) &&
    typeof (obj as any).total === 'number' &&
    typeof (obj as any).page === 'number'
  );
}

/**
 * Type guard for MessageRole enum
 */
export function isMessageRole(value: unknown): value is MessageRole {
  return (
    typeof value === 'string' &&
    ['system', 'user', 'assistant'].includes(value)
  );
}

/**
 * Type guard for ModelStatus enum
 */
export function isModelStatus(value: unknown): value is ModelStatus {
  return (
    typeof value === 'string' &&
    ['running', 'stopped', 'loading', 'error', 'unknown'].includes(value)
  );
}

/**
 * Type guard for PipelineExecutionStatus enum
 */
export function isPipelineExecutionStatus(value: unknown): value is PipelineExecutionStatus {
  return (
    typeof value === 'string' &&
    ['pending', 'running', 'completed', 'failed', 'cancelled'].includes(value)
  );
}

/**
 * Type guard for UserRole enum
 */
export function isUserRole(value: unknown): value is UserRole {
  return (
    typeof value === 'string' &&
    ['user', 'admin', 'developer', 'moderator'].includes(value)
  );
}

/**
 * Type guard for arrays of a specific type
 */
export function isArrayOf<T>(
  arr: unknown,
  itemGuard: (item: unknown) => item is T
): arr is T[] {
  return Array.isArray(arr) && arr.every(itemGuard);
}

/**
 * Type guard for nullable values
 */
export function isNullable<T>(
  value: T | null | undefined,
  guard: (value: unknown) => value is T
): value is T | null {
  return value === null || guard(value);
}

/**
 * Type guard for optional values
 */
export function isOptional<T>(
  value: T | undefined,
  guard: (value: unknown) => value is T
): value is T | undefined {
  return value === undefined || guard(value);
}

/**
 * Assert that a value is not null or undefined
 */
export function assertDefined<T>(
  value: T | null | undefined,
  message?: string
): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error(message || 'Value is null or undefined');
  }
}

/**
 * Assert that a value matches a type guard
 */
export function assertType<T>(
  value: unknown,
  guard: (value: unknown) => value is T,
  message?: string
): asserts value is T {
  if (!guard(value)) {
    throw new Error(message || 'Type assertion failed');
  }
}