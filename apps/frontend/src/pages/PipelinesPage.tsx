import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Copy, PencilIcon, PlayIcon, Plus, SearchIcon, Hash as Tag, Trash2 } from "lucide-react";
import { format } from 'date-fns';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/components/ui/use-toast';

import { getPipelines, createPipeline, deletePipeline } from '@/api/pipelines';
import { PIPELINE_TEMPLATES } from '@/lib/pipeline-templates';

// Types
interface Pipeline {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  is_active: boolean;
  is_public: boolean;
  version: string;
  tags: string[];
}

interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  icon: React.ReactNode;
}

// Template Category component
const TemplateCategory = ({ category, templates, onSelect }: { 
  category: string; 
  templates: PipelineTemplate[];
  onSelect: (template: PipelineTemplate) => void;
}) => (
  <div className="space-y-3">
    <h3 className="text-lg font-semibold text-slate-200">{category}</h3>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {templates.map(template => (
        <Card 
          key={template.id} 
          className="bg-slate-800 border-slate-700 hover:border-cyan-600 cursor-pointer transition-all"
          onClick={() => onSelect(template)}
        >
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <CardTitle className="text-slate-100">{template.name}</CardTitle>
                <CardDescription className="text-slate-400">{template.description}</CardDescription>
              </div>
              <div className="bg-slate-700 p-2 rounded-md">
                {template.icon}
              </div>
            </div>
          </CardHeader>
          <CardFooter className="pt-2 flex gap-2">
            {template.tags.map(tag => (
              <Badge key={tag} variant="secondary" className="bg-slate-700 hover:bg-slate-600">
                {tag}
              </Badge>
            ))}
          </CardFooter>
        </Card>
      ))}
    </div>
  </div>
);

// Status badge component
const StatusBadge = ({ status }: { status: string }) => {
  let color = "bg-slate-600";
  if (status === "completed") color = "bg-emerald-600";
  if (status === "running") color = "bg-blue-600";
  if (status === "failed") color = "bg-red-600";
  
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${color}`} />
      <span className="text-xs text-slate-300 capitalize">{status}</span>
    </div>
  );
};

const PipelinesPage = () => {
  const navigate = useNavigate();
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [filteredPipelines, setFilteredPipelines] = useState<Pipeline[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterTag, setFilterTag] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<PipelineTemplate | null>(null);

  // Fetch pipelines on component mount
  useEffect(() => {
    const fetchPipelines = async () => {
      try {
        setLoading(true);
        const data = await getPipelines();
        setPipelines(data);
        setFilteredPipelines(data);
      } catch (error) {
        console.error('Failed to fetch pipelines:', error);
        toast({
          title: "Failed to load pipelines",
          description: "There was an error loading your pipelines. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchPipelines();
  }, []);

  // Filter pipelines when search term or filter tag changes
  useEffect(() => {
    let filtered = pipelines;
    
    if (searchTerm) {
      filtered = filtered.filter(pipeline => 
        pipeline.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        pipeline.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    if (filterTag) {
      filtered = filtered.filter(pipeline => 
        pipeline.tags?.includes(filterTag)
      );
    }
    
    setFilteredPipelines(filtered);
  }, [searchTerm, filterTag, pipelines]);

  // Get all unique tags from pipelines
  const allTags = React.useMemo(() => {
    const tags = new Set<string>();
    pipelines.forEach(pipeline => {
      if (pipeline.tags) {
        pipeline.tags.forEach(tag => tags.add(tag));
      }
    });
    return Array.from(tags);
  }, [pipelines]);

  // Handler for creating a new pipeline
  const handleCreatePipeline = async (template?: PipelineTemplate) => {
    try {
      setLoading(true);
      const newPipeline = await createPipeline({
        name: template ? template.name : "New Pipeline",
        description: template ? template.description : "A new pipeline",
        is_public: false,
        tags: template ? template.tags : [],
      });
      
      // Navigate to the pipeline builder
      navigate(`/pipelines/${newPipeline.id}/edit`);
      
      toast({
        title: "Pipeline created",
        description: "Your new pipeline has been created successfully.",
      });
    } catch (error) {
      console.error('Failed to create pipeline:', error);
      toast({
        title: "Failed to create pipeline",
        description: "There was an error creating your pipeline. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
      setCreateDialogOpen(false);
    }
  };

  // Handler for deleting a pipeline
  const handleDeletePipeline = async (id: string) => {
    try {
      await deletePipeline(id);
      setPipelines(pipelines.filter(p => p.id !== id));
      toast({
        title: "Pipeline deleted",
        description: "The pipeline has been deleted successfully.",
      });
    } catch (error) {
      console.error('Failed to delete pipeline:', error);
      toast({
        title: "Failed to delete pipeline",
        description: "There was an error deleting the pipeline. Please try again.",
        variant: "destructive"
      });
    }
  };

  // Template selection handler
  const handleTemplateSelect = (template: PipelineTemplate) => {
    setSelectedTemplate(template);
    handleCreatePipeline(template);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-screen-2xl">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Code Factory</h1>
          <p className="text-slate-400 mt-1">Create, manage, and execute code generation pipelines</p>
        </div>
        <Button 
          onClick={() => setCreateDialogOpen(true)} 
          className="bg-cyan-600 hover:bg-cyan-700 text-white"
        >
          <Plus className="mr-2 h-4 w-4" />
          New Pipeline
        </Button>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-grow">
          <SearchIcon className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-10 bg-slate-800 border-slate-700 text-slate-100"
           
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select onValueChange={value => setFilterTag(value === "all" ? null : value)}>
          <SelectTrigger className="w-full md:w-[180px] bg-slate-800 border-slate-700 text-slate-100">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700 text-slate-100">
            <SelectItem value="all">All Tags</SelectItem>
            {allTags.map(tag => (
              <SelectItem key={tag} value={tag}>{tag}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Pipelines Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <Skeleton className="h-6 w-3/4 bg-slate-700 mb-2" />
              <Skeleton className="h-4 w-full bg-slate-700 mb-4" />
              <Skeleton className="h-4 w-1/2 bg-slate-700 mb-2" />
              <Skeleton className="h-4 w-3/4 bg-slate-700 mb-2" />
              <div className="flex gap-2 mt-6">
                <Skeleton className="h-8 w-8 rounded-full bg-slate-700" />
                <Skeleton className="h-8 w-8 rounded-full bg-slate-700" />
                <Skeleton className="h-8 w-8 rounded-full bg-slate-700" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredPipelines.length === 0 ? (
        <div className="text-center py-12 bg-slate-800 rounded-lg border border-slate-700">
          {searchTerm || filterTag ? (
            <>
              <p className="text-slate-300 text-lg mb-2">No matching pipelines found</p>
              <p className="text-slate-400">Try adjusting your search or filters</p>
            </>
          ) : (
            <>
              <p className="text-slate-300 text-lg mb-2">No pipelines yet</p>
              <p className="text-slate-400 mb-6">Create your first pipeline to get started</p>
              <Button 
                onClick={() => setCreateDialogOpen(true)}
                className="bg-cyan-600 hover:bg-cyan-700 text-white"
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Pipeline
              </Button>
            </>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPipelines.map(pipeline => (
            <Card key={pipeline.id} className="bg-slate-800 border-slate-700 overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex justify-between">
                  <CardTitle className="text-slate-100">{pipeline.name}</CardTitle>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400">
                        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M3.625 7.5C3.625 8.12132 3.12132 8.625 2.5 8.625C1.87868 8.625 1.375 8.12132 1.375 7.5C1.375 6.87868 1.87868 6.375 2.5 6.375C3.12132 6.375 3.625 6.87868 3.625 7.5ZM8.625 7.5C8.625 8.12132 8.12132 8.625 7.5 8.625C6.87868 8.625 6.375 8.12132 6.375 7.5C6.375 6.87868 6.87868 6.375 7.5 6.375C8.12132 6.375 8.625 6.87868 8.625 7.5ZM13.625 7.5C13.625 8.12132 13.1213 8.625 12.5 8.625C11.8787 8.625 11.375 8.12132 11.375 7.5C11.375 6.87868 11.8787 6.375 12.5 6.375C13.1213 6.375 13.625 6.87868 13.625 7.5Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
                        </svg>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="bg-slate-800 border-slate-700 text-slate-100">
                      <DropdownMenuItem 
                        className="hover:bg-slate-700 cursor-pointer"
                        onClick={() => navigate(`/pipelines/${pipeline.id}/run`)}
                      >
                        <PlayIcon className="h-4 w-4 mr-2 text-emerald-500" />
                        Run Pipeline
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="hover:bg-slate-700 cursor-pointer"
                        onClick={() => navigate(`/pipelines/${pipeline.id}/edit`)}
                      >
                        <PencilIcon className="h-4 w-4 mr-2 text-blue-500" />
                        Edit Pipeline
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="hover:bg-slate-700 cursor-pointer"
                        onClick={() => {
                          // Duplicate pipeline logic
                          toast({
                            title: "Duplicating pipeline",
                            description: "This feature is coming soon.",
                          });
                        }}
                      >
                        <Copy className="h-4 w-4 mr-2 text-orange-500" />
                        Duplicate
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className="bg-slate-700" />
                      <DropdownMenuItem 
                        className="hover:bg-slate-700 cursor-pointer text-red-500"
                        onClick={() => handleDeletePipeline(pipeline.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <CardDescription className="text-slate-400 line-clamp-2 min-h-[40px]">
                  {pipeline.description || "No description provided"}
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-3">
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                  <div className="flex items-center gap-1">
                    <Tag className="h-3.5 w-3.5" />
                    <span>{pipeline.tags?.length || 0} tags</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <StatusBadge status="completed" />
                  </div>
                  <div className="flex items-center gap-1">
                    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3.5 2C3.22386 2 3 2.22386 3 2.5V12.5C3 12.7761 3.22386 13 3.5 13H11.5C11.7761 13 12 12.7761 12 12.5V6H8.5C8.22386 6 8 5.77614 8 5.5V2H3.5ZM9 2.70711L11.2929 5H9V2.70711ZM2 2.5C2 1.67157 2.67157 1 3.5 1H8.5C8.63261 1 8.75979 1.05268 8.85355 1.14645L12.8536 5.14645C12.9473 5.24021 13 5.36739 13 5.5V12.5C13 13.3284 12.3284 14 11.5 14H3.5C2.67157 14 2 13.3284 2 12.5V2.5Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
                    </svg>
                    <span>5 steps</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    <span>{format(new Date(pipeline.updated_at), 'MMM d')}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-3 flex flex-wrap gap-2">
                {pipeline.tags?.slice(0, 3).map(tag => (
                  <Badge key={tag} variant="secondary" className="bg-slate-700 hover:bg-slate-600 cursor-pointer">
                    {tag}
                  </Badge>
                ))}
                {pipeline.tags?.length > 3 && (
                  <Badge variant="outline" className="border-slate-600 text-slate-400">
                    +{pipeline.tags.length - 3} more
                  </Badge>
                )}
              </CardFooter>
              <div 
                className="absolute inset-0 bg-gradient-to-r from-cyan-600/0 to-cyan-600/0 hover:from-cyan-600/10 hover:to-cyan-600/0 cursor-pointer transition-all"
                onClick={() => navigate(`/pipelines/${pipeline.id}`)}
              />
            </Card>
          ))}
        </div>
      )}

      {/* Create Pipeline Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-slate-100 sm:max-w-[900px]">
          <DialogHeader>
            <DialogTitle className="text-2xl">Create New Pipeline</DialogTitle>
            <DialogDescription className="text-slate-400">
              Start from scratch or use a template to create your pipeline.
            </DialogDescription>
          </DialogHeader>
          
          <Tabs defaultValue="templates" className="mt-4">
            <TabsList className="bg-slate-800 text-slate-400">
              <TabsTrigger value="templates" className="data-[state=active]:bg-slate-700 data-[state=active]:text-white">
                Templates
              </TabsTrigger>
              <TabsTrigger value="blank" className="data-[state=active]:bg-slate-700 data-[state=active]:text-white">
                Blank Pipeline
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="templates" className="mt-4 max-h-[50vh] overflow-y-auto pr-2">
              <div className="space-y-6">
                <TemplateCategory 
                  category="Code Generation" 
                  templates={PIPELINE_TEMPLATES.filter(t => t.category === 'code-generation')}
                  onSelect={handleTemplateSelect}
                />
                <TemplateCategory 
                  category="Code Transformation" 
                  templates={PIPELINE_TEMPLATES.filter(t => t.category === 'code-transformation')}
                  onSelect={handleTemplateSelect}
                />
                <TemplateCategory 
                  category="Documentation" 
                  templates={PIPELINE_TEMPLATES.filter(t => t.category === 'documentation')}
                  onSelect={handleTemplateSelect}
                />
              </div>
            </TabsContent>
            
            <TabsContent value="blank" className="mt-4">
              <div className="text-center py-10">
                <h3 className="text-xl text-slate-200 mb-2">Start with a Blank Pipeline</h3>
                <p className="text-slate-400 mb-6">Build your pipeline from scratch with custom steps</p>
                <Button 
                  onClick={() => handleCreatePipeline()} 
                  className="bg-cyan-600 hover:bg-cyan-700 text-white"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Create Blank Pipeline
                </Button>
              </div>
            </TabsContent>
          </Tabs>
          
          <DialogFooter className="mt-4">
            <Button 
              variant="outline" 
              onClick={() => setCreateDialogOpen(false)}
              className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
            >
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PipelinesPage;