import { AnchorHTMLAttributes, forwardRef } from "react";
import { cn } from "@/components/lib/utils";

// Link component that works with our Router
export const Link = forwardRef<
  HTMLAnchorElement,
  AnchorHTMLAttributes<HTMLAnchorElement>
>(({ href, children, className, ...props }, ref) => {
  const isExternal = 
    href?.startsWith("http") || 
    href?.startsWith("mailto:") || 
    href?.startsWith("tel:");

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (isExternal || !href || props.onClick) {
      // For external links or if there's already an onClick handler, do nothing
      if (props.onClick) {
        props.onClick(e);
      }
      return;
    }

    // For internal links, use the router's navigate function
    e.preventDefault();
    if ((window as any).navigate) {
      (window as any).navigate(href);
    }
  };

  return (
    <a
      ref={ref}
      href={href}
      className={cn(
        "text-primary hover:underline focus:outline-none",
        className
      )}
      {...props}
      target={isExternal ? "_blank" : props.target}
      rel={isExternal ? "noopener noreferrer" : props.rel}
      onClick={handleClick}
    >
      {children}
    </a>
  );
});

Link.displayName = "Link";