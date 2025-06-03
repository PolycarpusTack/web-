import React from 'react';
import { X, FileText, Image, FileCode, Archive, File } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface FileAttachment {
  id: string;
  file: File;
  preview?: string;
  uploading?: boolean;
  error?: string;
}

interface FilePreviewListProps {
  files: FileAttachment[];
  onRemove?: (id: string) => void;
  compact?: boolean;
  className?: string;
}

const getFileIcon = (file: File) => {
  const type = file.type;
  
  if (type.startsWith('image/')) return <Image className="h-4 w-4" />;
  if (type.startsWith('text/') || type.includes('document')) return <FileText className="h-4 w-4" />;
  if (type.includes('javascript') || type.includes('json') || type.includes('xml')) return <FileCode className="h-4 w-4" />;
  if (type.includes('zip') || type.includes('archive')) return <Archive className="h-4 w-4" />;
  
  return <File className="h-4 w-4" />;
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

export const FilePreviewList: React.FC<FilePreviewListProps> = ({
  files,
  onRemove,
  compact = false,
  className
}) => {
  if (files.length === 0) return null;

  if (compact) {
    return (
      <div className={cn("flex flex-wrap gap-2", className)}>
        {files.map((attachment) => (
          <div
            key={attachment.id}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs",
              "bg-muted border",
              attachment.error && "border-destructive bg-destructive/10"
            )}
          >
            {getFileIcon(attachment.file)}
            <span className="max-w-[150px] truncate">
              {attachment.file.name}
            </span>
            {onRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => onRemove(attachment.id)}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {files.map((attachment) => (
        <div
          key={attachment.id}
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg border bg-card",
            attachment.error && "border-destructive"
          )}
        >
          {/* File preview or icon */}
          <div className="flex-shrink-0">
            {attachment.preview && attachment.file.type.startsWith('image/') ? (
              <img
                src={attachment.preview}
                alt={attachment.file.name}
                className="h-12 w-12 rounded object-cover"
              />
            ) : (
              <div className="h-12 w-12 rounded bg-muted flex items-center justify-center">
                {getFileIcon(attachment.file)}
              </div>
            )}
          </div>

          {/* File info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">
              {attachment.file.name}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(attachment.file.size)}
              {attachment.error && (
                <span className="text-destructive ml-2">{attachment.error}</span>
              )}
            </p>
          </div>

          {/* Remove button */}
          {onRemove && (
            <Button
              variant="ghost"
              size="icon"
              className="flex-shrink-0"
              onClick={() => onRemove(attachment.id)}
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Remove file</span>
            </Button>
          )}
        </div>
      ))}
    </div>
  );
};