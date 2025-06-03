import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Search, Filter, X, ChevronDown, Loader2, SlidersHorizontal } from 'lucide-react';
import { useDebounce } from '@/hooks/useDebounce';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';

export interface SearchFilter {
  query?: string;
  provider?: string[];
  capabilities?: string[];
  min_context_window?: number;
  max_context_window?: number;
  min_cost?: number;
  max_cost?: number;
  tags?: string[];
  is_active?: boolean;
  sort_by?: string;
  sort_direction?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
  fuzzy_search?: boolean;
  include_inactive?: boolean;
}

export interface SearchSuggestion {
  text: string;
  type: 'model' | 'provider' | 'tag' | 'capability';
  score: number;
}

export interface FilterOptions {
  providers: string[];
  tags: string[];
  context_window_range: { min: number; max: number };
  cost_range: { min: number; max: number };
  capabilities: string[];
}

interface AdvancedModelSearchProps {
  onSearch: (filters: SearchFilter) => void;
  onSuggestionSelect?: (suggestion: SearchSuggestion) => void;
  loading?: boolean;
  filterOptions?: FilterOptions;
  initialFilters?: SearchFilter;
  showFiltersCount?: boolean;
}

const SORT_OPTIONS = [
  { value: 'name', label: 'Name' },
  { value: 'created_at', label: 'Date Added' },
  { value: 'updated_at', label: 'Last Updated' },
  { value: 'provider', label: 'Provider' },
  { value: 'context_window', label: 'Context Window' },
  { value: 'popularity', label: 'Popularity' },
  { value: 'cost', label: 'Cost' },
];

export const AdvancedModelSearch: React.FC<AdvancedModelSearchProps> = ({
  onSearch,
  onSuggestionSelect,
  loading = false,
  filterOptions,
  initialFilters = {},
  showFiltersCount = true,
}) => {
  const [filters, setFilters] = useState<SearchFilter>(initialFilters);
  const [searchQuery, setSearchQuery] = useState(initialFilters.query || '');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  
  const { toast } = useToast();
  
  // Debounce search query
  const debouncedQuery = useDebounce(searchQuery, 300);
  
  // Debounce filter changes
  const debouncedFilters = useDebounce(filters, 500);
  
  // Load recent searches from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recent_model_searches');
    if (stored) {
      try {
        setRecentSearches(JSON.parse(stored));
      } catch (e) {
        console.warn('Failed to parse recent searches:', e);
      }
    }
  }, []);
  
  // Save recent searches
  const saveRecentSearch = useCallback((query: string) => {
    if (!query.trim()) return;
    
    const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recent_model_searches', JSON.stringify(updated));
  }, [recentSearches]);
  
  // Trigger search when debounced query or filters change
  useEffect(() => {
    const searchFilters = {
      ...debouncedFilters,
      query: debouncedQuery || undefined,
    };
    
    // Remove undefined values
    Object.keys(searchFilters).forEach(key => {
      if (searchFilters[key as keyof SearchFilter] === undefined) {
        delete searchFilters[key as keyof SearchFilter];
      }
    });
    
    onSearch(searchFilters);
    
    if (debouncedQuery) {
      saveRecentSearch(debouncedQuery);
    }
  }, [debouncedQuery, debouncedFilters, onSearch, saveRecentSearch]);
  
  // Fetch search suggestions
  const fetchSuggestions = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    
    setSuggestionsLoading(true);
    try {
      const response = await fetch(`/api/models/search/suggestions?q=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    } finally {
      setSuggestionsLoading(false);
    }
  }, []);
  
  // Fetch suggestions when query changes
  useEffect(() => {
    if (showSuggestions) {
      fetchSuggestions(searchQuery);
    }
  }, [searchQuery, showSuggestions, fetchSuggestions]);
  
  // Handle search input change
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setShowSuggestions(value.length > 0);
  };
  
  // Handle suggestion selection
  const handleSuggestionSelect = (suggestion: SearchSuggestion) => {
    setSearchQuery(suggestion.text);
    setShowSuggestions(false);
    onSuggestionSelect?.(suggestion);
  };
  
  // Handle filter change
  const updateFilter = <K extends keyof SearchFilter>(key: K, value: SearchFilter[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };
  
  // Clear all filters
  const clearFilters = () => {
    setFilters({});
    setSearchQuery('');
  };
  
  // Count active filters
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.provider?.length) count++;
    if (filters.capabilities?.length) count++;
    if (filters.tags?.length) count++;
    if (filters.min_context_window || filters.max_context_window) count++;
    if (filters.min_cost || filters.max_cost) count++;
    if (filters.is_active !== undefined) count++;
    if (filters.fuzzy_search) count++;
    if (filters.include_inactive) count++;
    return count;
  }, [filters]);
  
  // Get filter summary text
  const getFilterSummary = () => {
    const parts = [];
    if (filters.provider?.length) parts.push(`${filters.provider.length} provider${filters.provider.length > 1 ? 's' : ''}`);
    if (filters.tags?.length) parts.push(`${filters.tags.length} tag${filters.tags.length > 1 ? 's' : ''}`);
    if (filters.capabilities?.length) parts.push(`${filters.capabilities.length} capability${filters.capabilities.length > 1 ? 'ies' : 'y'}`);
    return parts.join(', ');
  };
  
  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Search models by name, description, or provider..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            onFocus={() => setShowSuggestions(searchQuery.length > 0)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            className="pl-10 pr-4"
          />
          {loading && (
            <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin" />
          )}
        </div>
        
        {/* Search Suggestions */}
        {showSuggestions && (suggestions.length > 0 || recentSearches.length > 0) && (
          <Card className="absolute top-full left-0 right-0 z-50 mt-1 max-h-80 overflow-auto">
            <CardContent className="p-2">
              {suggestions.length > 0 && (
                <div className="space-y-1">
                  <div className="text-sm font-medium text-muted-foreground px-2 py-1">
                    Suggestions
                  </div>
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionSelect(suggestion)}
                      className="w-full text-left px-2 py-1 hover:bg-accent rounded-sm flex items-center gap-2"
                    >
                      <Search className="h-3 w-3 text-muted-foreground" />
                      <span>{suggestion.text}</span>
                      <Badge variant="secondary" className="ml-auto text-xs">
                        {suggestion.type}
                      </Badge>
                    </button>
                  ))}
                </div>
              )}
              
              {searchQuery.length === 0 && recentSearches.length > 0 && (
                <div className="space-y-1">
                  <div className="text-sm font-medium text-muted-foreground px-2 py-1">
                    Recent Searches
                  </div>
                  {recentSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => handleSearchChange(search)}
                      className="w-full text-left px-2 py-1 hover:bg-accent rounded-sm flex items-center gap-2"
                    >
                      <Search className="h-3 w-3 text-muted-foreground" />
                      <span>{search}</span>
                    </button>
                  ))}
                </div>
              )}
              
              {suggestionsLoading && (
                <div className="px-2 py-4 text-center">
                  <Loader2 className="h-4 w-4 animate-spin mx-auto" />
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
      
      {/* Filter Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        <Popover open={filtersOpen} onOpenChange={setFiltersOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <SlidersHorizontal className="h-4 w-4" />
              Filters
              {showFiltersCount && activeFiltersCount > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-96 p-4" align="start">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Search Filters</h4>
                {activeFiltersCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearFilters}
                    className="h-auto p-1 text-xs"
                  >
                    Clear all
                  </Button>
                )}
              </div>
              
              {/* Provider Filter */}
              {filterOptions?.providers && (
                <Collapsible>
                  <CollapsibleTrigger className="flex items-center justify-between w-full text-sm font-medium">
                    Provider
                    <ChevronDown className="h-4 w-4" />
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pt-2 space-y-2">
                    {filterOptions.providers.map(provider => (
                      <label key={provider} className="flex items-center gap-2 text-sm">
                        <Checkbox
                          checked={filters.provider?.includes(provider) || false}
                          onCheckedChange={(checked) => {
                            const current = filters.provider || [];
                            const updated = checked
                              ? [...current, provider]
                              : current.filter(p => p !== provider);
                            updateFilter('provider', updated.length > 0 ? updated : undefined);
                          }}
                        />
                        {provider}
                      </label>
                    ))}
                  </CollapsibleContent>
                </Collapsible>
              )}
              
              <Separator />
              
              {/* Tags Filter */}
              {filterOptions?.tags && (
                <Collapsible>
                  <CollapsibleTrigger className="flex items-center justify-between w-full text-sm font-medium">
                    Tags
                    <ChevronDown className="h-4 w-4" />
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pt-2 space-y-2 max-h-32 overflow-auto">
                    {filterOptions.tags.map(tag => (
                      <label key={tag} className="flex items-center gap-2 text-sm">
                        <Checkbox
                          checked={filters.tags?.includes(tag) || false}
                          onCheckedChange={(checked) => {
                            const current = filters.tags || [];
                            const updated = checked
                              ? [...current, tag]
                              : current.filter(t => t !== tag);
                            updateFilter('tags', updated.length > 0 ? updated : undefined);
                          }}
                        />
                        {tag}
                      </label>
                    ))}
                  </CollapsibleContent>
                </Collapsible>
              )}
              
              <Separator />
              
              {/* Context Window Range */}
              {filterOptions?.context_window_range && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Context Window</label>
                  <div className="px-2">
                    <Slider
                      min={filterOptions.context_window_range.min}
                      max={filterOptions.context_window_range.max}
                      step={1024}
                      value={[
                        filters.min_context_window || filterOptions.context_window_range.min,
                        filters.max_context_window || filterOptions.context_window_range.max
                      ]}
                      onValueChange={([min, max]) => {
                        updateFilter('min_context_window', min !== filterOptions.context_window_range.min ? min : undefined);
                        updateFilter('max_context_window', max !== filterOptions.context_window_range.max ? max : undefined);
                      }}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>{filters.min_context_window || filterOptions.context_window_range.min}</span>
                      <span>{filters.max_context_window || filterOptions.context_window_range.max}</span>
                    </div>
                  </div>
                </div>
              )}
              
              <Separator />
              
              {/* Options */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Options</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={filters.fuzzy_search || false}
                      onCheckedChange={(checked) => updateFilter('fuzzy_search', checked === true ? true : undefined)}
                    />
                    Enable fuzzy search
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={filters.include_inactive || false}
                      onCheckedChange={(checked) => updateFilter('include_inactive', checked === true ? true : undefined)}
                    />
                    Include inactive models
                  </label>
                </div>
              </div>
            </div>
          </PopoverContent>
        </Popover>
        
        {/* Sort Controls */}
        <Select
          value={filters.sort_by || 'name'}
          onValueChange={(value) => updateFilter('sort_by', value)}
        >
          <SelectTrigger className="w-auto">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map(option => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => updateFilter('sort_direction', filters.sort_direction === 'asc' ? 'desc' : 'asc')}
        >
          {filters.sort_direction === 'desc' ? '↓' : '↑'}
        </Button>
        
        {/* Active Filters Summary */}
        {activeFiltersCount > 0 && (
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Filter className="h-3 w-3" />
            {getFilterSummary()}
          </div>
        )}
      </div>
      
      {/* Active Filter Tags */}
      {(filters.provider?.length || filters.tags?.length || filters.capabilities?.length) && (
        <div className="flex flex-wrap gap-1">
          {filters.provider?.map(provider => (
            <Badge key={`provider-${provider}`} variant="secondary" className="gap-1">
              Provider: {provider}
              <X
                className="h-3 w-3 cursor-pointer"
                onClick={() => {
                  const updated = filters.provider?.filter(p => p !== provider);
                  updateFilter('provider', updated?.length ? updated : undefined);
                }}
              />
            </Badge>
          ))}
          {filters.tags?.map(tag => (
            <Badge key={`tag-${tag}`} variant="secondary" className="gap-1">
              {tag}
              <X
                className="h-3 w-3 cursor-pointer"
                onClick={() => {
                  const updated = filters.tags?.filter(t => t !== tag);
                  updateFilter('tags', updated?.length ? updated : undefined);
                }}
              />
            </Badge>
          ))}
          {filters.capabilities?.map(capability => (
            <Badge key={`capability-${capability}`} variant="secondary" className="gap-1">
              {capability}
              <X
                className="h-3 w-3 cursor-pointer"
                onClick={() => {
                  const updated = filters.capabilities?.filter(c => c !== capability);
                  updateFilter('capabilities', updated?.length ? updated : undefined);
                }}
              />
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
};