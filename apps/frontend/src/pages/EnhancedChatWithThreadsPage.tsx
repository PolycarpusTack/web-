// src/pages/EnhancedChatWithThreadsPage.tsx
import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { 
  conversationsApi, 
  Conversation, 
  Message, 
  MessageThread 
} from "@/api/conversations";
import { filesApi } from "@/api/files";
import { AlertCircle, ChevronLeft, Copy, Layers, MessageSquare, Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import HomePage from "./HomePage";
import { Skeleton } from "@/components/ui/skeleton";
import ThreadedMessageList from "@/components/chat/ThreadedMessageList";
import EnhancedMessageInput from "@/components/chat/EnhancedMessageInput";
import ContextWindow from "@/components/chat/ContextWindow";
import CreateThreadDialog from "@/components/chat/CreateThreadDialog";
import FileAnalysisModal from "@/components/chat/FileAnalysisModal";

interface ModelSettings {
  temperature: number;
  maxTokens: number;
  topP: number;
  streamResponse: boolean;
}

interface EnhancedChatWithThreadsPageProps {
  conversationId?: string;
}

export default function EnhancedChatWithThreadsPage({ conversationId }: EnhancedChatWithThreadsPageProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [threads, setThreads] = useState<MessageThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [usedTokens, setUsedTokens] = useState(0);
  const [modelSettings, setModelSettings] = useState<ModelSettings>({
    temperature: 0.7,
    maxTokens: 2000,
    topP: 0.95,
    streamResponse: true
  });
  
  // Dialogs state
  const [createThreadDialogOpen, setCreateThreadDialogOpen] = useState(false);
  const [threadDialogBasedOnMessage, setThreadDialogBasedOnMessage] = useState<Message | undefined>(undefined);
  const [fileAnalysisModalOpen, setFileAnalysisModalOpen] = useState(false);
  const [selectedMessageForAnalysis, setSelectedMessageForAnalysis] = useState<string | null>(null);
  
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
      const conversationResponse = await conversationsApi.getById(id);
      
      if (conversationResponse.success && conversationResponse.data) {
        setConversation(conversationResponse.data);
        
        // Get conversation messages (without thread messages)
        const rootMessages = (conversationResponse.data.messages || []).filter(
          msg => !msg.thread_id
        );
        
        setMessages(rootMessages);
        
        // Calculate total tokens
        const totalTokens = rootMessages.reduce(
          (sum, msg) => sum + (msg.tokens || 0), 
          0
        );
        setUsedTokens(totalTokens);
        
        // Load threads for this conversation
        const threadsResponse = await conversationsApi.threads.getByConversation(id);
        
        if (threadsResponse.success) {
          setThreads(threadsResponse.data?.threads || []);
        }
        
        setError("");
      } else {
        throw new Error(conversationResponse.error);
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
  
  // Load thread messages
  const loadThread = async (threadId: string) => {
    try {
      setActiveThreadId(threadId);
      
      const threadResponse = await conversationsApi.threads.getById(threadId);
      
      if (threadResponse.success) {
        // Update the thread in our thread list
        setThreads(prev => prev.map(t => 
          t.id === threadId && threadResponse.data ? threadResponse.data : t
        ));
      }
    } catch (err) {
      console.error("Error loading thread:", err);
      toast({
        title: "Error",
        description: "Could not load thread messages.",
        variant: "destructive",
      });
    }
  };
  
  // Send message
  const sendMessage = async (content: string, files?: File[], threadId?: string) => {
    if (!content.trim() && (!files || files.length === 0) || !conversation) return;
    
    // Add user message to UI immediately for better UX
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      content: content,
      role: "user" as any,
      created_at: new Date().toISOString(),
      conversation_id: conversation.id,
      user_id: user?.id || null,
      thread_id: threadId || null,
      meta_data: files && files.length > 0 ? { hasFiles: true, fileCount: files.length } : null,
      tokens: null,
      cost: null,
      parent_id: null,
      updated_at: new Date().toISOString()
    };
    
    try {
      setSending(true);
      
      if (threadId) {
        // Update the thread's messages
        setThreads(prev => prev.map(thread => {
          if (thread.id === threadId) {
            return {
              ...thread,
              messages: [...(thread.messages || []), tempUserMessage]
            };
          }
          return thread;
        }));
      } else {
        // Update the main conversation messages
        setMessages(prev => [...prev, tempUserMessage]);
      }
      
      // Upload files first if there are any
      if (files && files.length > 0) {
        try {
          const uploadResponse = await filesApi.uploadFilesToConversation(
            files, 
            conversation.id,
            threadId ? `thread_${threadId}` : undefined
          );
          
          if (!uploadResponse.success) {
            throw new Error("File upload failed");
          }
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
      const apiCall = threadId 
        ? conversationsApi.threads.sendMessage(threadId, {
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
          })
        : conversationsApi.sendMessage({
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
      
      const response = await apiCall;
      
      if (response.success) {
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
          thread_id: threadId || null,
          meta_data: files && files.length > 0 ? { hasFiles: true, fileCount: files.length } : null,
          parent_id: null,
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
          thread_id: threadId || null,
          meta_data: null,
          parent_id: null,
          updated_at: new Date().toISOString()
        };
        
        if (threadId) {
          // Update the thread's messages, removing the temp message
          setThreads(prev => prev.map(thread => {
            if (thread.id === threadId) {
              const updatedMessages = (thread.messages || []).filter(m => m.id !== tempUserMessage.id);
              return {
                ...thread,
                messages: [...updatedMessages, userMessage, assistantMessage]
              };
            }
            return thread;
          }));
        } else {
          // Update the main conversation messages, removing the temp message
          const updatedMessages = messages.filter(m => m.id !== tempUserMessage.id);
          setMessages([...updatedMessages, userMessage, assistantMessage]);
        }
        
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
      if (threadId) {
        setThreads(prev => prev.map(thread => {
          if (thread.id === threadId) {
            return {
              ...thread,
              messages: (thread.messages || []).filter(m => m.id !== tempUserMessage.id)
            };
          }
          return thread;
        }));
      } else {
        setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id));
      }
    } finally {
      setSending(false);
    }
  };
  
  // Create a new thread
  const handleCreateThread = async (title: string, basedOnMessageId?: string) => {
    if (!conversation) return;
    
    try {
      const response = await conversationsApi.threads.create({
        conversation_id: conversation.id,
        title: title
      });
      
      if (response.success) {
        // Add the new thread to our list
        setThreads(prev => [...prev, ...(response.data ? [response.data] : [])]);
        if (response.data?.id) {
          setActiveThreadId(response.data.id);
        }
        
        toast({
          title: "Thread created",
          description: `Thread "${title}" has been created.`
        });
        
        // If based on a message, reply to it in the new thread
        if (basedOnMessageId) {
          const message = messages.find(m => m.id === basedOnMessageId);
          if (message) {
            await sendMessage(`Continuing from: "${message.content.substring(0, 50)}${message.content.length > 50 ? '...' : ''}"`, undefined, response.data?.id);
          }
        }
        
        return response.data?.id;
      } else {
        throw new Error(response.error);
      }
    } catch (err) {
      console.error("Error creating thread:", err);
      toast({
        title: "Thread creation failed",
        description: "Could not create thread.",
        variant: "destructive",
      });
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
    const messageToDelete = [...messages, ...threads.flatMap(t => t.messages || [])].find(m => m.id === messageId);
    if (!messageToDelete) return;
    
    const tokensToRemove = messageToDelete.tokens || 0;
    
    if (messageToDelete.thread_id) {
      // Update thread messages
      setThreads(prev => prev.map(thread => {
        if (thread.id === messageToDelete.thread_id) {
          return {
            ...thread,
            messages: (thread.messages || []).filter(m => m.id !== messageId)
          };
        }
        return thread;
      }));
    } else {
      // Update main conversation messages
      setMessages(prev => prev.filter(m => m.id !== messageId));
    }
    
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
      })),
      threads: threads.map(t => ({
        id: t.id,
        title: t.title,
        messages: t.messages?.map(m => ({
          role: m.role,
          content: m.content,
          created_at: m.created_at,
          tokens: m.tokens
        }))
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
    let messagesToSearch;
    
    if (message.thread_id) {
      // Find the thread this message belongs to
      const thread = threads.find(t => t.id === message.thread_id);
      if (!thread || !thread.messages) return;
      messagesToSearch = thread.messages;
    } else {
      messagesToSearch = messages;
    }
    
    const messageIndex = messagesToSearch.findIndex(m => m.id === message.id);
    if (messageIndex <= 0) return;
    
    // Find the most recent user message
    let lastUserMessageIndex = -1;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messagesToSearch[i].role === "user") {
        lastUserMessageIndex = i;
        break;
      }
    }
    
    if (lastUserMessageIndex === -1) return;
    
    // Use that message content to regenerate
    const userMessage = messagesToSearch[lastUserMessageIndex];
    
    if (message.thread_id) {
      // Remove the assistant message from the thread
      setThreads(prev => prev.map(thread => {
        if (thread.id === message.thread_id) {
          return {
            ...thread,
            messages: (thread.messages || []).filter((_, index) => index !== messageIndex)
          };
        }
        return thread;
      }));
      
      // Send the message to the thread
      sendMessage(userMessage.content, undefined, message.thread_id);
    } else {
      // Remove the assistant message and send the user message again
      setMessages(prev => prev.filter((_, index) => index !== messageIndex));
      sendMessage(userMessage.content);
    }
  };
  
  // Handle thread creation
  const openThreadCreationDialog = (message?: Message) => {
    setThreadDialogBasedOnMessage(message);
    setCreateThreadDialogOpen(true);
  };
  
  // Handle file analysis
  const openFileAnalysisModal = (messageId: string) => {
    setSelectedMessageForAnalysis(messageId);
    setFileAnalysisModalOpen(true);
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
                {threads.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    <Layers className="h-3 w-3 mr-1" />
                    {threads.length} {threads.length === 1 ? 'thread' : 'threads'}
                  </Badge>
                )}
              </>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => openThreadCreationDialog()}
              title="Create a new thread"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Thread
            </Button>
            
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
        
        {/* Messages area with thread support */}
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
          ) : messages.length === 0 && threads.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <MessageSquare className="h-12 w-12 text-gray-300 mb-2" />
              <p className="text-gray-500">Start a conversation by sending a message.</p>
            </div>
          ) : (
            <ThreadedMessageList
              messages={messages}
              threads={threads}
              activeThreadId={activeThreadId || undefined}
              userInitials={userInitials}
              modelInitials={modelInitials}
              userAvatarUrl={`https://avatar.vercel.sh/${user?.username}`}
              modelAvatarUrl={`https://avatar.vercel.sh/model_${conversation?.model_id?.split(':')[0]}`}
              username={user?.username}
              modelName={conversation?.model_id?.split(':')[0]}
              loading={loading}
              onEditMessage={handleEditMessage}
              onDeleteMessage={handleDeleteMessage}
              onReplyToMessage={(message) => sendMessage(`Replying to: "${message.content.substring(0, 50)}${message.content.length > 50 ? '...' : ''}"\n\n`)}
              onReplyInThread={(message, threadId) => {
                if (threadId) {
                  const replyPrefix = message.id ? `Replying to: "${message.content.substring(0, 50)}${message.content.length > 50 ? '...' : ''}"\n\n` : '';
                  sendMessage(replyPrefix, undefined, threadId);
                }
              }}
              onCreateThread={openThreadCreationDialog}
              onSelectThread={loadThread}
              onRetryGeneration={handleRetryGeneration}
            />
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
        <EnhancedMessageInput
          onSend={async (content, files) => {
            if (activeThreadId) {
              await sendMessage(content, files, activeThreadId);
            } else {
              await sendMessage(content, files);
            }
          }}
          disabled={loading || !conversation}
          loading={sending}
          showModelSettings={true}
          initialModelSettings={modelSettings}
          onModelSettingsChange={setModelSettings}
          conversationId={conversation?.id}
        />
        
        {/* Thread Creation Dialog */}
        <CreateThreadDialog
          conversationId={conversation?.id || ''}
          basedOnMessage={threadDialogBasedOnMessage}
          open={createThreadDialogOpen}
          onOpenChange={setCreateThreadDialogOpen}
          onCreateThread={async (title: string, basedOnMessageId?: string) => {
            await handleCreateThread(title, basedOnMessageId);
          }}
        />
        
        {/* File Analysis Modal */}
        <FileAnalysisModal
          open={fileAnalysisModalOpen}
          onOpenChange={setFileAnalysisModalOpen}
          messageId={selectedMessageForAnalysis || undefined}
        />
      </div>
    </HomePage>
  );
}