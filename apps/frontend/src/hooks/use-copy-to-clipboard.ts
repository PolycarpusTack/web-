import { useState } from 'react';

export function useCopyToClipboard() {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const copyToClipboard = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setError(null);
      setTimeout(() => setCopied(false), 2000);
      return true;
    } catch (err) {
      setCopied(false);
      setError(err as Error);
      return false;
    }
  };

  return { copyToClipboard, copied, error };
}