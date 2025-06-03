// src/pages/HomePage.tsx
import { ReactNode } from "react";
import { Header } from "@/components/Header";
import ModelsPage from "@/app/pages/ModelsPage";

interface HomePageProps {
  children?: ReactNode;
}

export default function HomePage({ children }: HomePageProps) {
  const handleOpenEnterprisePortal = () => {
    // Use the global function defined in App.tsx
    if ((window as any).openEnterprisePortal) {
      (window as any).openEnterprisePortal();
    }
  };

  const handleModelSelect = (modelId: string) => {
    // Use the global function defined in App.tsx
    if ((window as any).openEnterprisePortal) {
      (window as any).openEnterprisePortal(modelId);
    }
  };

  return (
    <>
      <Header 
        title="Ollama Model Manager" 
        onEnterprisePortalClick={handleOpenEnterprisePortal} 
      />
      
      <main className="flex-1">
        {children || <ModelsPage onModelSelect={handleModelSelect} />}
      </main>
    </>
  );
}