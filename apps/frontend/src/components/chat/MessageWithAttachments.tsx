// src/components/chat/MessageWithAttachments.tsx
import React, { useState, useEffect } from 'react';
import { Message as MessageType } from '@/api/conversations';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { formatTimeAgo } from '@/lib/shared-utils';
import MarkdownRenderer from './MarkdownRenderer';
import { cn } from '@/components/lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { Check, Copy, RotateCcw, Edit, File, MoreHorizontal, ThumbsUp, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import FileAttachments from './FileAttachments';
import { filesApi } from '@/api/files';

interface FileAttachment {
  id: string;
  filename: string;
  originalFilename?: string;
  contentType: string;
  size: number;
  url?: string;
}

interface MessageWithAttachmentsProps {
  message: MessageType;
  userInitials: string;
  modelInitials: string;
  userAvatarUrl?: string;
  modelAvatarUrl?: string;
  username?: string;
  modelName?: string;
  isLastMessage?: boolean;
  onEdit?: (message: MessageType) => void;
  onDelete?: (messageId: string) => void;
  onReply?: (message: MessageType) => void;
  onRetry?: (message: MessageType) => void;
  showActionsDropdown?: boolean;
  threadActionButton?: React.ReactNode;
  showNestedReplyOption?: boolean;
  isThreadMessage?: boolean;
  showFileAnalysisButton?: boolean;
}

export const MessageWithAttachments: React.FC<MessageWithAttachmentsProps> = ({
  message,
  userInitials,
  modelInitials,
  userAvatarUrl,
  modelAvatarUrl,
  username = 'You',
  modelName = 'Assistant',
  isLastMessage = false,
  onEdit,
  onDelete,
  onReply,
  onRetry,
  showActionsDropdown = true,
  threadActionButton,
  showNestedReplyOption = true,
  isThreadMessage = false,
  showFileAnalysisButton = false,
}) => {
  const [copied, setCopied] = useState(false);
  const [files, setFiles] = useState<FileAttachment[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  
  const isUser = message.role === 'user';
  const avatarFallback = isUser ? userInitials : modelInitials;
  const avatarUrl = isUser ? userAvatarUrl : modelAvatarUrl;
  const displayName = isUser ? username : modelName;
  
  useEffect(() => {
    // Load message files if the message has files
    const loadMessageFiles = async () => {
      if (!message.id) return;
      
      try {
        setLoadingFiles(true);
        const response = await filesApi.getMessageFiles(message.id);
        
        if (response.success && response.data?.files && response.data.files.length > 0) {
          setFiles(response.data.files.map(file => ({
            id: file.id,
            filename: file.filename,
            originalFilename: file.original_filename || file.filename,
            contentType: file.content_type,
            size: file.size,
            url: file.url
          })));
        }
      } catch (error) {
        console.error('Error loading message files:', error);
        setFileError('Failed to load attachments');
      } finally {
        setLoadingFiles(false);
      }
    };
    
    // Check if the message might have files (from metadata or other indicators)
    if (message.meta_data?.hasFiles || message.meta_data?.fileCount) {
      loadMessageFiles();
    }
  }, [message.id, message.meta_data]);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn(
      "group flex gap-3 px-4 py-6 relative",
      isUser ? "bg-muted/50" : "bg-background",
      isLastMessage && "pb-8"
    )}>
      <div className="flex-shrink-0 mt-1">
        <Avatar>
          <AvatarImage src={avatarUrl} />
          <AvatarFallback>{avatarFallback}</AvatarFallback>
        </Avatar>
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm">{displayName}</span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="text-xs text-muted-foreground">
                  {formatTimeAgo(message.created_at)}
                </span>
              </TooltipTrigger>
              <TooltipContent>
                {new Date(message.created_at).toLocaleString()}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          {message.tokens && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground ml-auto">
              {message.tokens} tokens
            </span>
          )}
          
          {(message.meta_data?.hasFiles || files.length > 0) && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="flex items-center text-xs px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground">
                    <File className="h-3 w-3 mr-1" />
                    {files.length}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  {files.length} attachment{files.length !== 1 ? 's' : ''}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        
        {/* Message content */}
        <div className="prose-container overflow-hidden relative mb-2">
          <MarkdownRenderer content={message.content} />
        </div>
        
        {/* File attachments */}
        {(files.length > 0 || loadingFiles) && (
          <div className="mt-3">
            <FileAttachments
              files={files}
              loading={loadingFiles}
              error={fileError || undefined}
              compact={true}
            />
          </div>
        )}
        
        {/* Thread action button (if provided) */}
        {threadActionButton && (
          <div className="mt-2">
            {threadActionButton}
          </div>
        )}
        
        {/* Message actions */}
        <div className={cn(
          "absolute right-4 top-4 transition-opacity",
          showActionsDropdown ? "opacity-0 group-hover:opacity-100" : "hidden"
        )}>
          {showActionsDropdown ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleCopy}>
                  {copied ? <Check className="mr-2 h-4 w-4" /> : <Copy className="mr-2 h-4 w-4" />}
                  Copy text
                </DropdownMenuItem>
                
                {isUser && onEdit && (
                  <DropdownMenuItem onClick={() => onEdit(message)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                )}
                
                {onReply && showNestedReplyOption && (
                  <DropdownMenuItem onClick={() => onReply(message)}>
                    <RotateCcw className="mr-2 h-4 w-4" />
                    {isThreadMessage ? 'Reply in thread' : 'Reply'}
                  </DropdownMenuItem>
                )}
                
                {showFileAnalysisButton && files.length > 0 && (
                  <DropdownMenuItem 
                    onClick={() => {
                      // Implementation for showing file analysis dialog will go here
                      console.log('Show file analysis for message:', message.id);
                    }}
                  >
                    <File className="mr-2 h-4 w-4" />
                    Analyze files
                  </DropdownMenuItem>
                )}
                
                {isLastMessage && !isUser && onRetry && (
                  <DropdownMenuItem onClick={() => onRetry(message)}>
                    <ThumbsUp className="mr-2 h-4 w-4" />
                    Regenerate
                  </DropdownMenuItem>
                )}
                
                <DropdownMenuSeparator />
                
                {onDelete && (
                  <DropdownMenuItem 
                    className="text-destructive focus:text-destructive" 
                    onClick={() => onDelete(message.id)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 rounded-full"
              onClick={handleCopy}
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageWithAttachments;