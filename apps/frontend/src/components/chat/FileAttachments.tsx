// src/components/chat/FileAttachments.tsx
import React from 'react';
import { cn } from '@/components/lib/utils';
import FilePreview from './FilePreview';
import { Alert } from '@/components/ui/alert';
import { AlertCircleIcon } from "lucide-react";

export interface FileAttachment {
  id: string;
  filename: string;
  originalFilename?: string;
  contentType: string;
  size: number;
  url?: string;
}

interface FileAttachmentsProps {
  files: FileAttachment[];
  onRemove?: (fileId: string) => void;
  allowRemove?: boolean;
  className?: string;
  compact?: boolean;
  loading?: boolean;
  error?: string;
}

export const FileAttachments: React.FC<FileAttachmentsProps> = ({
  files,
  onRemove,
  allowRemove = false,
  className,
  compact = false,
  loading = false,
  error
}) => {
  if (loading) {
    return (
      <div className={cn("grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2", className)}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 rounded-md bg-muted animate-pulse"></div>
        ))}
      </div>
    );
  }
  
  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertCircleIcon className="h-4 w-4 mr-2" />
        {error}
      </Alert>
    );
  }
  
  if (files.length === 0) {
    return null;
  }
  
  return (
    <div className={cn(
      compact 
        ? "flex flex-wrap gap-2" 
        : "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3",
      className
    )}>
      {files.map((file) => (
        <FilePreview
          key={file.id}
          id={file.id}
          filename={file.originalFilename || file.filename}
          contentType={file.contentType}
          size={file.size}
          allowRemove={allowRemove}
          onRemove={onRemove ? () => onRemove(file.id) : undefined}
          maxWidth={compact ? 200 : 320}
          maxHeight={compact ? 150 : 240}
          className={compact ? "w-[200px]" : "w-full"}
        />
      ))}
    </div>
  );
};

export default FileAttachments;