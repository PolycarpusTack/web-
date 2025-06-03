import * as React from "react";
import { Loader2 } from "lucide-react";
import { Button, ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface LoadingButtonProps extends ButtonProps {
  loading?: boolean;
  loadingText?: string;
  loadingIcon?: React.ReactNode;
}

const LoadingButton = React.forwardRef<HTMLButtonElement, LoadingButtonProps>(
  ({ 
    className, 
    children, 
    disabled,
    loading = false,
    loadingText,
    loadingIcon,
    ...props 
  }, ref) => {
    return (
      <Button
        ref={ref}
        className={cn(className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <>
            {loadingIcon || <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {loadingText || children}
          </>
        ) : (
          children
        )}
      </Button>
    );
  }
);

LoadingButton.displayName = "LoadingButton";

export { LoadingButton };