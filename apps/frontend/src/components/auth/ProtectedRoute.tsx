import { ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";
import { AuthPage } from "./AuthPage";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: "user" | "admin";
}

export function ProtectedRoute({ 
  children,
  requiredRole = "user" 
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  // Check for role access if needed
  if (requiredRole === "admin" && !user?.is_superuser) {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-4">
        <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
        <p className="text-muted-foreground mb-4">
          You don't have permission to access this area.
        </p>
        <a 
          href="/"
          className="text-primary hover:underline"
        >
          Return to Home
        </a>
      </div>
    );
  }

  // If authenticated and has required role, render children
  return <>{children}</>;
}