/**
 * Model Status Display Component
 * Shows real-time model status updates using WebSocket
 */

import React, { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, Check, Download, Loader2, X } from "lucide-react";
import { useWebSocket, ConnectionState } from '@/lib/websocket-client';
import { apiClient } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';

interface Model {
  id: string;
  name: string;
  provider: string;
  size?: string;
  status: string;
  is_active: boolean;
  is_local: boolean;
  context_window: number;
  description?: string;
  metadata?: Record<string, any>;
}

interface ModelStatusUpdate {
  type: 'model_update';
  model_id: string;
  status: string;
  details?: {
    message?: string;
    progress?: number;
    [key: string]: any;
  };
}

export function ModelStatusDisplay() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [startingModel, setStartingModel] = useState<string | null>(null);
  const [stoppingModel, setStoppingModel] = useState<string | null>(null);
  
  const { state, lastMessage, subscribe, unsubscribe, isConnected } = useWebSocket();
  const { toast } = useToast();

  // Fetch initial models
  useEffect(() => {
    fetchModels();
  }, []);

  // Subscribe to model updates
  useEffect(() => {
    if (isConnected) {
      subscribe(['models', 'model:*']);
      
      return () => {
        unsubscribe(['models', 'model:*']);
      };
    }
  }, [isConnected, subscribe, unsubscribe]);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage?.type === 'model_update') {
      const update = lastMessage as ModelStatusUpdate;
      
      // Update model status
      setModels(prev => prev.map(model => 
        model.id === update.model_id 
          ? { ...model, status: update.status }
          : model
      ));

      // Show toast notification
      if (update.details?.message) {
        toast({
          title: `Model ${update.model_id}`,
          description: update.details.message,
          variant: update.status === 'error' ? 'destructive' : 'default',
        });
      }
    }
  }, [lastMessage, toast]);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{ models: Model[]; total: number }>('/api/models');
      setModels(response.models);
    } catch (error) {
      console.error('Failed to fetch models:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch models',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const startModel = async (modelId: string) => {
    try {
      setStartingModel(modelId);
      await apiClient.post('/api/models/start', { model_id: modelId });
    } catch (error) {
      console.error('Failed to start model:', error);
      toast({
        title: 'Error',
        description: 'Failed to start model',
        variant: 'destructive',
      });
    } finally {
      setStartingModel(null);
    }
  };

  const stopModel = async (modelId: string) => {
    try {
      setStoppingModel(modelId);
      await apiClient.post('/api/models/stop', { model_id: modelId });
    } catch (error) {
      console.error('Failed to stop model:', error);
      toast({
        title: 'Error',
        description: 'Failed to stop model',
        variant: 'destructive',
      });
    } finally {
      setStoppingModel(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return (
          <Badge variant="default" className="bg-green-500">
            <Check className="w-3 h-3 mr-1" />
            Running
          </Badge>
        );
      case 'starting':
        return (
          <Badge variant="default" className="bg-blue-500">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Starting
          </Badge>
        );
      case 'downloading':
        return (
          <Badge variant="default" className="bg-purple-500">
            <Download className="w-3 h-3 mr-1" />
            Downloading
          </Badge>
        );
      case 'stopped':
        return (
          <Badge variant="secondary">
            <X className="w-3 h-3 mr-1" />
            Stopped
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="destructive">
            <AlertCircle className="w-3 h-3 mr-1" />
            Error
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {status}
          </Badge>
        );
    }
  };

  const getConnectionBadge = () => {
    switch (state) {
      case ConnectionState.CONNECTED:
        return (
          <Badge variant="default" className="bg-green-500">
            <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse" />
            Connected
          </Badge>
        );
      case ConnectionState.CONNECTING:
      case ConnectionState.RECONNECTING:
        return (
          <Badge variant="default" className="bg-yellow-500">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Connecting
          </Badge>
        );
      case ConnectionState.ERROR:
      case ConnectionState.DISCONNECTED:
        return (
          <Badge variant="destructive">
            <X className="w-3 h-3 mr-1" />
            Disconnected
          </Badge>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Model Status</h2>
        <div className="flex items-center gap-4">
          {getConnectionBadge()}
          <Button onClick={fetchModels} variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </div>

      {models.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">No models available</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {models.map((model) => (
            <Card key={model.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{model.name}</CardTitle>
                    <CardDescription>
                      {model.provider} • {model.size || 'Unknown size'}
                    </CardDescription>
                  </div>
                  {getStatusBadge(model.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {model.description && (
                    <p className="text-sm text-muted-foreground">{model.description}</p>
                  )}
                  
                  <div className="text-sm">
                    <span className="font-medium">Context Window:</span> {model.context_window} tokens
                  </div>

                  {model.status === 'downloading' && (
                    <Progress value={33} className="w-full" />
                  )}

                  {model.is_local && (
                    <div className="flex gap-2">
                      {model.status === 'running' ? (
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-full"
                          onClick={() => stopModel(model.id)}
                          disabled={stoppingModel === model.id}
                        >
                          {stoppingModel === model.id ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Stopping...
                            </>
                          ) : (
                            'Stop Model'
                          )}
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          className="w-full"
                          onClick={() => startModel(model.id)}
                          disabled={startingModel === model.id || model.status === 'starting'}
                        >
                          {startingModel === model.id || model.status === 'starting' ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Starting...
                            </>
                          ) : (
                            'Start Model'
                          )}
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}