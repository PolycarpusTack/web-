# Frontend Authentication Integration

This document outlines the authentication integration in the frontend part of the Web+ application.

## Completed Work

### Authentication Context and Provider
- Created an `AuthProvider` component in `src/lib/auth-context.tsx` that manages all authentication state:
  - Login/logout functionality
  - JWT token storage and management
  - User information storage and retrieval
  - Automatic token refresh near expiration
  - Error handling for authentication operations

### API Client Authentication
- Created `authFetch` function in `src/lib/api.ts` that automatically adds authentication headers to requests
- Updated the `safeFetch` function to use authentication with `authSafeFetch`
- Updated the Ollama API client (`src/api/ollama.ts`) to use authenticated requests
- Added authentication tokens to the legacy class-based API client

### Authentication User Interface
- Created login form component (`src/components/auth/LoginForm.tsx`)
- Created registration form component (`src/components/auth/RegisterForm.tsx`)
- Created an authentication page (`src/components/auth/AuthPage.tsx`) that toggles between login and registration
- Added a user menu component (`src/components/auth/UserMenu.tsx`) for authenticated users
- Created a header component with user menu integration (`src/components/Header.tsx`)

### Route Protection
- Created protected route component (`src/components/auth/ProtectedRoute.tsx`) that:
  - Redirects unauthenticated users to the login page
  - Checks for required user roles (e.g., admin)
  - Shows loading state while authentication is in progress

### Additional API Clients
- Created auth API client (`src/api/auth.ts`) for auth-specific operations
- Created conversations API client (`src/api/conversations.ts`) for chat functionality
- Enhanced Ollama API client to include conversation methods

## Integration Architecture

The authentication system uses a context-based architecture with these key components:

1. **JWT Token Management**
   - Stores tokens in localStorage for persistence
   - Automatically refreshes tokens before expiry
   - Handles token validation and decoding

2. **Protected Routes**
   - Wraps application content to ensure authentication
   - Redirects to login page when unauthenticated
   - Controls access based on user roles

3. **API Authentication**
   - Authenticates all API requests automatically
   - Handles token expiration and refresh
   - Provides type-safe API response handling

4. **User Interface**
   - Login and registration forms
   - User profile menu and logout functionality
   - Error handling and feedback

## Next Steps

1. **Testing Authentication Flow**
   - Test registration flow
   - Test login and session persistence
   - Test token refresh mechanism
   - Test protected routes and role-based access

2. **Additional Authentication Features**
   - Password reset functionality
   - Email verification
   - Social login integration (optional)
   - Remember me functionality

3. **User Profile Management**
   - Profile editing
   - Password changing
   - Profile picture upload

4. **Admin User Management**
   - User listing for administrators
   - User editing for administrators
   - User activation/deactivation

## Usage

To use the authentication system in a new component:

```tsx
import { useAuth } from '@/lib/auth-context';

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <p>Please log in to view this content</p>;
  }
  
  return (
    <div>
      <h1>Welcome, {user?.username}!</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

To make authenticated API calls:

```tsx
import { authApi } from '@/lib/api';

async function fetchData() {
  const data = await authApi.get('/api/some-protected-endpoint');
  return data;
}
```

All API clients from `@/api/*` will automatically use authentication.