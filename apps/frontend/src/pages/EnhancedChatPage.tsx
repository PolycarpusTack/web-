// src/pages/EnhancedChatPage.tsx
import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { conversationsApi, Conversation, Message } from "@/api/conversations";
import { filesApi } from "@/api/files";
import { AlertCircle, ChevronLeft, Copy, MessageSquare, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import HomePage from "./HomePage";
import { Skeleton } from "@/components/ui/skeleton";
import MessageList from "@/components/chat/MessageList";
import { UnifiedMessageInput } from "@/components/chat/UnifiedMessageInput";
import { useModelSettings } from "@/hooks/useModelSettings";
import ContextWindow from "@/components/chat/ContextWindow";
import MessageWithAttachments from "@/components/chat/MessageWithAttachments";
import { formatTimeAgo } from "@/lib/shared-utils";

interface EnhancedChatPageProps {
  conversationId?: string;
}

export default function EnhancedChatPage({ conversationId }: EnhancedChatPageProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [usedTokens, setUsedTokens] = useState(0);
  const { settings: modelSettings, updateSettings: setModelSettings } = useModelSettings({
    temperature: 0.7,
    maxTokens: 2000,
    topP: 0.95,
    streamResponse: true
  });
  
  // Extract conversation ID from URL if not provided
  const getConversationId = useCallback(() => {
    if (conversationId) return conversationId;
    
    // Parse ID from URL path
    const path = window.location.pathname;
    const match = path.match(/\/chat\/([^/]+)/);
    return match ? match[1] : null;
  }, [conversationId]);
  
  // Load conversation and messages
  const loadConversation = useCallback(async () => {
    const id = getConversationId();
    if (!id) {
      setError("No conversation ID provided");
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const response = await conversationsApi.getById(id);
      
      if (response.success && response.data) {
        setConversation(response.data);
        setMessages(response.data?.messages || []);
        
        // Calculate total tokens
        const totalTokens = (response.data?.messages || []).reduce(
          (sum, msg) => sum + (msg.tokens || 0), 
          0
        );
        setUsedTokens(totalTokens);
        setError("");
      } else {
        throw new Error(response.error);
      }
    } catch (err) {
      console.error(err);
      setError("Error loading conversation");
      toast({
        title: "Error",
        description: "Could not load conversation.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [getConversationId, toast]);
  
  // Send message
  const sendMessage = async (content: string, files?: File[]) => {
    if (!content.trim() && (!files || files.length === 0) || !conversation) return;
    
    try {
      setSending(true);
      
      // Add user message to UI immediately for better UX
      const tempUserMessage: Message = {
        id: `temp-${Date.now()}`,
        content: content,
        role: "user" as any,
        created_at: new Date().toISOString(),
        conversation_id: conversation.id,
        meta_data: files && files.length > 0 ? { hasFiles: true, fileCount: files.length } : null,
        user_id: user?.id || null,
        tokens: null,
        cost: null,
        parent_id: null,
        thread_id: null,
        updated_at: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, tempUserMessage]);
      
      // Upload files first if there are any
      if (files && files.length > 0) {
        try {
          const uploadResponse = await filesApi.uploadFilesToConversation(files, conversation.id);
          if (!uploadResponse.success) {
            throw new Error("File upload failed");
          }
          console.log("Files uploaded:", uploadResponse.data);
        } catch (error) {
          console.error("Error uploading files:", error);
          toast({
            title: "File upload failed",
            description: "Could not upload files, but will attempt to send message.",
            variant: "destructive",
          });
        }
      }
      
      // Send to API with model settings
      const response = await conversationsApi.sendMessage({
        model_id: conversation.model_id,
        prompt: content,
        conversation_id: conversation.id,
        stream: false,
        options: {
          temperature: modelSettings.temperature,
          max_tokens: modelSettings.maxTokens,
          top_p: modelSettings.topP,
          stream: modelSettings.streamResponse
        }
      });
      
      if (response.success) {
        // Add both messages (replace temp with real)
        const updatedMessages = messages.filter(m => m.id !== tempUserMessage.id);
        
        // Create user message from response
        const userMessage: Message = {
          id: `user-${Date.now()}`,
          content: content,
          role: "user" as any,
          created_at: new Date().toISOString(),
          conversation_id: conversation.id,
          user_id: user?.id || null,
          tokens: response.data?.usage?.prompt_tokens || null,
          cost: response.data?.usage?.costs?.input_cost || null,
          meta_data: files && files.length > 0 ? { hasFiles: true, fileCount: files.length } : null,
          parent_id: null,
          thread_id: null,
          updated_at: new Date().toISOString()
        };
        
        // Create assistant message from response
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          content: response.data?.content || '',
          role: "assistant" as any,
          created_at: new Date().toISOString(),
          conversation_id: conversation.id,
          user_id: null,
          tokens: response.data?.usage?.completion_tokens || null,
          cost: response.data?.usage?.costs?.output_cost || null,
          meta_data: null,
          parent_id: null,
          thread_id: null,
          updated_at: new Date().toISOString()
        };
        
        // Update messages
        setMessages([...updatedMessages, userMessage, assistantMessage]);
        
        // Update token usage
        setUsedTokens(prev => prev + (response.data?.usage?.total_tokens || 0));
        
        // Refresh the conversation to get updated message list
        loadConversation();
      } else {
        throw new Error(response.error);
      }
    } catch (err) {
      console.error("Error sending message:", err);
      toast({
        title: "Message failed",
        description: "Could not send message.",
        variant: "destructive",
      });
      
      // Remove the temporary message if it failed
      setMessages(prev => prev.filter(m => m.id !== `temp-${Date.now()}`));
    } finally {
      setSending(false);
    }
  };
  
  // Handle message editing
  const handleEditMessage = (message: Message) => {
    toast({
      title: "Edit Message",
      description: "Message editing is coming soon."
    });
  };
  
  // Handle message deletion
  const handleDeleteMessage = async (messageId: string) => {
    // Optimistic UI update
    const messageToDelete = messages.find(m => m.id === messageId);
    if (!messageToDelete) return;
    
    const tokensToRemove = messageToDelete.tokens || 0;
    
    // Update UI immediately
    setMessages(prev => prev.filter(m => m.id !== messageId));
    setUsedTokens(prev => Math.max(0, prev - tokensToRemove));
    
    // In a real implementation, you would call an API here
    toast({
      title: "Message deleted",
      description: "The message has been removed."
    });
  };
  
  // Handle context pruning
  const handlePruneContext = (messageIds: string[]) => {
    const messagesToRemove = messages.filter(m => messageIds.includes(m.id));
    const tokensToRemove = messagesToRemove.reduce((sum, m) => sum + (m.tokens || 0), 0);
    
    // Update UI
    setMessages(prev => prev.filter(m => !messageIds.includes(m.id)));
    setUsedTokens(prev => Math.max(0, prev - tokensToRemove));
    
    toast({
      title: "Context pruned",
      description: `Removed ${messageIds.length} messages (${tokensToRemove} tokens).`
    });
  };
  
  // Handle context export
  const handleExportContext = () => {
    const exportData = {
      conversation: {
        id: conversation?.id,
        title: conversation?.title,
        model_id: conversation?.model_id,
        created_at: conversation?.created_at,
        system_prompt: conversation?.system_prompt
      },
      messages: messages.map(m => ({
        role: m.role,
        content: m.content,
        created_at: m.created_at,
        tokens: m.tokens
      }))
    };
    
    // Create file and trigger download
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
    
    const exportFileDefaultName = `conversation-${conversation?.id}-${new Date().toISOString().slice(0, 10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    toast({
      title: "Conversation exported",
      description: "The conversation has been exported as JSON."
    });
  };
  
  // Handle retry generation (regenerate response)
  const handleRetryGeneration = (message: Message) => {
    // Find the last user message before this assistant message
    const messageIndex = messages.findIndex(m => m.id === message.id);
    if (messageIndex <= 0) return;
    
    // Find the most recent user message
    let lastUserMessageIndex = -1;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        lastUserMessageIndex = i;
        break;
      }
    }
    
    if (lastUserMessageIndex === -1) return;
    
    // Use that message content to regenerate
    const userMessage = messages[lastUserMessageIndex];
    
    // Remove the assistant message and send the user message again
    setMessages(prev => prev.filter((_, index) => index !== messageIndex));
    sendMessage(userMessage.content);
  };
  
  // Load conversation on mount
  useEffect(() => {
    loadConversation();
  }, [loadConversation]);
  
  // Navigate back to conversations list
  const navigateToConversations = () => {
    if ((window as any).navigate) {
      (window as any).navigate('/conversations');
    }
  };
  
  // Generate model avatar fallback
  const modelInitials = conversation?.model_id?.split(':')[0]?.slice(0, 2)?.toUpperCase() || "AI";
  
  // User avatar fallback
  const userInitials = user?.username?.slice(0, 2)?.toUpperCase() || "U";
  
  // Custom message renderer with attachments
  const renderEnhancedMessage = (message: Message) => {
    return (
      <MessageWithAttachments
        key={message.id}
        message={message}
        userInitials={userInitials}
        modelInitials={modelInitials}
        userAvatarUrl={`https://avatar.vercel.sh/${user?.username}`}
        modelAvatarUrl={`https://avatar.vercel.sh/model_${conversation?.model_id?.split(':')[0]}`}
        username={user?.username}
        modelName={conversation?.model_id?.split(':')[0]}
        isLastMessage={message.id === messages[messages.length - 1]?.id}
        onEdit={handleEditMessage}
        onDelete={handleDeleteMessage}
        onRetry={message.role === 'assistant' ? handleRetryGeneration : undefined}
      />
    );
  };
  
  // Empty state - no conversation found
  if (!loading && !conversation && !error) {
    return (
      <HomePage>
        <div className="flex flex-col items-center justify-center h-[70vh]">
          <MessageSquare className="h-16 w-16 text-gray-300 mb-4" />
          <h2 className="text-xl font-bold mb-2">No Conversation Selected</h2>
          <p className="text-gray-500 mb-4">Select a conversation or create a new one.</p>
          <Button onClick={navigateToConversations}>
            Go to Conversations
          </Button>
        </div>
      </HomePage>
    );
  }
  
  // Error state
  if (error && !conversation) {
    return (
      <HomePage>
        <div className="p-6 flex flex-col items-center justify-center min-h-[300px]">
          <div className="text-center">
            <AlertCircle className="h-10 w-10 text-red-500 mb-2 mx-auto" />
            <h2 className="text-xl font-bold mb-2">An error occurred</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-4">{error}</p>
            <Button onClick={() => loadConversation()}>Try again</Button>
          </div>
        </div>
      </HomePage>
    );
  }
  
  return (
    <HomePage>
      <div className="flex flex-col h-[calc(100vh-4rem)]">
        {/* Chat header */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={navigateToConversations}
              className="mr-2"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
            
            {loading && !conversation ? (
              <Skeleton className="h-6 w-48" />
            ) : (
              <>
                <h2 className="font-semibold text-lg mr-2">{conversation?.title}</h2>
                <Badge variant="outline">{conversation?.model_id?.split(':')[0]}</Badge>
              </>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportContext}
              title="Export conversation"
            >
              <Copy className="h-4 w-4 mr-2" />
              Export
            </Button>
            
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => loadConversation()}
              disabled={loading}
            >
              {loading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
        
        {/* Messages area with custom renderer */}
        <div className="flex-1 overflow-y-auto">
          {loading && messages.length === 0 ? (
            <div className="space-y-4 p-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-3 mb-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-16 w-64" />
                  </div>
                </div>
              ))}
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <MessageSquare className="h-12 w-12 text-gray-300 mb-2" />
              <p className="text-gray-500">Start a conversation by sending a message.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {messages.map(renderEnhancedMessage)}
            </div>
          )}
        </div>
        
        {/* Context window */}
        <ContextWindow
          messages={messages}
          maxTokens={4000} // This should come from model config
          usedTokens={usedTokens}
          onPruneContext={handlePruneContext}
          onExportContext={handleExportContext}
          onClearContext={() => {
            setMessages([]);
            setUsedTokens(0);
            toast({
              title: "Context cleared",
              description: "All messages have been removed from the context window."
            });
          }}
        />
        
        {/* Message input */}
        <UnifiedMessageInput
          onSend={sendMessage}
          disabled={loading || !conversation}
          loading={sending}
          enhanced={true}
          showModelSettings={true}
          initialModelSettings={modelSettings}
          onModelSettingsChange={setModelSettings}
          conversationId={conversation?.id}
        />
      </div>
    </HomePage>
  );
}