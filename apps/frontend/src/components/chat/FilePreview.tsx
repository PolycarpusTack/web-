// src/components/chat/FilePreview.tsx
import React, { useState } from 'react';
import { DownloadIcon, ExternalLink, File, FileText, Image, X } from "lucide-react";
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { cn } from '@/components/lib/utils';
import { getFileUrl, isImageFile, formatFileSize } from '@/api/files';

export interface FilePreviewProps {
  id: string;
  filename: string;
  contentType: string;
  size: number;
  className?: string;
  onRemove?: () => void;
  allowRemove?: boolean;
  maxWidth?: number;
  maxHeight?: number;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  id,
  filename,
  contentType,
  size,
  className,
  onRemove,
  allowRemove = false,
  maxWidth = 320,
  maxHeight = 240
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  const fileUrl = getFileUrl(id);
  const isImage = isImageFile(contentType);
  const formattedSize = formatFileSize(size);
  
  // Get icon based on file type
  const getFileTypeIcon = () => {
    if (contentType === 'application/pdf') {
      return <FileText className="h-8 w-8 text-red-500" />;
    } else if (contentType === 'text/plain' || contentType === 'text/markdown') {
      return <FileText className="h-8 w-8 text-blue-500" />;
    } else if (contentType === 'application/msword' || contentType.includes('word')) {
      return <FileText className="h-8 w-8 text-blue-500" />;
    } else {
      return <File className="h-8 w-8 text-gray-500" />;
    }
  };
  
  return (
    <Card className={cn(
      "relative flex rounded-md overflow-hidden border",
      className
    )}>
      {/* File content preview */}
      <div className="flex flex-col w-full">
        {isImage && !imageError ? (
          <div 
            className={cn(
              "flex items-center justify-center bg-black/5 min-h-[120px]",
              !imageLoaded && "animate-pulse"
            )}
            style={{ maxWidth, maxHeight }}
          >
            <img
              src={fileUrl}
              alt={filename}
              className={cn(
                "object-contain max-w-full max-h-full",
                !imageLoaded && "opacity-0",
                imageLoaded && "opacity-100"
              )}
              style={{ maxWidth, maxHeight }}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />
            {!imageLoaded && <Image className="h-8 w-8 text-muted-foreground/50" />}
          </div>
        ) : (
          <div className="flex items-center justify-center bg-muted/50 p-6 min-h-[120px]">
            {getFileTypeIcon()}
          </div>
        )}
        
        {/* File info */}
        <div className="flex justify-between items-center p-3 bg-card">
          <div className="overflow-hidden">
            <div className="font-medium text-sm truncate max-w-[200px]" title={filename}>
              {filename}
            </div>
            <div className="text-xs text-muted-foreground">
              {formattedSize}
            </div>
          </div>
          
          <div className="flex space-x-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => window.open(fileUrl, '_blank')}
              title="Open in new tab"
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => {
                const link = document.createElement('a');
                link.href = fileUrl;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}
              title="Download"
            >
              <DownloadIcon className="h-4 w-4" />
            </Button>
            
            {allowRemove && onRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={onRemove}
                title="Remove"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default FilePreview;