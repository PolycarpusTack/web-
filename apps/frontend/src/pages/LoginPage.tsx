// src/pages/LoginPage.tsx
import { useState, useEffect } from "react";
import { AuthPage } from "@/components/auth";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { isAuthenticated } = useAuth();
  const [redirectUrl, setRedirectUrl] = useState("/");

  useEffect(() => {
    // Get the redirect URL from the query params if any
    const urlParams = new URLSearchParams(window.location.search);
    const redirectTo = urlParams.get("redirect");
    
    if (redirectTo) {
      setRedirectUrl(redirectTo);
    }
    
    // If user is already authenticated, redirect to the home page or the redirect URL
    if (isAuthenticated) {
      window.location.href = redirectUrl;
    }
  }, [isAuthenticated, redirectUrl]);

  const handleAuthSuccess = () => {
    // Redirect on successful authentication
    window.location.href = redirectUrl;
  };

  return (
    <AuthPage 
      defaultView="login" 
      onAuthSuccess={handleAuthSuccess} 
    />
  );
}