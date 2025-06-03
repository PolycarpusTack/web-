import { Button } from "@/components/ui/button";
import { UserMenu } from "@/components/auth/UserMenu";
import { HelpMenu } from "@/components/help";
import { LayoutDashboardIcon, MessagesSquareIcon } from "lucide-react";

interface HeaderProps {
  title: string;
  onEnterprisePortalClick?: () => void;
}

export function Header({ title, onEnterprisePortalClick }: HeaderProps) {
  // Navigate function that uses the window.navigate from Router.tsx
  const navigate = (path: string) => {
    if ((window as any).navigate) {
      (window as any).navigate(path);
    }
  };

  return (
    <header className="border-b p-4 flex justify-between items-center">
      <div className="flex items-center">
        <h1 className="text-2xl font-bold">{title}</h1>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="flex space-x-1">
          <Button 
            variant="ghost" 
            onClick={() => navigate("/")}
            className="text-sm"
          >
            <LayoutDashboardIcon className="h-4 w-4 mr-2" />
            Models
          </Button>
          
          <Button 
            variant="ghost" 
            onClick={() => navigate("/conversations")}
            className="text-sm"
          >
            <MessagesSquareIcon className="h-4 w-4 mr-2" />
            Conversations
          </Button>
        </div>
        
        {onEnterprisePortalClick && (
          <Button 
            onClick={onEnterprisePortalClick}
            variant="outline"
          >
            Open Enterprise Portal
          </Button>
        )}
        
        <HelpMenu />
        <UserMenu />
      </div>
    </header>
  );
}