import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import {
  Send,
  Square,
  Loader2,
  Cpu,
  Zap,
  Clock,
  DollarSign,
  MessageSquare,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface StreamingMessage {
  id: string;
  type: 'start' | 'chunk' | 'end' | 'error' | 'cancel' | 'metadata';
  content: string;
  timestamp: string;
  metadata?: {
    model_id?: string;
    model_name?: string;
    stream_id?: string;
    conversation_id?: string;
    chunk_index?: number;
    total_length?: number;
    total_tokens?: number;
    duration_ms?: number;
    tokens_per_second?: number;
    full_response?: string;
    error_code?: string;
    status?: string;
  };
}

interface StreamingChatRequest {
  model_id: string;
  prompt: string;
  conversation_id?: string;
  system_prompt?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
  stream_delay?: number;
  include_thinking?: boolean;
  format_markdown?: boolean;
}

interface Model {
  id: string;
  name: string;
  provider: string;
  status: string;
  is_active: boolean;
}

interface StreamingChatInterfaceProps {
  className?: string;
  conversationId?: string;
  onConversationChange?: (conversationId: string) => void;
}

const STREAMING_STATUS = {
  IDLE: 'idle',
  CONNECTING: 'connecting',
  STREAMING: 'streaming',
  COMPLETED: 'completed',
  ERROR: 'error',
  CANCELLED: 'cancelled'
} as const;

type StreamingStatus = typeof STREAMING_STATUS[keyof typeof STREAMING_STATUS];

export const StreamingChatInterface: React.FC<StreamingChatInterfaceProps> = ({
  className,
  conversationId,
  onConversationChange
}) => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<StreamingMessage[]>([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [streamingStatus, setStreamingStatus] = useState<StreamingStatus>(STREAMING_STATUS.IDLE);
  const [streamId, setStreamId] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<StreamingMessage['metadata'] | null>(null);
  const [settings, setSettings] = useState({
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 0.9,
    stream_delay: 0.05,
    include_thinking: false,
    format_markdown: true
  });
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const { toast } = useToast();
  
  // Load available models
  useEffect(() => {
    loadModels();
  }, []);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse]);
  
  const loadModels = async () => {
    try {
      const response = await fetch('/api/models/available');
      if (response.ok) {
        const data = await response.json();
        setModels(data.models.filter((model: Model) => model.is_active));
        if (data.models.length > 0 && !selectedModel) {
          setSelectedModel(data.models[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      toast({
        title: "Failed to load models",
        description: "Please refresh the page to try again.",
        variant: "destructive",
      });
    }
  };
  
  const startStreaming = useCallback(async () => {
    if (!selectedModel || !prompt.trim()) return;
    
    setStreamingStatus(STREAMING_STATUS.CONNECTING);
    setCurrentResponse('');
    setMetadata(null);
    
    try {
      const requestData: StreamingChatRequest = {
        model_id: selectedModel,
        prompt: prompt.trim(),
        conversation_id: conversationId,
        temperature: settings.temperature,
        max_tokens: settings.max_tokens,
        top_p: settings.top_p,
        stream_delay: settings.stream_delay,
        include_thinking: settings.include_thinking,
        format_markdown: settings.format_markdown
      };
      
      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();
      
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` // Assuming JWT auth
        },
        body: JSON.stringify(requestData),
        signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) {
        throw new Error(`Streaming request failed: ${response.status}`);
      }
      
      // Create EventSource for streaming
      const eventSource = new EventSource('/api/chat/stream', {
        // Note: EventSource doesn't support POST directly
        // In a real implementation, we'd need to modify the backend to accept GET with query params
        // or use fetch with ReadableStream
      });
      
      // Alternative implementation using fetch with ReadableStream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('Response body is not readable');
      }
      
      setStreamingStatus(STREAMING_STATUS.STREAMING);
      
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              const message: StreamingMessage = {
                id: Date.now().toString(),
                ...data
              };
              
              handleStreamingMessage(message);
            } catch (e) {
              console.warn('Failed to parse SSE message:', line);
            }
          }
        }
      }
      
    } catch (error: any) {
      if (error.name === 'AbortError') {
        setStreamingStatus(STREAMING_STATUS.CANCELLED);
        toast({
          title: "Stream cancelled",
          description: "Chat stream was cancelled by user.",
        });
      } else {
        setStreamingStatus(STREAMING_STATUS.ERROR);
        toast({
          title: "Streaming failed",
          description: error.message || "Failed to start streaming chat.",
          variant: "destructive",
        });
      }
    }
  }, [selectedModel, prompt, conversationId, settings, toast]);
  
  const handleStreamingMessage = (message: StreamingMessage) => {
    switch (message.type) {
      case 'start':
        setStreamId(message.metadata?.stream_id || null);
        if (message.metadata?.conversation_id && onConversationChange) {
          onConversationChange(message.metadata.conversation_id);
        }
        toast({
          title: "Stream started",
          description: `Streaming from ${message.metadata?.model_name}`,
        });
        break;
        
      case 'chunk':
        setCurrentResponse(prev => prev + message.content);
        break;
        
      case 'metadata':
        setMetadata(message.metadata || null);
        break;
        
      case 'end':
        setStreamingStatus(STREAMING_STATUS.COMPLETED);
        // Add final message to history
        setMessages(prev => [...prev, {
          ...message,
          content: currentResponse,
          type: 'chunk'
        }]);
        toast({
          title: "Stream completed",
          description: `Received ${message.metadata?.total_tokens} tokens`,
        });
        break;
        
      case 'error':
        setStreamingStatus(STREAMING_STATUS.ERROR);
        toast({
          title: "Streaming error",
          description: message.content,
          variant: "destructive",
        });
        break;
        
      case 'cancel':
        setStreamingStatus(STREAMING_STATUS.CANCELLED);
        break;
    }
  };
  
  const cancelStreaming = async () => {
    if (streamId) {
      try {
        await fetch(`/api/chat/stream/${streamId}/cancel`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
      } catch (error) {
        console.error('Failed to cancel stream:', error);
      }
    }
    
    // Cancel fetch request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Close EventSource
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    setStreamingStatus(STREAMING_STATUS.CANCELLED);
    setStreamId(null);
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (streamingStatus === STREAMING_STATUS.STREAMING) {
      cancelStreaming();
    } else {
      // Add user message to history
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'chunk',
        content: prompt,
        timestamp: new Date().toISOString(),
        metadata: { status: 'user' }
      }]);
      startStreaming();
      setPrompt('');
    }
  };
  
  const getStatusIcon = () => {
    switch (streamingStatus) {
      case STREAMING_STATUS.CONNECTING:
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case STREAMING_STATUS.STREAMING:
        return <Zap className="h-4 w-4 text-blue-500" />;
      case STREAMING_STATUS.COMPLETED:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case STREAMING_STATUS.ERROR:
        return <XCircle className="h-4 w-4 text-red-500" />;
      case STREAMING_STATUS.CANCELLED:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <MessageSquare className="h-4 w-4" />;
    }
  };
  
  const formatTokensPerSecond = (tps?: number) => {
    if (!tps) return 'N/A';
    return `${tps.toFixed(1)} tokens/s`;
  };
  
  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    return `${(ms / 1000).toFixed(2)}s`;
  };
  
  const formatCost = (tokens?: number) => {
    if (!tokens) return 'N/A';
    // Simple cost calculation - in real app this would come from model pricing
    const costPer1K = 0.002;
    return `$${((tokens / 1000) * costPer1K).toFixed(4)}`;
  };
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon()}
              Streaming Chat
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant={streamingStatus === STREAMING_STATUS.STREAMING ? "default" : "secondary"}>
                {streamingStatus}
              </Badge>
              {metadata && (
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Cpu className="h-3 w-3" />
                    {metadata.total_tokens || 0} tokens
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(metadata.duration_ms)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    {formatTokensPerSecond(metadata.tokens_per_second)}
                  </div>
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-3 w-3" />
                    {formatCost(metadata.total_tokens)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>
      
      {/* Messages */}
      <Card>
        <CardContent className="p-4">
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.metadata?.status === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    message.metadata?.status === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-muted'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className="text-xs opacity-70 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Current streaming response */}
            {currentResponse && (
              <div className="flex justify-start">
                <div className="max-w-[80%] p-3 rounded-lg bg-muted">
                  <div className="whitespace-pre-wrap">{currentResponse}</div>
                  {streamingStatus === STREAMING_STATUS.STREAMING && (
                    <div className="flex items-center gap-1 mt-2">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span className="text-xs text-muted-foreground">Streaming...</span>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>
      
      {/* Input Form */}
      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Model Selection */}
            <div className="flex items-center gap-2">
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {model.provider}
                        </Badge>
                        {model.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Button type="button" variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Prompt Input */}
            <div className="flex gap-2">
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your message..."
                className="flex-1 min-h-[60px]"
                disabled={streamingStatus === STREAMING_STATUS.STREAMING}
              />
              <Button
                type="submit"
                disabled={!selectedModel || (!prompt.trim() && streamingStatus !== STREAMING_STATUS.STREAMING)}
                className="px-6"
              >
                {streamingStatus === STREAMING_STATUS.STREAMING ? (
                  <>
                    <Square className="h-4 w-4 mr-2" />
                    Stop
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Send
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      
      {/* Error Display */}
      {streamingStatus === STREAMING_STATUS.ERROR && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Streaming encountered an error. Please try again.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};