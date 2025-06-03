import { useState } from "react";
import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";

type AuthView = "login" | "register";

interface AuthPageProps {
  defaultView?: AuthView;
  onAuthSuccess?: () => void;
}

export function AuthPage({ defaultView = "login", onAuthSuccess }: AuthPageProps) {
  const [currentView, setCurrentView] = useState<AuthView>(defaultView);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold">Web+ LLM Manager</h1>
          <p className="text-muted-foreground">
            {currentView === "login" 
              ? "Log in to manage your LLM models" 
              : "Create an account to get started"}
          </p>
        </div>

        {currentView === "login" ? (
          <LoginForm
            onSuccess={onAuthSuccess}
            onRegisterClick={() => setCurrentView("register")}
          />
        ) : (
          <RegisterForm
            onSuccess={() => setCurrentView("login")}
            onLoginClick={() => setCurrentView("login")}
          />
        )}
      </div>
    </div>
  );
}