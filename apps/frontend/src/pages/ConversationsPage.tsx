// src/pages/ConversationsPage.tsx
import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { conversationsApi, Conversation, ConversationListResponse } from "@/api/conversations";
import HomePage from "./HomePage";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircleIcon, MessageSquareIcon, MessagesSquareIcon, Plus, RefreshCw, SearchIcon } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { formatTimeAgo } from "@/lib/shared-utils";
import { api } from "@/api/ollama";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function ConversationsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [filteredConversations, setFilteredConversations] = useState<Conversation[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [modelOptions, setModelOptions] = useState<{id: string, name: string}[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  
  // New conversation dialog state
  const [newConversationOpen, setNewConversationOpen] = useState(false);
  const [newConversation, setNewConversation] = useState({
    title: "",
    model_id: "",
    system_prompt: ""
  });
  const [creatingConversation, setCreatingConversation] = useState(false);

  // Load conversations
  const loadConversations = useCallback(async (showToast = false) => {
    try {
      setLoading(true);
      const response = await conversationsApi.getAll();
      
      if (response.success && response.data) {
        setConversations((response.data as any).conversations);
        setFilteredConversations((response.data as any).conversations);
        setError("");
        
        if (showToast) {
          toast({
            title: "Conversations updated",
            description: `${response.data.conversations.length} conversations loaded.`,
            variant: "default",
          });
        }
      } else {
        throw new Error(response.error);
      }
    } catch (err) {
      console.error(err);
      setError("Error fetching conversations");
      
      if (showToast) {
        toast({
          title: "Update failed",
          description: "Could not load conversations from server.",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Load models for the new conversation dialog
  const loadModels = useCallback(async () => {
    try {
      setLoadingModels(true);
      const response = await api.models.getAll();
      
      if (response && (response as any).models) {
        const models = (response as any).models || [];
        const options = models.map((model: any) => ({
          id: model.id,
          name: model.name
        }));
        setModelOptions(options);
      }
    } catch (err) {
      console.error("Error loading models:", err);
    } finally {
      setLoadingModels(false);
    }
  }, []);

  // Filter conversations based on search term
  useEffect(() => {
    if (!searchTerm) {
      setFilteredConversations(conversations);
      return;
    }
    
    const term = searchTerm.toLowerCase();
    const filtered = conversations.filter(conv => 
      conv.title.toLowerCase().includes(term) || 
      conv.model_id.toLowerCase().includes(term)
    );
    
    setFilteredConversations(filtered);
  }, [searchTerm, conversations]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Handle new conversation dialog open
  const handleNewConversationOpen = () => {
    setNewConversationOpen(true);
    loadModels();
  };

  // Handle input change for new conversation
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewConversation(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle model selection for new conversation
  const handleModelChange = (value: string) => {
    setNewConversation(prev => ({
      ...prev,
      model_id: value
    }));
  };

  // Create new conversation
  const handleCreateConversation = async () => {
    try {
      setCreatingConversation(true);
      
      if (!newConversation.title || !newConversation.model_id) {
        toast({
          title: "Missing information",
          description: "Please provide a title and select a model.",
          variant: "destructive",
        });
        return;
      }
      
      const response = await conversationsApi.create({
        title: newConversation.title,
        model_id: newConversation.model_id,
        system_prompt: newConversation.system_prompt || undefined
      });
      
      if (response.success) {
        toast({
          title: "Conversation created",
          description: "New conversation has been created successfully.",
          variant: "default",
        });
        
        // Reset form and close dialog
        setNewConversation({
          title: "",
          model_id: "",
          system_prompt: ""
        });
        setNewConversationOpen(false);
        
        // Reload conversations
        loadConversations();
      } else {
        throw new Error(response.error);
      }
    } catch (err) {
      console.error("Error creating conversation:", err);
      toast({
        title: "Creation failed",
        description: "Could not create new conversation.",
        variant: "destructive",
      });
    } finally {
      setCreatingConversation(false);
    }
  };

  // Open conversation in chat view
  const openConversation = (conversation: Conversation) => {
    // In a real app, this would navigate to the chat page with the conversation ID
    setSelectedConversation(conversation);
    if ((window as any).navigate) {
      (window as any).navigate(`/chat/${conversation.id}`);
    } else {
      toast({
        title: "Navigation not available",
        description: "Chat view is not yet implemented.",
        variant: "default",
      });
    }
  };

  // Render the conversation list
  const renderConversationList = () => {
    if (loading && conversations.length === 0) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="w-full">
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-2/3" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      );
    }

    if (filteredConversations.length === 0 && !loading) {
      return (
        <div className="text-center py-10">
          <MessagesSquareIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            {searchTerm ? "No conversations found matching your search." : "No conversations yet."}
          </p>
          <Button onClick={handleNewConversationOpen}>
            <Plus className="h-4 w-4 mr-2" />
            Start a new conversation
          </Button>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredConversations.map((conversation) => (
          <Card 
            key={conversation.id} 
            className="w-full cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => openConversation(conversation)}
          >
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg font-bold line-clamp-1">{conversation.title}</CardTitle>
                <Badge variant="outline">{conversation.message_count || 0} messages</Badge>
              </div>
            </CardHeader>
            <CardContent className="pb-2">
              <div className="space-y-1 text-sm">
                <p className="text-gray-500 dark:text-gray-400">
                  <strong>Model:</strong> {conversation.model_id.split(':')[0]}
                </p>
                <p className="text-gray-500 dark:text-gray-400">
                  <strong>Last updated:</strong> {formatTimeAgo(conversation.updated_at)}
                </p>
              </div>
            </CardContent>
            <CardFooter className="pt-0">
              <Button variant="ghost" size="sm" className="w-full justify-start">
                <MessageSquareIcon className="h-4 w-4 mr-2" />
                Continue conversation
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    );
  };

  // Error state
  if (error && conversations.length === 0) {
    return (
      <HomePage>
        <div className="p-6 flex flex-col items-center justify-center min-h-[300px]">
          <div className="text-center">
            <AlertCircleIcon className="h-10 w-10 text-red-500 mb-2 mx-auto" />
            <h2 className="text-xl font-bold mb-2">An error occurred</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-4">{error}</p>
            <Button onClick={() => loadConversations(true)}>Try again</Button>
          </div>
        </div>
      </HomePage>
    );
  }

  return (
    <HomePage>
      <div className="p-8 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <h1 className="text-3xl font-bold">Your Conversations</h1>
          
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => loadConversations(true)} 
              disabled={loading}
            >
              {loading ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Refresh
            </Button>
            
            <Button onClick={handleNewConversationOpen}>
              <Plus className="h-4 w-4 mr-2" />
              New Conversation
            </Button>
          </div>
        </div>
        
        <div className="w-full md:w-1/2 lg:w-1/3 relative">
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
           
            className="pl-9"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="mt-6">
          {renderConversationList()}
        </div>
      </div>
      
      {/* New Conversation Dialog */}
      <Dialog open={newConversationOpen} onOpenChange={setNewConversationOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create New Conversation</DialogTitle>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="title" className="text-right">
                Title
              </Label>
              <Input
                id="title"
                name="title"
                value={newConversation.title}
                onChange={handleInputChange}
                className="col-span-3"
               
              />
            </div>
            
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="model" className="text-right">
                Model
              </Label>
              <div className="col-span-3">
                <Select 
                  onValueChange={handleModelChange}
                  value={newConversation.model_id}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {loadingModels ? (
                      <div className="flex items-center justify-center p-2">
                        <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                        Loading models...
                      </div>
                    ) : (
                      modelOptions.map(model => (
                        <SelectItem key={model.id} value={model.id}>
                          {model.name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="system_prompt" className="text-right">
                System Prompt
              </Label>
              <Input
                id="system_prompt"
                name="system_prompt"
                value={newConversation.system_prompt}
                onChange={handleInputChange}
                className="col-span-3"
               
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewConversationOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateConversation} disabled={creatingConversation}>
              {creatingConversation ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </HomePage>
  );
}