// src/app/pages/ModelsPage.tsx
import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/ollama";
import { Model } from "@/types";
import { ModelCard } from "@/components/ModelCard";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { AlertCircleIcon, RefreshCw, SearchIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/lib/auth-context";

// WebSocket setup (if supported by your API)
const setupWebsocket = (onMessage: (data: unknown) => void) => {
  try {
    const socket = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/models/ws`);
    
    socket.onopen = () => {
      // WebSocket connection established
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };
    
    socket.onclose = () => {
      // WebSocket connection closed
    };
    
    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
    
    return socket;
  } catch (error) {
    console.error("Error setting up WebSocket:", error);
    return null;
  }
};

interface ModelsPageProps {
  onModelSelect?: (modelId: string) => void;
}

export default function ModelsPage({ onModelSelect }: ModelsPageProps = {}) {
  const [models, setModels] = useState<Model[]>([]);
  const [filteredModels, setFilteredModels] = useState<Model[]>([]);
  const [cacheHit, setCacheHit] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [showOnlyRunning, setShowOnlyRunning] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);
  const [useWebsocket] = useState(false);
  const { toast } = useToast();
  const { user: _user } = useAuth();

  // Load models function
  const loadModels = useCallback(async (showToast = false) => {
    try {
      setLoading(true);
      const response = await api.models.getAll();
      setModels(response.models);
      setCacheHit(response.cache_hit);
      setError("");
      if (showToast) {
        toast({
          title: "Models updated",
          description: `${response.models.length} models loaded.`,
          variant: "default",
        });
      }
    } catch (err) {
      console.error(err);
      setError("Error fetching models");
      if (showToast) {
        toast({
          title: "Update failed",
          description: "Could not load models from server.",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Filter models whenever the original list, search term, or filter changes
  useEffect(() => {
    let result = [...models];
    
    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(model => 
        model.name.toLowerCase().includes(term) || 
        model.id.toLowerCase().includes(term) ||
        (model.status?.toLowerCase().includes(term) || false)
      );
    }
    
    // Apply running filter
    if (showOnlyRunning) {
      result = result.filter(model => (model as any).running);
    }
    
    setFilteredModels(result);
  }, [models, searchTerm, showOnlyRunning]);

  // Initial load & auto-refresh setup
  useEffect(() => {
    loadModels();

    // Set up auto-refresh if enabled
    if (autoRefresh && !refreshInterval) {
      const interval = window.setInterval(() => {
        loadModels();
      }, 10000); // Refresh every 10 seconds
      setRefreshInterval(interval);
      return () => {
        if (interval) window.clearInterval(interval);
      };
    }
    
    // Clear interval if auto-refresh is disabled
    if (!autoRefresh && refreshInterval) {
      window.clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
    
    // Set up WebSocket if enabled
    let socket: WebSocket | null = null;
    if (useWebsocket) {
      socket = setupWebsocket((data) => {
        const typedData = data as { models?: Model[]; cache_hit?: boolean };
        if (typedData.models) {
          setModels(typedData.models);
          setCacheHit(typedData.cache_hit || false);
        }
      });
    }
    
    return () => {
      if (refreshInterval) window.clearInterval(refreshInterval);
      if (socket) socket.close();
    };
  }, [loadModels, autoRefresh, useWebsocket, refreshInterval]);

  // Models list render function
  const renderModelsList = () => {
    if (loading && models.length === 0) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="w-full max-w-md">
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      );
    }

    if (filteredModels.length === 0 && !loading) {
      return (
        <div className="text-center py-10">
          <p className="text-gray-500 dark:text-gray-400">
            {searchTerm || showOnlyRunning ? "No models found with these filters." : "No models available."}
          </p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredModels.map((model) => (
          <ModelCard
            key={model.id}
            id={model.id}
            name={model.name}
            size={model.size || undefined}
            status={model.status || undefined}
            running={(model as any).running || false}
            onStatusChange={loadModels}
            onOpenEnterprise={onModelSelect}
          />
        ))}
      </div>
    );
  };

  // Error state
  if (error && models.length === 0) {
    return (
      <div className="p-6 flex flex-col items-center justify-center min-h-[300px]">
        <div className="text-center">
          <AlertCircleIcon className="h-10 w-10 text-red-500 mb-2 mx-auto" />
          <h2 className="text-xl font-bold mb-2">An error occurred</h2>
          <p className="text-gray-500 dark:text-gray-400 mb-4">{error}</p>
          <Button onClick={() => loadModels(true)}>Try again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-3xl font-bold">Available Models</h1>
        <div className="flex items-center space-x-2">
          <Badge variant={cacheHit ? "default" : "secondary"} className="whitespace-nowrap">
            {cacheHit ? "Cached" : "Fresh"}
          </Badge>
          {loading && models.length > 0 && (
            <RefreshCw className="h-4 w-4 animate-spin" />
          )}
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        <div className="w-full md:w-1/2 lg:w-1/3 relative">
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
           
            className="pl-9"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="show-running"
              checked={showOnlyRunning}
              onCheckedChange={setShowOnlyRunning}
            />
            <Label htmlFor="show-running">Only active models</Label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
            <Label htmlFor="auto-refresh">Auto-refresh</Label>
          </div>
        </div>
        
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => loadModels(true)} 
          disabled={loading}
          className="ml-auto"
        >
          {loading ? (
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      <div className="mt-6">
        {renderModelsList()}
      </div>
    </div>
  );
}