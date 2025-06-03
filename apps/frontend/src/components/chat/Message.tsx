import React, { useState } from 'react';
import { Message as MessageType } from '@/api/conversations';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { formatTimeAgo } from '@/lib/shared-utils';
import MarkdownRenderer from './MarkdownRenderer';
import { cn } from '@/components/lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { Check, Copy, RotateCcw, Edit, MoreHorizontal, ThumbsUp, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface MessageProps {
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
}

export const Message: React.FC<MessageProps> = ({
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
}) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const avatarFallback = isUser ? userInitials : modelInitials;
  const avatarUrl = isUser ? userAvatarUrl : modelAvatarUrl;
  const displayName = isUser ? username : modelName;
  
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
        </div>
        
        <div className="prose-container overflow-hidden relative">
          <MarkdownRenderer content={message.content} />
        </div>
        
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
                
                {onReply && (
                  <DropdownMenuItem onClick={() => onReply(message)}>
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Reply
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

export default Message;