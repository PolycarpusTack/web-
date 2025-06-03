// src/App.tsx
import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { AuthProvider } from "@/lib/auth-context";
import { Router } from "@/lib/Router";
import EnterpriseModelManagerPortal from "./EnterpriseModelManagerPortal";
import { PerformanceMonitor } from "@/components/dev/PerformanceMonitor";
import { AccessibilityChecker } from "@/components/dev/AccessibilityChecker";

function App() {
  const [showEnterprisePortal, setShowEnterprisePortal] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);

  // Make the callback available globally
  (window as unknown as Record<string, unknown>).openEnterprisePortal = (modelId?: string) => {
    if (modelId) {
      setSelectedModelId(modelId);
    }
    setShowEnterprisePortal(true);
  };

  return (
    <AuthProvider>
      <div className="min-h-screen flex flex-col" data-testid="app-ready">
        <Router />
        
        {/* The enterprise portal is always rendered but visibility is controlled by the 'open' prop */}
        <EnterpriseModelManagerPortal 
          open={showEnterprisePortal} 
          onClose={() => setShowEnterprisePortal(false)} 
          defaultSelectedModel={selectedModelId}
        />
      </div>
      
      <Toaster />
      <PerformanceMonitor />
      <AccessibilityChecker />
    </AuthProvider>
  );
}

export default App;