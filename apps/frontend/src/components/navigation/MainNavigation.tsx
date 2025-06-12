import { Button } from "@/components/ui/button";
import { 
  LayoutDashboardIcon, 
  MessagesSquareIcon, 
  BrainIcon,
  WorkflowIcon,
  ShieldIcon,
  UserIcon
} from "lucide-react";

export function MainNavigation() {
  const navigate = (path: string) => {
    if ((window as any).navigate) {
      (window as any).navigate(path);
    }
  };

  const navItems = [
    { path: "/", label: "Models", icon: LayoutDashboardIcon },
    { path: "/chat", label: "Chat", icon: MessagesSquareIcon },
    { path: "/pipelines", label: "Pipelines", icon: WorkflowIcon },
    { path: "/conversations", label: "Conversations", icon: BrainIcon },
    { path: "/admin", label: "Admin", icon: ShieldIcon },
    { path: "/profile", label: "Profile", icon: UserIcon },
  ];

  return (
    <nav className="flex space-x-1">
      {navItems.map((item) => (
        <Button
          key={item.path}
          variant="ghost"
          onClick={() => navigate(item.path)}
          className="text-sm"
        >
          <item.icon className="h-4 w-4 mr-2" />
          {item.label}
        </Button>
      ))}
    </nav>
  );
}
