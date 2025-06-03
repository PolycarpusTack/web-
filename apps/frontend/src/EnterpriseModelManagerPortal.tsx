// src/EnterpriseModelManagerPortal.tsx
import { useEffect } from 'react';
import OriginalEnterprisePortal from './components/OriginalEnterpriseModelManagerPortal';

// This is a wrapper to ensure the original enterprise portal component 
// integrates well with our application structure
interface EnterpriseModelManagerPortalProps {
  open: boolean;
  onClose: () => void;
  defaultSelectedModel?: string | null;
  defaultConversationId?: string | null;
}

export default function EnterpriseModelManagerPortal({
  open,
  onClose,
  defaultSelectedModel = null,
  defaultConversationId = null
}: EnterpriseModelManagerPortalProps) {
  
  // Any additional logic to bridge between our app and the enterprise portal
  useEffect(() => {
    if (open) {
      // You could add any setup needed when opening the enterprise portal
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [open]);

  return (
    <OriginalEnterprisePortal
      open={open}
      onClose={onClose}
      defaultSelectedModel={defaultSelectedModel}
      defaultConversationId={defaultConversationId}
    />
  );
}
