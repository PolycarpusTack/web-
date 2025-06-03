import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from '@/components/ui/pagination';
import { AdvancedModelSearch, SearchFilter, FilterOptions } from '@/components/models/AdvancedModelSearch';
import { useToast } from '@/hooks/use-toast';
import { 
  Brain, 
  Zap, 
  DollarSign, 
  Clock, 
  Users, 
  TrendingUp,
  Star,
  Play,
  Pause,
  Settings,
  BarChart3,
  Download,
  Heart,
  BookOpen
} from 'lucide-react';

interface Model {
  id: string;
  name: string;
  provider: string;
  description?: string;
  version?: string;
  is_active: boolean;
  context_window?: number;
  max_output_tokens?: number;
  capabilities?: string[];
  pricing?: {
    input_cost_per_token?: number;
    output_cost_per_token?: number;
  };
  size?: string;
  tags: Array<{ id: number; name: string }>;
  created_at?: string;
  updated_at?: string;
}

interface SearchResponse {
  models: Model[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  search_metadata: {
    query_text?: string;
    filters_applied: Record<string, boolean>;
    sort_by: string;
    sort_direction: string;
    fuzzy_search: boolean;
    results_count: number;
    search_time: string;
  };
}

export const ModelsPageAdvanced: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [favoriteModels, setFavoriteModels] = useState<Set<string>>(new Set());
  const [currentFilters, setCurrentFilters] = useState<SearchFilter>({
    page: 1,
    page_size: 12,
    sort_by: 'name',
    sort_direction: 'asc'
  });
  
  const { toast } = useToast();
  
  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions();
    loadFavorites();
  }, []);
  
  const loadFilterOptions = async () => {
    try {
      const response = await fetch('/api/models/search/filters');
      if (response.ok) {
        const data = await response.json();
        setFilterOptions(data);
      }
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  };
  
  const loadFavorites = () => {
    const stored = localStorage.getItem('favorite_models');
    if (stored) {
      try {
        setFavoriteModels(new Set(JSON.parse(stored)));
      } catch (e) {
        console.warn('Failed to parse favorite models:', e);
      }
    }
  };
  
  const saveFavorites = (favorites: Set<string>) => {
    localStorage.setItem('favorite_models', JSON.stringify(Array.from(favorites)));
  };
  
  const handleSearch = useCallback(async (filters: SearchFilter) => {
    setLoading(true);
    setError(null);
    setCurrentFilters(filters);
    
    try {
      const response = await fetch('/api/models/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      });
      
      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }
      
      const data: SearchResponse = await response.json();
      setModels(data.models);
      setSearchResponse(data);
      
      // Show search results toast
      toast({
        title: "Search Complete",
        description: `Found ${data.total_count} model${data.total_count !== 1 ? 's' : ''}`,
      });
      
    } catch (error) {
      console.error('Search failed:', error);
      setError('Failed to search models. Please try again.');
      toast({
        title: "Search Failed",
        description: "Failed to search models. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);
  
  const toggleFavorite = (modelId: string) => {
    const newFavorites = new Set(favoriteModels);
    if (newFavorites.has(modelId)) {
      newFavorites.delete(modelId);
      toast({
        title: "Removed from favorites",
        description: "Model removed from your favorites",
      });
    } else {
      newFavorites.add(modelId);
      toast({
        title: "Added to favorites",
        description: "Model added to your favorites",
      });
    }
    setFavoriteModels(newFavorites);
    saveFavorites(newFavorites);
  };
  
  const handlePageChange = (page: number) => {
    handleSearch({ ...currentFilters, page });
  };
  
  const formatCost = (cost?: number) => {
    if (!cost) return 'N/A';
    return `$${(cost * 1000).toFixed(4)}/1K tokens`;
  };
  
  const formatContextWindow = (size?: number) => {
    if (!size) return 'N/A';
    if (size >= 1000000) return `${(size / 1000000).toFixed(1)}M`;
    if (size >= 1000) return `${(size / 1000).toFixed(0)}K`;
    return size.toString();
  };
  
  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      'openai': 'bg-green-100 text-green-800',
      'anthropic': 'bg-blue-100 text-blue-800',
      'ollama': 'bg-purple-100 text-purple-800',
      'google': 'bg-yellow-100 text-yellow-800',
      'microsoft': 'bg-cyan-100 text-cyan-800',
    };
    return colors[provider.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };
  
  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI Models</h1>
          <p className="text-muted-foreground">
            Discover and manage AI models with advanced search and filtering
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>
      
      {/* Search Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Model Search
          </CardTitle>
          <CardDescription>
            Search through {filterOptions?.providers.length || 0} providers and thousands of AI models
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AdvancedModelSearch
            onSearch={handleSearch}
            loading={loading}
            filterOptions={filterOptions || undefined}
            initialFilters={currentFilters}
            showFiltersCount={true}
          />
        </CardContent>
      </Card>
      
      {/* Search Results Summary */}
      {searchResponse && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing {searchResponse.models.length} of {searchResponse.total_count} models
            {searchResponse.search_metadata.query_text && (
              <span> for "{searchResponse.search_metadata.query_text}"</span>
            )}
          </div>
          <div className="text-xs text-muted-foreground">
            Search completed in {new Date(searchResponse.search_metadata.search_time).toLocaleTimeString()}
          </div>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full mb-4" />
                <div className="space-y-2">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      
      {/* Models Grid */}
      {!loading && models.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {models.map((model) => (
            <Card key={model.id} className="group hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base truncate">{model.name}</CardTitle>
                    <CardDescription className="text-sm">
                      <Badge
                        variant="secondary"
                        className={`${getProviderColor(model.provider)} text-xs`}
                      >
                        {model.provider}
                      </Badge>
                      {model.version && (
                        <span className="ml-2 text-xs">v{model.version}</span>
                      )}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleFavorite(model.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Heart
                        className={`h-4 w-4 ${
                          favoriteModels.has(model.id)
                            ? 'fill-red-500 text-red-500'
                            : 'text-muted-foreground'
                        }`}
                      />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-3">
                {/* Description */}
                {model.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {model.description}
                  </p>
                )}
                
                {/* Capabilities */}
                {model.capabilities && model.capabilities.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {model.capabilities.slice(0, 3).map((capability) => (
                      <Badge key={capability} variant="outline" className="text-xs">
                        {capability}
                      </Badge>
                    ))}
                    {model.capabilities.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{model.capabilities.length - 3}
                      </Badge>
                    )}
                  </div>
                )}
                
                {/* Stats */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="flex items-center gap-1">
                    <Brain className="h-3 w-3 text-muted-foreground" />
                    <span>{formatContextWindow(model.context_window)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-3 w-3 text-muted-foreground" />
                    <span>{formatCost(model.pricing?.input_cost_per_token)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Zap className="h-3 w-3 text-muted-foreground" />
                    <span>{model.max_output_tokens ? formatContextWindow(model.max_output_tokens) : 'N/A'}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className={`h-2 w-2 rounded-full ${model.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                    <span>{model.is_active ? 'Active' : 'Inactive'}</span>
                  </div>
                </div>
                
                {/* Tags */}
                {model.tags && model.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {model.tags.slice(0, 2).map((tag) => (
                      <Badge key={tag.id} variant="secondary" className="text-xs">
                        {tag.name}
                      </Badge>
                    ))}
                    {model.tags.length > 2 && (
                      <Badge variant="secondary" className="text-xs">
                        +{model.tags.length - 2}
                      </Badge>
                    )}
                  </div>
                )}
                
                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button size="sm" className="flex-1">
                    <Play className="h-3 w-3 mr-1" />
                    Use Model
                  </Button>
                  <Button variant="outline" size="sm">
                    <BookOpen className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      
      {/* No Results */}
      {!loading && models.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No models found</h3>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search criteria or clearing filters
            </p>
            <Button
              variant="outline"
              onClick={() => handleSearch({ page: 1, page_size: 12 })}
            >
              Clear all filters
            </Button>
          </CardContent>
        </Card>
      )}
      
      {/* Pagination */}
      {searchResponse && searchResponse.total_pages > 1 && (
        <div className="flex justify-center">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => searchResponse.page > 1 && handlePageChange(searchResponse.page - 1)}
                  className={searchResponse.page <= 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
              
              {/* Page numbers */}
              {Array.from({ length: Math.min(5, searchResponse.total_pages) }, (_, i) => {
                const pageNum = Math.max(1, searchResponse.page - 2) + i;
                if (pageNum > searchResponse.total_pages) return null;
                
                return (
                  <PaginationItem key={pageNum}>
                    <PaginationLink
                      onClick={() => handlePageChange(pageNum)}
                      isActive={pageNum === searchResponse.page}
                      className="cursor-pointer"
                    >
                      {pageNum}
                    </PaginationLink>
                  </PaginationItem>
                );
              })}
              
              <PaginationItem>
                <PaginationNext
                  onClick={() => searchResponse.page < searchResponse.total_pages && handlePageChange(searchResponse.page + 1)}
                  className={searchResponse.page >= searchResponse.total_pages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}
    </div>
  );
};