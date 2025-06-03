# Authentication Implementation

This document provides a comprehensive overview of the authentication system implementation in Web+.

## Architecture

The authentication system uses a layered approach with these key components:

### 1. JWT-based Authentication

- **Backend**: JWT token generation and validation with role-based permissions
- **Frontend**: Token storage, automatic refresh, and authenticated API calls

### 2. User Interface Components

- Login page with form validation
- Registration page with form validation
- Protected routes that redirect to login if not authenticated
- User profile management

### 3. API Integration

- Authenticated API clients for all backend services
- Automatic token refresh when expired
- Error handling for authentication failures

## Implementation Details

### Authentication Context

A React context provides authentication state and functions throughout the application:

```tsx
// auth-context.tsx
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  // ... more state and functions

  // Authentication functions
  const login = async (username: string, password: string): Promise<boolean> => { /* ... */ };
  const logout = () => { /* ... */ };
  const refreshTokens = async (): Promise<boolean> => { /* ... */ };
  
  // ... token refresh logic, user info fetching, etc.
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Authenticated API Client

A custom fetch wrapper that automatically adds authentication headers and handles token refresh:

```tsx
// api.ts
export function createAuthFetch(config: ApiConfig = DEFAULT_CONFIG) {
  return async function authFetch(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    // ... check and refresh tokens if needed
    // ... add authentication headers
    return fetch(finalUrl, authOptions);
  };
}
```

### Protected Routes

A component that checks authentication status and redirects if needed:

```tsx
// ProtectedRoute.tsx
export function ProtectedRoute({ 
  children,
  requiredRole = "user" 
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  if (requiredRole === "admin" && !user?.is_superuser) {
    return <AccessDenied />;
  }

  return <>{children}</>;
}
```

## Routing System

A simple client-side routing system was implemented to handle navigation between authenticated pages:

```tsx
// Router.tsx
export function Router() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  // ... navigation event listeners
  
  const routeElement = getRouteElement(currentPath);
  
  return (
    <div id="router">
      {routeElement}
    </div>
  );
}
```

## User Interface

### Login and Registration

- Forms for username/password login
- Registration with password confirmation
- Form validation
- Error handling

### User Menu

- Avatar with user initials
- Dropdown menu with user information
- Navigation to profile, settings, etc.
- Logout functionality

### Profile Management

- User information editing
- Password changing
- Account settings

## API Endpoints

The authentication system integrates with these backend endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Authenticate and get tokens |
| `/api/auth/register` | POST | Create a new user account |
| `/api/auth/refresh` | POST | Refresh an expired token |
| `/api/auth/me` | GET | Get the current user's information |
| `/api/auth/me` | PUT | Update the current user's information |
| `/api/auth/change-password` | POST | Change the current user's password |

## Security Considerations

1. **Token Storage**: JWT tokens are stored in localStorage for persistence
2. **CSRF Protection**: JWT tokens are sent in the Authorization header, not as cookies
3. **XSS Protection**: React's inherent protection against XSS
4. **Token Expiration**: Access tokens expire after a short period, refresh tokens have longer life
5. **Automatic Refresh**: Tokens are refreshed automatically before expiry

## Future Improvements

1. **Social Authentication**: Integration with Google, GitHub, etc.
2. **2FA Support**: Add two-factor authentication
3. **OAuth Integration**: Support for external OAuth providers
4. **Persistent Sessions**: "Remember me" functionality
5. **Enhanced Security**: HTTP-only cookies for token storage on production

## Usage Examples

### Accessing Authentication Context

```tsx
function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <p>Please log in</p>;
  }
  
  return (
    <div>
      <h1>Welcome, {user?.username}!</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Making Authenticated API Calls

```tsx
// Using the enhanced API client
const response = await api.models.getAll();

// Using the authFetch function directly
const response = await authFetch('/api/some/endpoint', {
  method: 'POST',
  body: JSON.stringify(data)
});
```

### Protecting Routes

```tsx
// In routes definition
{
  path: "/admin",
  element: (
    <ProtectedRoute requiredRole="admin">
      <AdminPanel />
    </ProtectedRoute>
  ),
  protected: true,
  adminOnly: true
}
```