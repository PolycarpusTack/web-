// src/pages/ChatPage.tsx
import { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { conversationsApi, Conversation, Message } from "@/api/conversations";
import { AlertCircle, ChevronLeft, MessageSquare, RefreshCw, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useToast } from "@/components/ui/use-toast";
import { formatTimeAgo } from "@/lib/shared-utils";
import HomePage from "./HomePage";
import { Skeleton } from "@/components/ui/skeleton";

interface ChatPageProps {
  conversationId?: string;
}

export default function ChatPage({ conversationId }: ChatPageProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
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
        setMessages(response.data.messages || []);
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
  
  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  // Send message
  const sendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    if (!message.trim() || !conversation) return;
    
    try {
      setSending(true);
      
      // Add user message to UI immediately for better UX
      const tempUserMessage: Message = {
        id: `temp-${Date.now()}`,
        content: message,
        role: "user" as any,
        created_at: new Date().toISOString(),
        conversation_id: conversation.id,
        user_id: user?.id || null,
        meta_data: null,
        tokens: null,
        cost: null,
        parent_id: null,
        thread_id: null,
        updated_at: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, tempUserMessage]);
      scrollToBottom();
      
      // Clear input
      setMessage("");
      
      // Send to API
      const response = await conversationsApi.sendMessage({
        model_id: conversation.model_id,
        prompt: message,
        conversation_id: conversation.id,
        stream: false
      });
      
      if (response.success) {
        // Add both messages (replace temp with real)
        const updatedMessages = messages.filter(m => m.id !== tempUserMessage.id);
        
        // Create user message from response
        const userMessage: Message = {
          id: `user-${Date.now()}`,
          content: message,
          role: "user" as any,
          created_at: new Date().toISOString(),
          conversation_id: conversation.id,
          user_id: user?.id || null,
          meta_data: null,
          tokens: response.data?.usage?.prompt_tokens || null,
          cost: response.data?.usage?.costs?.input_cost || null,
          parent_id: null,
          thread_id: null,
          updated_at: new Date().toISOString()
        };
        
        // Create assistant message from response
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          content: response.data?.content || "No response",
          role: "assistant" as any,
          created_at: new Date().toISOString(),
          conversation_id: conversation.id,
          user_id: null,
          meta_data: null,
          tokens: response.data?.usage?.completion_tokens || null,
          cost: response.data?.usage?.costs?.output_cost || null,
          parent_id: null,
          thread_id: null,
          updated_at: new Date().toISOString()
        };
        
        // Update messages
        setMessages([...updatedMessages, userMessage, assistantMessage]);
        
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
      setTimeout(scrollToBottom, 100);
    }
  };
  
  // Load conversation on mount
  useEffect(() => {
    loadConversation();
  }, [loadConversation]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
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
  
  // Render message item
  const renderMessage = (message: Message) => {
    const isUser = message.role === "user";
    
    return (
      <div 
        key={message.id} 
        className={`flex gap-3 ${isUser ? 'justify-start' : 'justify-start'} mb-4`}
      >
        <div className="flex-shrink-0">
          {isUser ? (
            <Avatar>
              <AvatarImage src={`https://avatar.vercel.sh/${user?.username}`} />
              <AvatarFallback>{userInitials}</AvatarFallback>
            </Avatar>
          ) : (
            <Avatar>
              <AvatarImage src={`https://avatar.vercel.sh/model_${conversation?.model_id?.split(':')[0]}`} />
              <AvatarFallback>{modelInitials}</AvatarFallback>
            </Avatar>
          )}
        </div>
        
        <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-start' : 'items-start'}`}>
          <div className="flex items-center mb-1">
            <span className="font-semibold text-sm">
              {isUser ? user?.username : conversation?.model_id?.split(':')[0]}
            </span>
            <span className="text-xs text-gray-500 ml-2">
              {formatTimeAgo(message.created_at)}
            </span>
          </div>
          
          <div className={`p-3 rounded-lg ${
            isUser ? 'bg-primary/10 text-primary-foreground/90' : 'bg-card text-card-foreground border'
          }`}>
            {message.content}
          </div>
        </div>
      </div>
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
        
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading && messages.length === 0 ? (
            <div className="space-y-4">
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
            <>
              {messages.map(renderMessage)}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
        
        {/* Message input */}
        <div className="border-t p-4">
          <form onSubmit={sendMessage} className="flex items-end gap-2">
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
             
              className="flex-1 min-h-[80px]"
              disabled={sending || loading || !conversation}
            />
            <Button 
              type="submit" 
              size="icon" 
              className="h-10 w-10"
              disabled={sending || loading || !message.trim() || !conversation}
            >
              {sending ? (
                <RefreshCw className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </form>
        </div>
      </div>
    </HomePage>
  );
}