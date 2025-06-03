import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import {
  Folder,
  FolderPlus,
  MessageSquare,
  Share2,
  Bookmark,
  Search,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Users,
  Link,
  Globe,
  Lock,
  Calendar,
  Tag,
  Move,
  Star,
  Archive,
  ChevronRight,
  ChevronDown,
  Plus,
  Settings
} from 'lucide-react';

interface Folder {
  id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  owner_id: string;
  parent_folder_id?: string;
  is_system: boolean;
  is_shared: boolean;
  created_at: string;
  updated_at?: string;
  conversation_count: number;
  sub_folder_count: number;
}

interface Conversation {
  id: string;
  title: string;
  model_id: string;
  model_name?: string;
  created_at: string;
  updated_at?: string;
  message_count: number;
  folders: Array<{id: string; name: string}>;
  is_bookmarked: boolean;
  is_shared: boolean;
}

interface ShareInfo {
  id: string;
  conversation_id: string;
  share_type: 'private' | 'link' | 'public' | 'team';
  share_token?: string;
  shared_by_id: string;
  shared_with_id?: string;
  permission_level: 'read' | 'write' | 'admin';
  expires_at?: string;
  is_active: boolean;
  access_count: number;
  created_at: string;
}

interface ConversationManagerProps {
  className?: string;
  onConversationSelect?: (conversationId: string) => void;
}

const SHARE_TYPES = [
  { value: 'private', label: 'Private', icon: Lock, description: 'Only you and invited users' },
  { value: 'link', label: 'Link Sharing', icon: Link, description: 'Anyone with the link' },
  { value: 'public', label: 'Public', icon: Globe, description: 'Visible to everyone' },
  { value: 'team', label: 'Team', icon: Users, description: 'Team members only' }
];

const PERMISSION_LEVELS = [
  { value: 'read', label: 'Read Only', description: 'Can view messages' },
  { value: 'write', label: 'Write', description: 'Can add messages' },
  { value: 'admin', label: 'Admin', description: 'Full control' }
];

export const ConversationManager: React.FC<ConversationManagerProps> = ({
  className,
  onConversationSelect
}) => {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [selectedConversations, setSelectedConversations] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [moveDialogOpen, setMoveDialogOpen] = useState(false);
  const [selectedConversationForShare, setSelectedConversationForShare] = useState<string | null>(null);
  
  // Form states
  const [newFolder, setNewFolder] = useState({
    name: '',
    description: '',
    color: '#3b82f6',
    icon: 'folder',
    parent_folder_id: null as string | null
  });
  
  const [shareForm, setShareForm] = useState({
    share_type: 'private' as 'private' | 'link' | 'public' | 'team',
    permission_level: 'read' as 'read' | 'write' | 'admin',
    shared_with_id: '',
    expires_at: ''
  });
  
  const [searchFilters, setSearchFilters] = useState({
    folder_id: null as string | null,
    shared_only: false,
    bookmarked_only: false,
    model_ids: [] as string[],
    date_from: '',
    date_to: '',
    sort_by: 'updated_at',
    sort_direction: 'desc'
  });
  
  const { toast } = useToast();
  
  // Load data on mount
  useEffect(() => {
    loadFolders();
    searchConversations();
  }, []);
  
  const loadFolders = async () => {
    try {
      const response = await fetch('/api/conversations/folders?include_conversations=true');
      if (response.ok) {
        const data = await response.json();
        setFolders(data);
      }
    } catch (error) {
      console.error('Failed to load folders:', error);
      setError('Failed to load folders');
    }
  };
  
  const searchConversations = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/conversations/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery || undefined,
          ...searchFilters,
          page: 1,
          page_size: 50
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error('Failed to search conversations:', error);
      setError('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };
  
  // Search when query or filters change
  useEffect(() => {
    const timer = setTimeout(() => {
      searchConversations();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, searchFilters]);
  
  const handleCreateFolder = async () => {
    try {
      const response = await fetch('/api/conversations/folders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFolder)
      });
      
      if (response.ok) {
        setCreateFolderOpen(false);
        setNewFolder({
          name: '',
          description: '',
          color: '#3b82f6',
          icon: 'folder',
          parent_folder_id: null
        });
        await loadFolders();
        toast({
          title: "Folder created",
          description: "Your new folder has been created successfully.",
        });
      }
    } catch (error) {
      toast({
        title: "Failed to create folder",
        description: "Please try again.",
        variant: "destructive",
      });
    }
  };
  
  const handleMoveConversations = async (targetFolderId: string | null) => {
    try {
      const response = await fetch('/api/conversations/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_ids: Array.from(selectedConversations),
          folder_id: targetFolderId
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMoveDialogOpen(false);
        setSelectedConversations(new Set());
        await searchConversations();
        toast({
          title: "Conversations moved",
          description: `${data.moved_count} conversation(s) moved to ${data.folder_name}`,
        });
      }
    } catch (error) {
      toast({
        title: "Failed to move conversations",
        description: "Please try again.",
        variant: "destructive",
      });
    }
  };
  
  const handleShare = async () => {
    if (!selectedConversationForShare) return;
    
    try {
      const response = await fetch('/api/conversations/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: selectedConversationForShare,
          ...shareForm,
          expires_at: shareForm.expires_at || undefined
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setShareDialogOpen(false);
        setSelectedConversationForShare(null);
        
        // Show share link for link sharing
        if (data.share_token) {
          const shareUrl = `${window.location.origin}/shared/${data.share_token}`;
          navigator.clipboard.writeText(shareUrl);
          toast({
            title: "Conversation shared",
            description: "Share link copied to clipboard",
          });
        } else {
          toast({
            title: "Conversation shared",
            description: "Sharing settings updated successfully",
          });
        }
      }
    } catch (error) {
      toast({
        title: "Failed to share conversation",
        description: "Please try again.",
        variant: "destructive",
      });
    }
  };
  
  const handleBookmark = async (conversationId: string, isBookmarked: boolean) => {
    try {
      if (isBookmarked) {
        await fetch(`/api/conversations/bookmark/${conversationId}`, {
          method: 'DELETE'
        });
        toast({
          title: "Bookmark removed",
          description: "Conversation removed from bookmarks",
        });
      } else {
        await fetch('/api/conversations/bookmark', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation_id: conversationId })
        });
        toast({
          title: "Conversation bookmarked",
          description: "Added to your bookmarks",
        });
      }
      
      await searchConversations();
    } catch (error) {
      toast({
        title: "Failed to update bookmark",
        description: "Please try again.",
        variant: "destructive",
      });
    }
  };
  
  const toggleConversationSelection = (conversationId: string) => {
    const newSelection = new Set(selectedConversations);
    if (newSelection.has(conversationId)) {
      newSelection.delete(conversationId);
    } else {
      newSelection.add(conversationId);
    }
    setSelectedConversations(newSelection);
  };
  
  const renderFolderTree = (parentId: string | null = null, level: number = 0) => {
    const childFolders = folders.filter(f => f.parent_folder_id === parentId);
    
    return childFolders.map(folder => (
      <div key={folder.id} className={`ml-${level * 4}`}>
        <div
          className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted ${
            selectedFolder === folder.id ? 'bg-muted' : ''
          }`}
          onClick={() => {
            setSelectedFolder(folder.id);
            setSearchFilters(prev => ({ ...prev, folder_id: folder.id }));
          }}
        >
          <ChevronRight className="h-4 w-4" />
          <Folder className="h-4 w-4" style={{ color: folder.color }} />
          <span className="text-sm">{folder.name}</span>
          <Badge variant="secondary" className="text-xs">
            {folder.conversation_count}
          </Badge>
        </div>
        {renderFolderTree(folder.id, level + 1)}
      </div>
    ));
  };
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Conversations</h2>
        <div className="flex items-center gap-2">
          <Dialog open={createFolderOpen} onOpenChange={setCreateFolderOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <FolderPlus className="h-4 w-4 mr-2" />
                New Folder
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Folder</DialogTitle>
                <DialogDescription>
                  Organize your conversations with folders
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Name</label>
                  <Input
                    value={newFolder.name}
                    onChange={(e) => setNewFolder(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Folder name"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Description</label>
                  <Textarea
                    value={newFolder.description}
                    onChange={(e) => setNewFolder(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Optional description"
                  />
                </div>
                <div className="flex gap-4">
                  <div>
                    <label className="text-sm font-medium">Color</label>
                    <Input
                      type="color"
                      value={newFolder.color}
                      onChange={(e) => setNewFolder(prev => ({ ...prev, color: e.target.value }))}
                      className="w-20 h-10"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-sm font-medium">Parent Folder</label>
                    <Select
                      value={newFolder.parent_folder_id || 'root'}
                      onValueChange={(value) => setNewFolder(prev => ({ 
                        ...prev, 
                        parent_folder_id: value === 'root' ? null : value 
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="root">Root</SelectItem>
                        {folders.map(folder => (
                          <SelectItem key={folder.id} value={folder.id}>
                            {folder.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateFolderOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateFolder} disabled={!newFolder.name.trim()}>
                  Create Folder
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          {selectedConversations.size > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMoveDialogOpen(true)}
            >
              <Move className="h-4 w-4 mr-2" />
              Move ({selectedConversations.size})
            </Button>
          )}
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="space-y-4">
          {/* Folders */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Folders</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <div
                className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted ${
                  selectedFolder === null ? 'bg-muted' : ''
                }`}
                onClick={() => {
                  setSelectedFolder(null);
                  setSearchFilters(prev => ({ ...prev, folder_id: null }));
                }}
              >
                <MessageSquare className="h-4 w-4" />
                <span className="text-sm">All Conversations</span>
              </div>
              {renderFolderTree()}
            </CardContent>
          </Card>
          
          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Filters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="bookmarked"
                  checked={searchFilters.bookmarked_only}
                  onCheckedChange={(checked) => 
                    setSearchFilters(prev => ({ ...prev, bookmarked_only: !!checked }))
                  }
                />
                <label htmlFor="bookmarked" className="text-sm">Bookmarked only</label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="shared"
                  checked={searchFilters.shared_only}
                  onCheckedChange={(checked) => 
                    setSearchFilters(prev => ({ ...prev, shared_only: !!checked }))
                  }
                />
                <label htmlFor="shared" className="text-sm">Shared only</label>
              </div>
              
              <div>
                <label className="text-sm font-medium">Sort by</label>
                <Select
                  value={searchFilters.sort_by}
                  onValueChange={(value) => setSearchFilters(prev => ({ ...prev, sort_by: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="updated_at">Last Updated</SelectItem>
                    <SelectItem value="created_at">Created</SelectItem>
                    <SelectItem value="title">Title</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Main Content */}
        <div className="lg:col-span-3 space-y-4">
          {/* Search */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          {/* Conversations List */}
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                      <Skeleton className="h-3 w-2/3" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : conversations.length > 0 ? (
            <div className="space-y-3">
              {conversations.map((conversation) => (
                <Card key={conversation.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <Checkbox
                          checked={selectedConversations.has(conversation.id)}
                          onCheckedChange={() => toggleConversationSelection(conversation.id)}
                        />
                        <div 
                          className="flex-1 cursor-pointer"
                          onClick={() => onConversationSelect?.(conversation.id)}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium">{conversation.title}</h3>
                            {conversation.is_bookmarked && (
                              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                            )}
                            {conversation.is_shared && (
                              <Share2 className="h-4 w-4 text-blue-500" />
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{conversation.model_name}</span>
                            <span>{conversation.message_count} messages</span>
                            <span>{new Date(conversation.updated_at || conversation.created_at).toLocaleDateString()}</span>
                          </div>
                          {conversation.folders.length > 0 && (
                            <div className="flex gap-1 mt-2">
                              {conversation.folders.map(folder => (
                                <Badge key={folder.id} variant="secondary" className="text-xs">
                                  {folder.name}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleBookmark(conversation.id, conversation.is_bookmarked)}
                        >
                          <Star className={`h-4 w-4 ${
                            conversation.is_bookmarked 
                              ? 'fill-yellow-400 text-yellow-400' 
                              : 'text-muted-foreground'
                          }`} />
                        </Button>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedConversationForShare(conversation.id);
                            setShareDialogOpen(true);
                          }}
                        >
                          <Share2 className="h-4 w-4" />
                        </Button>
                        
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No conversations found</h3>
                <p className="text-muted-foreground">
                  {searchQuery ? 'Try adjusting your search' : 'Start a new conversation to get started'}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      
      {/* Move Dialog */}
      <Dialog open={moveDialogOpen} onOpenChange={setMoveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Move Conversations</DialogTitle>
            <DialogDescription>
              Select a folder to move {selectedConversations.size} conversation(s)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            <div
              className="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted"
              onClick={() => handleMoveConversations(null)}
            >
              <MessageSquare className="h-4 w-4" />
              <span>Root (No folder)</span>
            </div>
            {folders.map(folder => (
              <div
                key={folder.id}
                className="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted"
                onClick={() => handleMoveConversations(folder.id)}
              >
                <Folder className="h-4 w-4" style={{ color: folder.color }} />
                <span>{folder.name}</span>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Share Conversation</DialogTitle>
            <DialogDescription>
              Choose how you want to share this conversation
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Share Type</label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {SHARE_TYPES.map(type => (
                  <div
                    key={type.value}
                    className={`p-3 border rounded cursor-pointer hover:bg-muted ${
                      shareForm.share_type === type.value ? 'border-primary' : ''
                    }`}
                    onClick={() => setShareForm(prev => ({ ...prev, share_type: type.value as any }))}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <type.icon className="h-4 w-4" />
                      <span className="text-sm font-medium">{type.label}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{type.description}</p>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium">Permission Level</label>
              <Select
                value={shareForm.permission_level}
                onValueChange={(value) => setShareForm(prev => ({ ...prev, permission_level: value as any }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PERMISSION_LEVELS.map(level => (
                    <SelectItem key={level.value} value={level.value}>
                      <div>
                        <div className="font-medium">{level.label}</div>
                        <div className="text-xs text-muted-foreground">{level.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium">Expires At (Optional)</label>
              <Input
                type="datetime-local"
                value={shareForm.expires_at}
                onChange={(e) => setShareForm(prev => ({ ...prev, expires_at: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShareDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleShare}>
              Share Conversation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};