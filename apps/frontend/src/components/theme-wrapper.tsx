import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface ThemeWrapperProps {
  children: ReactNode;
  className?: string;
  defaultTheme?: string;
}

export function ThemeWrapper({ children, className, defaultTheme = 'zinc' }: ThemeWrapperProps) {
  return (
    <div className={cn(`theme-${defaultTheme}`, className)}>
      {children}
    </div>
  );
}