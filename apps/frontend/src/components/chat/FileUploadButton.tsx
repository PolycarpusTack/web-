// src/components/chat/FileUploadButton.tsx
import React, { useState, useRef } from 'react';
import { File, Image, Loader2Icon, Paperclip, X } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { filesApi } from '@/api/files';
import { useToast } from '@/components/ui/use-toast';

interface FileUploadButtonProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  allowedFileTypes?: string;
  maxFileSize?: number;
  maxFiles?: number;
  className?: string;
}

export const FileUploadButton: React.FC<FileUploadButtonProps> = ({
  onFilesSelected,
  disabled = false,
  allowedFileTypes = "image/*,.pdf,.doc,.docx,.txt,.md",
  maxFileSize = 50 * 1024 * 1024, // 50MB
  maxFiles = 5,
  className,
}) => {
  const [loading, setLoading] = useState(false);
  const [uploadInfo, setUploadInfo] = useState<{
    allowed_types: string[];
    max_file_size: number;
    max_file_size_mb: number;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Load file upload info on first render
  React.useEffect(() => {
    const loadUploadInfo = async () => {
      try {
        const response = await filesApi.getUploadInfo();
        if (response.success) {
          setUploadInfo(response.data || null);
        }
      } catch (error) {
        console.error("Failed to load file upload info:", error);
      }
    };
    
    loadUploadInfo();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    
    const files = Array.from(e.target.files);
    
    // Validate file count
    if (files.length > maxFiles) {
      toast({
        title: "Too many files",
        description: `You can only upload ${maxFiles} files at once.`,
        variant: "destructive",
      });
      return;
    }
    
    // Validate file sizes
    const oversizedFiles = files.filter(file => file.size > maxFileSize);
    if (oversizedFiles.length > 0) {
      const maxSizeMB = Math.round(maxFileSize / (1024 * 1024));
      toast({
        title: "File too large",
        description: `Some files exceed the maximum size of ${maxSizeMB}MB.`,
        variant: "destructive",
      });
      return;
    }
    
    // Send selected files to parent
    onFilesSelected(files);
    
    // Reset the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        onChange={handleFileChange}
        multiple
        accept={allowedFileTypes}
        disabled={disabled || loading}
      />
      
      <DropdownMenu>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-10 w-10"
                  disabled={disabled || loading}
                >
                  {loading ? (
                    <Loader2Icon className="h-5 w-5 animate-spin" />
                  ) : (
                    <Paperclip className="h-5 w-5" />
                  )}
                </Button>
              </DropdownMenuTrigger>
            </TooltipTrigger>
            <TooltipContent>Attach files</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        
        <DropdownMenuContent align="end">
          <DropdownMenuItem 
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center cursor-pointer"
          >
            <Image className="mr-2 h-4 w-4" />
            Upload image
          </DropdownMenuItem>
          
          <DropdownMenuItem 
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center cursor-pointer"
          >
            <File className="mr-2 h-4 w-4" />
            Upload document
          </DropdownMenuItem>
          
          {uploadInfo && (
            <div className="px-2 py-1 text-xs text-muted-foreground">
              Max size: {uploadInfo.max_file_size_mb}MB
            </div>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
};

export default FileUploadButton;