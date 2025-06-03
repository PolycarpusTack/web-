import { useState } from 'react';
import { Check, Copy } from "lucide-react";
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface CopyButtonProps {
  value: string;
  className?: string;
}

export function copyToClipboardWithMeta(value: string, meta?: Record<string, any>) {
  navigator.clipboard.writeText(value);
  // In a real app, this might track analytics
  console.log('Copied to clipboard:', { value, meta });
}

export function CopyButton({ value, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    copyToClipboardWithMeta(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button
      size="icon"
      variant="ghost"
      className={cn("h-6 w-6", className)}
      onClick={handleCopy}
    >
      {copied ? (
        <Check className="h-3 w-3" />
      ) : (
        <Copy className="h-3 w-3" />
      )}
      <span className="sr-only">Copy</span>
    </Button>
  );
}