import { useState, useEffect, useRef, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
  id: string;
  sender_id?: string;
  room_id?: string;
}

interface WebSocketOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface WebSocketHook {
  isConnected: boolean;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';
  lastMessage: WebSocketMessage | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (type: string, data: any, roomId?: string) => void;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
  error: string | null;
}

export const useWebSocket = (
  endpoint: string,
  options: WebSocketOptions = {}
): WebSocketHook => {
  const {
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected' | 'reconnecting'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const getToken = useCallback(() => {
    // Get token from localStorage or your auth context
    return localStorage.getItem('token') || '';
  }, []);

  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval > 0) {
      heartbeatIntervalRef.current = setInterval(() => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          sendMessage('ping', {});
        }
      }, heartbeatInterval);
    }
  }, [heartbeatInterval]);

  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState('connecting');
    setError(null);

    try {
      const token = getToken();
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}${endpoint}?token=${encodeURIComponent(token)}`;
      
      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        setIsConnected(true);
        setConnectionState('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;
        startHeartbeat();
        onConnect?.();
      };

      websocketRef.current.onclose = (event) => {
        setIsConnected(false);
        clearTimeouts();
        
        if (event.code !== 1000 && reconnectAttemptsRef.current < reconnectAttempts) {
          // Attempt to reconnect
          setConnectionState('reconnecting');
          reconnectAttemptsRef.current++;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          setConnectionState('disconnected');
          onDisconnect?.();
        }
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          // Handle system messages
          if (message.type === 'ping') {
            sendMessage('pong', {});
          } else if (message.type === 'error') {
            setError(message.data.error || 'WebSocket error');
          }
          
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          setError('Failed to parse message');
        }
      };

      websocketRef.current.onerror = (event) => {
        setError('WebSocket connection error');
        onError?.(event);
      };

    } catch (error) {
      setError('Failed to create WebSocket connection');
      setConnectionState('disconnected');
    }
  }, [endpoint, getToken, reconnectAttempts, reconnectInterval, startHeartbeat, onConnect, onDisconnect, onMessage, onError]);

  const disconnect = useCallback(() => {
    clearTimeouts();
    
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Manual disconnect');
      websocketRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionState('disconnected');
    reconnectAttemptsRef.current = reconnectAttempts; // Prevent auto-reconnect
  }, [reconnectAttempts]);

  const sendMessage = useCallback((type: string, data: any, roomId?: string) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        type,
        data,
        room_id: roomId,
        timestamp: Date.now(),
        id: Math.random().toString(36).substr(2, 9)
      };
      
      websocketRef.current.send(JSON.stringify(message));
    } else {
      setError('WebSocket is not connected');
    }
  }, []);

  const joinRoom = useCallback((roomId: string) => {
    sendMessage('custom', { action: 'join_room', room_id: roomId });
  }, [sendMessage]);

  const leaveRoom = useCallback((roomId: string) => {
    sendMessage('custom', { action: 'leave_room', room_id: roomId });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeouts();
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [clearTimeouts]);

  return {
    isConnected,
    connectionState,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    joinRoom,
    leaveRoom,
    error
  };
};

// Specialized hooks for different WebSocket endpoints
export const useChatWebSocket = (conversationId?: string) => {
  const endpoint = conversationId ? `/api/ws/chat/${conversationId}` : '/api/ws/connect';
  
  return useWebSocket(endpoint, {
    onMessage: (message) => {
      // Handle chat-specific messages
      if (message.type === 'message') {
        console.log('New chat message:', message.data);
      } else if (message.type === 'typing_start') {
        console.log('User started typing:', message.data);
      } else if (message.type === 'typing_stop') {
        console.log('User stopped typing:', message.data);
      }
    }
  });
};

export const useAnalyticsWebSocket = () => {
  return useWebSocket('/api/ws/analytics', {
    onMessage: (message) => {
      if (message.type === 'analytics_update') {
        console.log('Analytics update:', message.data);
      }
    }
  });
};

export const useAdminWebSocket = () => {
  return useWebSocket('/api/ws/admin', {
    onMessage: (message) => {
      if (message.type === 'custom') {
        console.log('Admin message:', message.data);
      }
    }
  });
};