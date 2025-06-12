import { Button } from "@/components/ui/button";
import { UserMenu } from "@/components/auth/UserMenu";
import { HelpMenu } from "@/components/help";
import { MainNavigation } from "@/components/navigation/MainNavigation";

interface HeaderProps {
  title: string;
  onEnterprisePortalClick?: () => void;
}

export function Header({ title, onEnterprisePortalClick }: HeaderProps) {
  return (
    <header className="border-b p-4 flex justify-between items-center">
      <div className="flex items-center">
        <h1 className="text-2xl font-bold">{title}</h1>
      </div>
      
      <div className="flex items-center gap-4">
        <MainNavigation />
        
        <HelpMenu />
        <UserMenu />
      </div>
    </header>
  );
}