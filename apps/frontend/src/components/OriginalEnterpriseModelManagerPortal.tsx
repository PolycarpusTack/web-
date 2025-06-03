import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { BotIcon, Loader2, Send, User as UserIcon } from "lucide-react";

// Types
interface EnterprisePortalProps {
  open: boolean;
  onClose: () => void;
  defaultSelectedModel?: string | null;
  defaultConversationId?: string | null;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

export default function OriginalEnterpriseModelManagerPortal({
  open,
  onClose,
  defaultSelectedModel = null,
  defaultConversationId = null
}: EnterprisePortalProps) {
  const [activeTab, setActiveTab] = useState<string>('chat');
  const [inputMessage, setInputMessage] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [conversation, setConversation] = useState<Conversation>({
    id: 'conversation-1',
    title: 'New conversation',
    messages: []
  });

  // Mock sending a message
  const handleSendMessage = () => {
    if (!inputMessage.trim() || isSending) return;
    
    setIsSending(true);
    
    // Create a new user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };
    
    // Update conversation with the new message
    setConversation(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage]
    }));
    
    setInputMessage('');
    
    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: `This is a placeholder response from the AI model to your message: "${inputMessage}"`,
        timestamp: new Date().toISOString()
      };
      
      setConversation(prev => ({
        ...prev,
        messages: [...prev.messages, aiMessage]
      }));
      
      setIsSending(false);
    }, 1500);
  };
  
  // Handle key press (Enter to send)
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Format message timestamp
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Enterprise Model Manager Portal</DialogTitle>
        </DialogHeader>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="models">Models</TabsTrigger>
            <TabsTrigger value="factory">Auto Factory</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>
          
          <TabsContent value="chat" className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col overflow-auto p-4 space-y-4">
              {conversation.messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                  <BotIcon className="h-12 w-12 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No messages yet</h3>
                  <p>Start a conversation with the AI model</p>
                </div>
              ) : (
                conversation.messages.map((message) => (
                  <div 
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-3 rounded-lg ${
                        message.role === 'user' 
                          ? 'bg-primary text-primary-foreground ml-12' 
                          : 'bg-muted mr-12'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {message.role === 'user' ? (
                          <Badge>You</Badge>
                        ) : (
                          <Badge variant="secondary">AI</Badge>
                        )}
                        <span className="text-xs opacity-70">
                          {formatTimestamp(message.timestamp)}
                        </span>
                      </div>
                      <div className="whitespace-pre-wrap">{message.content}</div>
                    </div>
                  </div>
                ))
              )}
              
              {isSending && (
                <div className="flex justify-start">
                  <div className="bg-muted p-3 rounded-lg flex items-center">
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    <span>AI is thinking...</span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="border-t p-4">
              <div className="relative">
                <Textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                 
                  className="min-h-[80px] pr-12"
                  disabled={isSending}
                />
                <Button
                  className="absolute bottom-2 right-2"
                  size="icon"
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isSending}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="models" className="p-4">
            <Card>
              <CardContent className="pt-6">
                <p>This is a placeholder for the Models tab. In the full version, you would see a list of available models and their details here.</p>
                {defaultSelectedModel && (
                  <p className="mt-4">
                    Currently selected model: <Badge>{defaultSelectedModel}</Badge>
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="factory" className="p-4">
            <Card>
              <CardContent className="pt-6">
                <p>This is a placeholder for the Auto Factory tab. In the full version, you would be able to create automated AI pipelines here.</p>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="settings" className="p-4">
            <Card>
              <CardContent className="pt-6">
                <p>This is a placeholder for the Settings tab. In the full version, you would be able to configure various settings for the Enterprise Model Manager Portal here.</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
