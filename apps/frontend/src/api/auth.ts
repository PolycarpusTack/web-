// src/api/auth.ts
import { APIResponse, safeFetch } from "@/lib/shared-utils";

// Auth API types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegistrationRequest {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  full_name?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
}

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

export interface RequestPasswordResetRequest {
  email: string;
}

// Auth API client
export const authApi = {
  // Login
  login: (data: LoginRequest): Promise<APIResponse<AuthTokens>> => {
    return safeFetch<AuthTokens>(
      '/api/auth/login',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }
    );
  },
  
  // Register
  register: (data: RegistrationRequest): Promise<APIResponse<UserInfo>> => {
    return safeFetch<UserInfo>(
      '/api/auth/register',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }
    );
  },
  
  // Refresh tokens
  refreshTokens: (refreshToken: string): Promise<APIResponse<AuthTokens>> => {
    return safeFetch<AuthTokens>(
      '/api/auth/refresh',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      }
    );
  },
  
  // Get current user info
  getCurrentUser: (accessToken: string): Promise<APIResponse<UserInfo>> => {
    return safeFetch<UserInfo>(
      '/api/auth/me',
      {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    );
  },
  
  // Update user profile
  updateProfile: (accessToken: string, data: Partial<UserInfo>): Promise<APIResponse<UserInfo>> => {
    return safeFetch<UserInfo>(
      '/api/auth/me',
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(data)
      }
    );
  },
  
  // Change password
  changePassword: (accessToken: string, data: ChangePasswordRequest): Promise<APIResponse<void>> => {
    return safeFetch<void>(
      '/api/auth/change-password',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(data)
      }
    );
  },
  
  // Request password reset
  requestPasswordReset: (data: RequestPasswordResetRequest): Promise<APIResponse<void>> => {
    return safeFetch<void>(
      '/api/auth/request-password-reset',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }
    );
  }
};