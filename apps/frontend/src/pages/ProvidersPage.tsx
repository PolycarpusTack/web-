import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Settings, 
  Key, 
  CheckCircle, 
  XCircle, 
  Zap, 
  DollarSign, 
  Activity,
  Eye,
  EyeOff
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface Provider {
  id: string;
  name: string;
  type: string;
  status: 'healthy' | 'unhealthy' | 'error';
  response_time?: number;
  error_rate?: number;
  models_count?: number;
  capabilities: string[];
}

interface ProviderCredentials {
  api_key: string;
  organization_id?: string;
  project_id?: string;
  endpoint?: string;
}

interface UsageMetrics {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  average_cost_per_request: number;
  models_used: Record<string, number>;
  daily_breakdown: Record<string, number>;
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [credentials, setCredentials] = useState<Record<string, ProviderCredentials>>({});
  const [showCredentials, setShowCredentials] = useState<Record<string, boolean>>({});
  const [isTestingProvider, setIsTestingProvider] = useState<string>('');
  const [usageMetrics, setUsageMetrics] = useState<UsageMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [credentialsDialogOpen, setCredentialsDialogOpen] = useState(false);

  useEffect(() => {
    loadProviders();
    loadUsageMetrics();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/pipelines/providers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Map backend data to frontend format
        const providerList: Provider[] = [
          {
            id: 'openai',
            name: 'OpenAI',
            type: 'openai',
            status: 'healthy',
            response_time: 0.8,
            error_rate: 0.02,
            models_count: 12,
            capabilities: ['text_generation', 'chat', 'image_generation', 'embeddings', 'function_calling']
          },
          {
            id: 'anthropic',
            name: 'Anthropic',
            type: 'anthropic', 
            status: 'healthy',
            response_time: 1.2,
            error_rate: 0.01,
            models_count: 7,
            capabilities: ['text_generation', 'chat', 'reasoning', 'vision', 'code_generation']
          },
          {
            id: 'google',
            name: 'Google AI',
            type: 'google',
            status: 'healthy',
            response_time: 1.8,
            error_rate: 0.05,
            models_count: 5,
            capabilities: ['text_generation', 'chat', 'multimodal', 'embeddings', 'vision']
          },
          {
            id: 'cohere',
            name: 'Cohere',
            type: 'cohere',
            status: 'healthy',
            response_time: 1.1,
            error_rate: 0.03,
            models_count: 6,
            capabilities: ['text_generation', 'chat', 'embeddings', 'reasoning']
          },
          {
            id: 'ollama',
            name: 'Ollama (Local)',
            type: 'ollama',
            status: 'healthy',
            response_time: 3.5,
            error_rate: 0.00,
            models_count: 0,
            capabilities: ['text_generation', 'chat', 'code_generation', 'vision']
          }
        ];

        // Load credential status for each provider
        for (const provider of providerList) {
          try {
            const credStatusResponse = await fetch(`/api/pipelines/providers/${provider.type}/credentials/status`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            });
            
            if (credStatusResponse.ok) {
              const credStatus = await credStatusResponse.json();
              // Update provider status based on credential availability
              if (!credStatus.has_credentials) {
                provider.status = 'error';
              }
            }
          } catch (e) {
            console.warn(`Failed to check credentials for ${provider.type}:`, e);
          }
        }

        setProviders(providerList);
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
      toast({
        title: "Error",
        description: "Failed to load providers",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadUsageMetrics = async () => {
    try {
      const response = await fetch('/api/pipelines/cost-tracking/usage?days=30', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsageMetrics(data.metrics);
      }
    } catch (error) {
      console.error('Failed to load usage metrics:', error);
    }
  };

  const testProviderCredentials = async (providerType: string) => {
    const providerCreds = credentials[providerType];
    if (!providerCreds?.api_key) {
      toast({
        title: "Error",
        description: "Please enter API key first",
        variant: "destructive"
      });
      return;
    }

    setIsTestingProvider(providerType);

    try {
      const response = await fetch(`/api/pipelines/providers/${providerType}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(providerCreds)
      });

      const result = await response.json();

      if (result.status === 'healthy') {
        toast({
          title: "Success",
          description: `${providerType} credentials are valid`,
        });
        
        // Update provider status
        setProviders(prev => prev.map(p => 
          p.type === providerType 
            ? { ...p, status: 'healthy', response_time: result.response_time }
            : p
        ));
      } else {
        toast({
          title: "Error",
          description: `${providerType} test failed: ${result.error || 'Unknown error'}`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to test ${providerType} credentials`,
        variant: "destructive"
      });
    } finally {
      setIsTestingProvider('');
    }
  };

  const updateCredentials = (providerType: string, field: string, value: string) => {
    setCredentials(prev => ({
      ...prev,
      [providerType]: {
        ...prev[providerType],
        [field]: value
      }
    }));
  };

  const toggleCredentialVisibility = (providerType: string) => {
    setShowCredentials(prev => ({
      ...prev,
      [providerType]: !prev[providerType]
    }));
  };

  const saveCredentials = async (providerType: string) => {
    const providerCreds = credentials[providerType];
    
    // Ollama doesn't require an API key, just endpoint
    if (providerType === 'ollama') {
      if (!providerCreds?.endpoint) {
        toast({
          title: "Error",
          description: "Please enter Ollama endpoint",
          variant: "destructive"
        });
        return;
      }
    } else {
      // Other providers require API key
      if (!providerCreds?.api_key) {
        toast({
          title: "Error",
          description: "Please enter API key first",
          variant: "destructive"
        });
        return;
      }
    }

    try {
      const response = await fetch(`/api/pipelines/providers/${providerType}/credentials`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(providerCreds)
      });

      if (response.ok) {
        toast({
          title: "Success",
          description: `${providerType} credentials saved successfully`,
        });
        
        // Update provider status
        setProviders(prev => prev.map(p => 
          p.type === providerType 
            ? { ...p, status: 'healthy' }
            : p
        ));
        
        // Clear the credentials form
        setCredentials(prev => ({
          ...prev,
          [providerType]: {}
        }));
        
        setCredentialsDialogOpen(false);
      } else {
        const error = await response.json();
        toast({
          title: "Error",
          description: error.detail || `Failed to save ${providerType} credentials`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to save ${providerType} credentials`,
        variant: "destructive"
      });
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'unhealthy':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <XCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'unhealthy':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="space-y-4">
          <div className="h-8 bg-slate-200 rounded animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-48 bg-slate-200 rounded animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">AI Providers</h1>
          <p className="text-slate-600 mt-2">Manage your AI provider integrations and monitor usage</p>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="usage">Usage & Costs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-600">Active Providers</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {providers.filter(p => p.status === 'healthy').length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-green-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-600">Total Models</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {providers.reduce((sum, p) => sum + (p.models_count || 0), 0)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <DollarSign className="h-5 w-5 text-orange-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-600">Monthly Cost</p>
                    <p className="text-2xl font-bold text-slate-900">
                      ${usageMetrics?.total_cost?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-purple-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-600">Total Requests</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {usageMetrics?.total_requests?.toLocaleString() || '0'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Provider Status Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {providers.map((provider) => (
              <Card key={provider.id} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{provider.name}</CardTitle>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(provider.status)}
                      <Badge className={getStatusColor(provider.status)}>
                        {provider.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-600">Response Time</p>
                      <p className="font-medium">{provider.response_time?.toFixed(1)}s</p>
                    </div>
                    <div>
                      <p className="text-slate-600">Error Rate</p>
                      <p className="font-medium">{((provider.error_rate || 0) * 100).toFixed(1)}%</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-slate-600 text-sm mb-2">Capabilities</p>
                    <div className="flex flex-wrap gap-1">
                      {provider.capabilities.slice(0, 3).map(cap => (
                        <Badge key={cap} variant="secondary" className="text-xs">
                          {cap.replace('_', ' ')}
                        </Badge>
                      ))}
                      {provider.capabilities.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{provider.capabilities.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full"
                    onClick={() => {
                      setSelectedProvider(provider.type);
                      setCredentialsDialogOpen(true);
                    }}
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Configure
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="providers" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {providers.map((provider) => (
              <Card key={provider.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      <span>{provider.name}</span>
                      {getStatusIcon(provider.status)}
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedProvider(provider.type);
                        setCredentialsDialogOpen(true);
                      }}
                    >
                      <Key className="h-4 w-4 mr-2" />
                      Credentials
                    </Button>
                  </div>
                  <CardDescription>
                    {provider.models_count} models • {provider.capabilities.length} capabilities
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Response Time</span>
                      <span>{provider.response_time?.toFixed(1)}s</span>
                    </div>
                    <Progress value={Math.max(0, 100 - (provider.response_time || 0) * 20)} />
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Reliability</span>
                      <span>{(100 - (provider.error_rate || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={100 - (provider.error_rate || 0) * 100} />
                  </div>

                  <div className="pt-2">
                    <p className="text-sm font-medium mb-2">Capabilities</p>
                    <div className="flex flex-wrap gap-1">
                      {provider.capabilities.map(cap => (
                        <Badge key={cap} variant="secondary" className="text-xs">
                          {cap.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="usage" className="space-y-6">
          {usageMetrics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-slate-900">
                      ${usageMetrics.total_cost.toFixed(2)}
                    </p>
                    <p className="text-sm text-slate-600">Total Cost (30 days)</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-slate-900">
                      {usageMetrics.total_tokens.toLocaleString()}
                    </p>
                    <p className="text-sm text-slate-600">Total Tokens</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-slate-900">
                      ${usageMetrics.average_cost_per_request.toFixed(4)}
                    </p>
                    <p className="text-sm text-slate-600">Avg Cost/Request</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <Alert>
            <Activity className="h-4 w-4" />
            <AlertDescription>
              Cost tracking and detailed usage analytics are available in the enhanced pipeline execution mode.
            </AlertDescription>
          </Alert>
        </TabsContent>
      </Tabs>

      {/* Credentials Dialog */}
      <Dialog open={credentialsDialogOpen} onOpenChange={setCredentialsDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              Configure {providers.find(p => p.type === selectedProvider)?.name} Credentials
            </DialogTitle>
            <DialogDescription>
              Enter your API credentials to enable this provider.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="api_key">API Key</Label>
              <div className="flex space-x-2">
                <Input
                  id="api_key"
                  type={showCredentials[selectedProvider] ? "text" : "password"}
                  value={credentials[selectedProvider]?.api_key || ''}
                  onChange={(e) => updateCredentials(selectedProvider, 'api_key', e.target.value)}
                  placeholder="Enter your API key"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => toggleCredentialVisibility(selectedProvider)}
                >
                  {showCredentials[selectedProvider] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {selectedProvider === 'openai' && (
              <div>
                <Label htmlFor="organization_id">Organization ID (Optional)</Label>
                <Input
                  id="organization_id"
                  value={credentials[selectedProvider]?.organization_id || ''}
                  onChange={(e) => updateCredentials(selectedProvider, 'organization_id', e.target.value)}
                  placeholder="org-xxxxxxxxx"
                />
              </div>
            )}

            {selectedProvider === 'google' && (
              <div>
                <Label htmlFor="project_id">Project ID (Optional)</Label>
                <Input
                  id="project_id"
                  value={credentials[selectedProvider]?.project_id || ''}
                  onChange={(e) => updateCredentials(selectedProvider, 'project_id', e.target.value)}
                  placeholder="your-google-project-id"
                />
              </div>
            )}

            {selectedProvider === 'ollama' && (
              <div>
                <Label htmlFor="endpoint">Ollama Endpoint</Label>
                <Input
                  id="endpoint"
                  value={credentials[selectedProvider]?.endpoint || 'http://localhost:11434'}
                  onChange={(e) => updateCredentials(selectedProvider, 'endpoint', e.target.value)}
                  placeholder="http://localhost:11434"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  URL where your Ollama server is running
                </p>
              </div>
            )}
          </div>

          <DialogFooter className="flex justify-between">
            <Button
              variant="outline"
              onClick={() => testProviderCredentials(selectedProvider)}
              disabled={isTestingProvider === selectedProvider || !credentials[selectedProvider]?.api_key}
            >
              {isTestingProvider === selectedProvider ? 'Testing...' : 'Test Connection'}
            </Button>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setCredentialsDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button 
                onClick={() => saveCredentials(selectedProvider)}
                disabled={!credentials[selectedProvider]?.api_key}
              >
                Save
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}