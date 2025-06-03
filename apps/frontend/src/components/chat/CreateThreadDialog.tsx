import React, { useState } from 'react';
import { Message } from '@/api/conversations';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { MessageSquareIcon } from "lucide-react";

interface CreateThreadDialogProps {
  conversationId: string;
  basedOnMessage?: Message;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateThread: (title: string, basedOnMessageId?: string) => Promise<void>;
  trigger?: React.ReactNode;
}

export const CreateThreadDialog: React.FC<CreateThreadDialogProps> = ({
  conversationId,
  basedOnMessage,
  open,
  onOpenChange,
  onCreateThread,
  trigger,
}) => {
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      await onCreateThread(title, basedOnMessage?.id);
      setTitle('');
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to create thread:", error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Thread</DialogTitle>
          <DialogDescription>
            {basedOnMessage 
              ? 'Create a discussion thread based on this message.' 
              : 'Create a new discussion thread in this conversation.'}
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="grid w-full items-center gap-1.5">
            <Label htmlFor="thread-title">Thread Title</Label>
            <Input
              id="thread-title"
             
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="col-span-3"
              autoComplete="off"
              required
            />
          </div>
          
          {basedOnMessage && (
            <div className="rounded-md bg-muted p-3 text-sm">
              <p className="font-medium mb-1">Based on message:</p>
              <p className="text-muted-foreground line-clamp-3">
                {basedOnMessage.content}
              </p>
            </div>
          )}
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !title.trim()}>
              {loading ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-primary border-r-transparent" />
                  Creating...
                </>
              ) : (
                <>
                  <MessageSquareIcon className="mr-2 h-4 w-4" />
                  Create Thread
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateThreadDialog;