import React, { useRef, useEffect } from 'react';
import { Message as MessageType } from '@/api/conversations';
import Message from './Message';
import { cn } from '@/components/lib/utils';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { RefreshCcw } from "lucide-react";

interface MessageListProps {
  messages: MessageType[];
  userInitials: string;
  modelInitials: string;
  userAvatarUrl?: string;
  modelAvatarUrl?: string;
  username?: string;
  modelName?: string;
  loading?: boolean;
  error?: string;
  className?: string;
  onEditMessage?: (message: MessageType) => void;
  onDeleteMessage?: (messageId: string) => void;
  onReplyToMessage?: (message: MessageType) => void;
  onRetryGeneration?: (message: MessageType) => void;
  onClearConversation?: () => void;
  emptyState?: React.ReactNode;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  userInitials,
  modelInitials,
  userAvatarUrl,
  modelAvatarUrl,
  username = 'You',
  modelName = 'Assistant',
  loading = false,
  error = '',
  className,
  onEditMessage,
  onDeleteMessage,
  onReplyToMessage,
  onRetryGeneration,
  onClearConversation,
  emptyState
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Empty state when no messages
  if (messages.length === 0 && !loading) {
    return (
      <div className={cn(
        "flex-1 flex flex-col items-center justify-center p-8 text-center",
        className
      )}>
        {emptyState || (
          <div className="max-w-md">
            <h3 className="text-xl font-semibold mb-2">No messages yet</h3>
            <p className="text-muted-foreground mb-4">
              Start the conversation by sending a message below.
            </p>
          </div>
        )}
      </div>
    );
  }
  
  // Group messages by date for date separators
  const groupedMessages = messages.reduce<{date: string; messages: MessageType[]}[]>((acc, message) => {
    const date = new Date(message.created_at).toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    
    const lastGroup = acc[acc.length - 1];
    
    if (lastGroup && lastGroup.date === date) {
      lastGroup.messages.push(message);
    } else {
      acc.push({ date, messages: [message] });
    }
    
    return acc;
  }, []);

  return (
    <div className={cn("flex-1 overflow-y-auto", className)}>
      {/* Optional conversation controls */}
      {messages.length > 0 && onClearConversation && (
        <div className="flex justify-center py-4 sticky top-0 bg-background/80 backdrop-blur-sm z-10">
          <Button
            variant="outline"
            size="sm"
            onClick={onClearConversation}
            className="text-xs"
          >
            Clear conversation
          </Button>
        </div>
      )}
      
      {/* Messages with date separators */}
      {groupedMessages.map((group, groupIndex) => (
        <div key={group.date}>
          {/* Date separator */}
          <div className="flex items-center justify-center py-4">
            <Separator className="flex-grow" />
            <span className="px-2 text-xs text-muted-foreground">{group.date}</span>
            <Separator className="flex-grow" />
          </div>
          
          {/* Messages in this date group */}
          {group.messages.map((message, index) => (
            <Message
              key={message.id}
              message={message}
              userInitials={userInitials}
              modelInitials={modelInitials}
              userAvatarUrl={userAvatarUrl}
              modelAvatarUrl={modelAvatarUrl}
              username={username}
              modelName={modelName}
              isLastMessage={
                groupIndex === groupedMessages.length - 1 && 
                index === group.messages.length - 1
              }
              onEdit={onEditMessage}
              onDelete={onDeleteMessage}
              onReply={onReplyToMessage}
              onRetry={message.role === 'assistant' ? onRetryGeneration : undefined}
            />
          ))}
        </div>
      ))}
      
      {/* Loading indicator */}
      {loading && (
        <div className="flex items-start gap-3 p-4">
          <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
            <div className="h-5 w-5 rounded-full border-2 border-t-primary border-r-transparent border-b-transparent border-l-transparent animate-spin" />
          </div>
          <div className="flex-1 py-2">
            <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
            <div className="h-4 w-1/2 bg-muted animate-pulse rounded mt-2" />
          </div>
        </div>
      )}
      
      {/* Error message */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-destructive/10 border-l-4 border-destructive">
          <div className="flex-1">
            <p className="font-medium text-destructive mb-1">Error</p>
            <p className="text-sm text-destructive/90">{error}</p>
          </div>
          {onRetryGeneration && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const lastAssistantMessage = [...messages]
                  .reverse()
                  .find(m => m.role === 'assistant');
                  
                if (lastAssistantMessage && onRetryGeneration) {
                  onRetryGeneration(lastAssistantMessage);
                }
              }}
            >
              <RefreshCcw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          )}
        </div>
      )}
      
      {/* This element is used to scroll to bottom */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;