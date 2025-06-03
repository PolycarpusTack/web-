import React from 'react';
import { Message as MessageType } from '@/api/conversations';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { cn } from '@/components/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Database, Download, Info, Scissors } from "lucide-react";

interface ContextWindowProps {
  messages: MessageType[];
  maxTokens?: number;
  usedTokens?: number;
  className?: string;
  onClearContext?: () => void;
  onPruneContext?: (messageIds: string[]) => void;
  onExportContext?: () => void;
}

export const ContextWindow: React.FC<ContextWindowProps> = ({
  messages,
  maxTokens = 4000,
  usedTokens = 0,
  className,
  onClearContext,
  onPruneContext,
  onExportContext
}) => {
  const [selectedMessages, setSelectedMessages] = React.useState<string[]>([]);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  
  const tokenPercentage = Math.min(100, (usedTokens / maxTokens) * 100);
  const tokenStatus = 
    tokenPercentage < 70 ? 'success' :
    tokenPercentage < 90 ? 'warning' :
    'danger';
  
  // Calculate token distribution - which types of messages use how many tokens
  const userMessages = messages.filter(m => m.role === 'user');
  const assistantMessages = messages.filter(m => m.role === 'assistant');
  const systemMessages = messages.filter(m => m.role === 'system');
  
  const userTokens = userMessages.reduce((sum, msg) => sum + (msg.tokens || 0), 0);
  const assistantTokens = assistantMessages.reduce((sum, msg) => sum + (msg.tokens || 0), 0);
  const systemTokens = systemMessages.reduce((sum, msg) => sum + (msg.tokens || 0), 0);
  
  const handleMessageSelect = (messageId: string) => {
    setSelectedMessages(prev => 
      prev.includes(messageId)
        ? prev.filter(id => id !== messageId)
        : [...prev, messageId]
    );
  };
  
  const handlePruneSelected = () => {
    if (onPruneContext && selectedMessages.length > 0) {
      onPruneContext(selectedMessages);
      setSelectedMessages([]);
      setDialogOpen(false);
    }
  };

  return (
    <div className={cn("p-4 border-t bg-muted/20", className)}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Database className="h-4 w-4 mr-2 text-muted-foreground" />
          <h4 className="text-sm font-medium">Context Window</h4>
        </div>
        
        <div className="flex items-center gap-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Info className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>The context window shows how much of the model's memory is being used.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          {onExportContext && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={onExportContext}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Export conversation</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          
          {onClearContext && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={onClearContext}
                  >
                    <Scissors className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Clear context window</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          
          {onPruneContext && (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="text-xs h-8">
                  Manage Context
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[550px]">
                <DialogHeader>
                  <DialogTitle>Manage Context Window</DialogTitle>
                  <DialogDescription>
                    Select messages to remove from the context window to free up space.
                  </DialogDescription>
                </DialogHeader>
                
                <div className="py-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Context Usage: {usedTokens} / {maxTokens} tokens</span>
                    <span
                      className={cn(
                        tokenStatus === 'success' && 'text-green-500',
                        tokenStatus === 'warning' && 'text-yellow-500',
                        tokenStatus === 'danger' && 'text-red-500'
                      )}
                    >
                      {Math.round(tokenPercentage)}%
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="flex flex-col items-center">
                      <span className="text-xs text-muted-foreground">User</span>
                      <span className="font-medium">{userTokens} tokens</span>
                      <span className="text-xs text-muted-foreground">
                        ({Math.round((userTokens / usedTokens) * 100)}%)
                      </span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-xs text-muted-foreground">Assistant</span>
                      <span className="font-medium">{assistantTokens} tokens</span>
                      <span className="text-xs text-muted-foreground">
                        ({Math.round((assistantTokens / usedTokens) * 100)}%)
                      </span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-xs text-muted-foreground">System</span>
                      <span className="font-medium">{systemTokens} tokens</span>
                      <span className="text-xs text-muted-foreground">
                        ({Math.round((systemTokens / usedTokens) * 100)}%)
                      </span>
                    </div>
                  </div>
                  
                  <Separator className="my-4" />
                  
                  <ScrollArea className="h-[200px] rounded-md border p-4">
                    <div className="space-y-4">
                      {messages.map((message) => (
                        <div key={message.id} className="flex items-start gap-2">
                          <Checkbox
                            id={message.id}
                            checked={selectedMessages.includes(message.id)}
                            onCheckedChange={() => handleMessageSelect(message.id)}
                          />
                          <div className="grid gap-1.5">
                            <Label
                              htmlFor={message.id}
                              className="font-medium text-sm flex items-center"
                            >
                              {message.role === 'user' ? 'User' : 
                               message.role === 'assistant' ? 'Assistant' : 'System'}
                              {message.tokens && (
                                <span className="ml-2 text-xs text-muted-foreground">
                                  ({message.tokens} tokens)
                                </span>
                              )}
                            </Label>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {message.content}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
                
                <div className="flex justify-between">
                  <Button variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handlePruneSelected}
                    disabled={selectedMessages.length === 0}
                  >
                    Remove Selected Messages
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">
            {usedTokens} / {maxTokens} tokens used
          </span>
          <span
            className={cn(
              "font-medium",
              tokenStatus === 'success' && 'text-green-500',
              tokenStatus === 'warning' && 'text-yellow-500',
              tokenStatus === 'danger' && 'text-red-500'
            )}
          >
            {Math.round(tokenPercentage)}%
          </span>
        </div>
        
        <Progress
          value={tokenPercentage}
          className={cn(
            "h-2",
            tokenStatus === 'success' && 'bg-muted [&>div]:bg-green-500',
            tokenStatus === 'warning' && 'bg-muted [&>div]:bg-yellow-500',
            tokenStatus === 'danger' && 'bg-muted [&>div]:bg-red-500'
          )}
        />
      </div>
    </div>
  );
};

export default ContextWindow;