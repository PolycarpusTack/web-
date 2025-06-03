declare module 'sonner' {
  import { FC, ReactNode } from 'react';

  export interface ToasterProps {
    position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
    hotkey?: string[];
    richColors?: boolean;
    expand?: boolean;
    duration?: number;
    gap?: number;
    visibleToasts?: number;
    closeButton?: boolean;
    toastOptions?: {
      className?: string;
      descriptionClassName?: string;
      style?: React.CSSProperties;
    };
    className?: string;
    style?: React.CSSProperties;
    offset?: string | number;
    dir?: 'ltr' | 'rtl';
    theme?: 'light' | 'dark' | 'system';
    invert?: boolean;
  }

  export const Toaster: FC<ToasterProps>;

  export interface ToastOptions {
    id?: string | number;
    duration?: number;
    onDismiss?: (toast: any) => void;
    onAutoClose?: (toast: any) => void;
  }

  export interface ToastT {
    id: string | number;
    title?: ReactNode;
    type?: 'normal' | 'action' | 'success' | 'info' | 'warning' | 'error' | 'loading' | 'default';
    icon?: ReactNode;
    jsx?: ReactNode;
    invert?: boolean;
    closeButton?: boolean;
    dismissible?: boolean;
    description?: ReactNode;
    duration?: number;
    delete?: boolean;
    important?: boolean;
    action?: {
      label: ReactNode;
      onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
    };
    cancel?: {
      label: ReactNode;
      onClick?: () => void;
    };
    onDismiss?: (toast: ToastT) => void;
    onAutoClose?: (toast: ToastT) => void;
    promise?: PromiseT;
    cancelButtonStyle?: React.CSSProperties;
    actionButtonStyle?: React.CSSProperties;
    style?: React.CSSProperties;
    unstyled?: boolean;
    className?: string;
    classNames?: {
      toast?: string;
      title?: string;
      description?: string;
      loader?: string;
      closeButton?: string;
      cancelButton?: string;
      actionButton?: string;
      action?: string;
      warning?: string;
      error?: string;
      success?: string;
      default?: string;
      info?: string;
      loading?: string;
    };
  }

  interface PromiseT {
    loading?: string;
    success?: string | ((data: any) => ReactNode);
    error?: string | ((error: any) => ReactNode);
  }

  export const toast: {
    (message: ReactNode, options?: ToastOptions): string | number;
    success: (message: ReactNode, options?: ToastOptions) => string | number;
    info: (message: ReactNode, options?: ToastOptions) => string | number;
    warning: (message: ReactNode, options?: ToastOptions) => string | number;
    error: (message: ReactNode, options?: ToastOptions) => string | number;
    custom: (jsx: ReactNode, options?: ToastOptions) => string | number;
    message: (message: ReactNode, options?: ToastOptions) => string | number;
    promise: <T,>(promise: Promise<T>, options: PromiseT & ToastOptions) => string | number;
    dismiss: (toastId?: string | number) => void;
    loading: (message: ReactNode, options?: ToastOptions) => string | number;
  };
}