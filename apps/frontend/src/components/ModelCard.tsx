// src/components/ModelCard.tsx
import { useState } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoaderIcon, PlayIcon, Square } from "lucide-react";
import { api } from "@/api/ollama";
import { useToast } from "@/components/ui/use-toast";
import { formatFileSize } from "@/lib/shared-utils";

interface ModelCardProps {
  id: string;
  name: string;
  size?: string;
  status?: string;
  running: boolean;
  onStatusChange?: () => void;
  onOpenEnterprise?: (modelId: string) => void;
}

export const ModelCard = ({ 
  id, 
  name, 
  size, 
  status, 
  running,
  onStatusChange,
  onOpenEnterprise
}: ModelCardProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleStartModel = async () => {
    setIsLoading(true);
    try {
      const response = await api.models.start(id);
      
      if (response.success) {
        toast({
          title: "Model started",
          description: `${name} is now starting.`,
          variant: "default",
        });
        if (onStatusChange) onStatusChange();
      } else {
        throw new Error(response.message || "Failed to start model");
      }
    } catch (error) {
      toast({
        title: "Error starting model",
        description: `${name} could not be started.`,
        variant: "destructive",
      });
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopModel = async () => {
    setIsLoading(true);
    try {
      const response = await api.models.stop(id);
      
      if (response.success) {
        toast({
          title: "Model stopped",
          description: `${name} is now stopping.`,
          variant: "default",
        });
        if (onStatusChange) onStatusChange();
      } else {
        throw new Error(response.message || "Failed to stop model");
      }
    } catch (error) {
      toast({
        title: "Error stopping model",
        description: `${name} could not be stopped.`,
        variant: "destructive",
      });
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to render status badge with appropriate color
  const renderStatusBadge = () => {
    if (running) {
      return <Badge className="bg-green-500 hover:bg-green-600">Active</Badge>
    } else {
      return <Badge variant="secondary">Inactive</Badge>
    }
  };

  // Format size using the utility function
  const formatSize = (sizeInBytes?: string) => {
    if (!sizeInBytes) return "Unknown";
    return formatFileSize(sizeInBytes);
  };

  return (
    <Card className="w-full max-w-md transition-all duration-200 hover:shadow-md">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg font-bold">{name}</CardTitle>
          {renderStatusBadge()}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <p className="text-gray-500 dark:text-gray-400"><strong>ID:</strong> {id}</p>
          {status && <p className="text-gray-500 dark:text-gray-400"><strong>Status:</strong> {status}</p>}
          <p className="text-gray-500 dark:text-gray-400"><strong>Size:</strong> {formatSize(size)}</p>
        </div>
      </CardContent>
      <CardFooter className="pt-2 flex justify-between gap-2">
        <div>
          {onOpenEnterprise && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenEnterprise(id)}
            >
              Advanced
            </Button>
          )}
        </div>
        <div>
          {running ? (
            <Button 
              variant="destructive" 
              size="sm" 
              onClick={handleStopModel} 
              disabled={isLoading}
            >
              {isLoading ? <LoaderIcon className="mr-2 h-4 w-4 animate-spin" /> : <Square className="mr-2 h-4 w-4" />}
              Stop
            </Button>
          ) : (
            <Button 
              variant="default" 
              size="sm" 
              onClick={handleStartModel} 
              disabled={isLoading}
            >
              {isLoading ? <LoaderIcon className="mr-2 h-4 w-4 animate-spin" /> : <PlayIcon className="mr-2 h-4 w-4" />}
              Start
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};