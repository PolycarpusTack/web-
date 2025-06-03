import React, { useRef, useEffect, useState } from 'react';
import { MessageThread, Message as MessageType } from '@/api/conversations';
import MessageWithAttachments from './MessageWithAttachments';
import { cn } from '@/components/lib/utils';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, MessageSquare, Plus } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

interface ThreadedMessageListProps {
  messages: MessageType[];
  threads?: MessageThread[];
  activeThreadId?: string;
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
  onReplyInThread?: (message: MessageType, threadId?: string) => void;
  onCreateThread?: (basedOnMessage?: MessageType) => void;
  onSelectThread?: (threadId: string) => void;
  onRetryGeneration?: (message: MessageType) => void;
  emptyState?: React.ReactNode;
}

export const ThreadedMessageList: React.FC<ThreadedMessageListProps> = ({
  messages,
  threads = [],
  activeThreadId,
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
  onReplyInThread,
  onCreateThread,
  onSelectThread,
  onRetryGeneration,
  emptyState
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [openThreads, setOpenThreads] = useState<Record<string, boolean>>({});
  
  // Initialize with active thread open
  useEffect(() => {
    if (activeThreadId) {
      setOpenThreads(prev => ({ ...prev, [activeThreadId]: true }));
    }
  }, [activeThreadId]);
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, openThreads]);
  
  // Empty state when no messages
  if (messages.length === 0 && threads.length === 0 && !loading) {
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
  
  // Organize messages - separate root messages and thread messages
  const rootMessages = messages.filter(msg => !msg.thread_id);
  
  // Toggle thread visibility
  const toggleThread = (threadId: string) => {
    setOpenThreads(prev => ({
      ...prev,
      [threadId]: !prev[threadId]
    }));
  };
  
  return (
    <div className={cn("flex-1 overflow-y-auto", className)}>
      {/* Root messages */}
      {rootMessages.map((message, index) => (
        <div key={message.id} className="message-container">
          <MessageWithAttachments
            message={message}
            userInitials={userInitials}
            modelInitials={modelInitials}
            userAvatarUrl={userAvatarUrl}
            modelAvatarUrl={modelAvatarUrl}
            username={username}
            modelName={modelName}
            onEdit={onEditMessage}
            onDelete={onDeleteMessage}
            onReply={onReplyToMessage}
            onRetry={message.role === 'assistant' ? onRetryGeneration : undefined}
            threadActionButton={
              onCreateThread && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onCreateThread(message)}
                  className="flex items-center gap-1 text-xs"
                >
                  <Plus className="h-3 w-3" />
                  <span>New Thread</span>
                </Button>
              )
            }
          />
          
          {/* Display replies if any */}
          {message.replies && message.replies.length > 0 && (
            <div className="ml-10 pl-6 border-l-2 border-muted mt-2">
              {message.replies.map(reply => (
                <MessageWithAttachments
                  key={reply.id}
                  message={reply}
                  userInitials={userInitials}
                  modelInitials={modelInitials}
                  userAvatarUrl={userAvatarUrl}
                  modelAvatarUrl={modelAvatarUrl}
                  username={username}
                  modelName={modelName}
                  onEdit={onEditMessage}
                  onDelete={onDeleteMessage}
                  onReply={onReplyToMessage}
                  onRetry={reply.role === 'assistant' ? onRetryGeneration : undefined}
                  showNestedReplyOption={false}
                />
              ))}
            </div>
          )}
        </div>
      ))}
      
      {/* Thread section */}
      {threads.length > 0 && (
        <div className="mt-6">
          <Separator className="mb-4" />
          <h3 className="text-lg font-medium mb-4">Discussion Threads</h3>
          
          {threads.map(thread => (
            <Collapsible
              key={thread.id}
              open={openThreads[thread.id] || false}
              onOpenChange={() => toggleThread(thread.id)}
              className="mb-4 border rounded-md"
            >
              <CollapsibleTrigger className="w-full p-3 flex items-center justify-between hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">
                    {thread.title || `Thread ${thread.id.substring(0, 6)}`}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {thread.messages?.length || 0} messages
                  </span>
                </div>
                {openThreads[thread.id] ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <div className="p-2">
                  {thread.messages && thread.messages.length > 0 ? (
                    thread.messages.map(message => (
                      <MessageWithAttachments
                        key={message.id}
                        message={message}
                        userInitials={userInitials}
                        modelInitials={modelInitials}
                        userAvatarUrl={userAvatarUrl}
                        modelAvatarUrl={modelAvatarUrl}
                        username={username}
                        modelName={modelName}
                        onEdit={onEditMessage}
                        onDelete={onDeleteMessage}
                        onReply={
                          message => onReplyInThread ? onReplyInThread(message, thread.id) : undefined
                        }
                        onRetry={message.role === 'assistant' ? onRetryGeneration : undefined}
                      />
                    ))
                  ) : (
                    <div className="py-4 text-center text-muted-foreground">
                      <p>No messages in this thread yet.</p>
                    </div>
                  )}
                  
                  {onReplyInThread && (
                    <div className="mt-2 flex justify-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onReplyInThread({} as MessageType, thread.id)}
                        className="w-full"
                      >
                        Reply in thread
                      </Button>
                    </div>
                  )}
                </div>
              </CollapsibleContent>
            </Collapsible>
          ))}
        </div>
      )}
      
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
        </div>
      )}
      
      {/* This element is used to scroll to bottom */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ThreadedMessageList;