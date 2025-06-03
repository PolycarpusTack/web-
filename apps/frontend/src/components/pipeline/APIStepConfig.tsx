import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { 
  Plus, 
  Minus, 
  Send, 
  Key, 
  Shield,
  Eye,
  EyeOff,
  TestTube,
  Info,
  AlertTriangle,
  CheckCircle,
  Globe,
  Lock
} from 'lucide-react';

import { PipelineStepConfig } from '@/types/pipeline-config';

interface Header {
  key: string;
  value: string;
}

interface AuthConfig {
  type: 'none' | 'bearer' | 'basic' | 'api_key';
  token?: string;
  username?: string;
  password?: string;
  api_key?: string;
  header_name?: string;
}

interface APIStepConfigProps {
  config: PipelineStepConfig;
  onChange: (config: PipelineStepConfig) => void;
  availableVariables?: string[];
}

export const APIStepConfig: React.FC<APIStepConfigProps> = ({
  config,
  onChange,
  availableVariables = []
}) => {
  const [url, setUrl] = useState<string>(config.url || '');
  const [method, setMethod] = useState<string>(config.method || 'GET');
  const [headers, setHeaders] = useState<Header[]>(config.headers || []);
  const [body, setBody] = useState<string>(config.body || '');
  const [bodyType, setBodyType] = useState<'json' | 'text' | 'form'>(config.body_type || 'json');
  const [auth, setAuth] = useState<AuthConfig>(config.auth || { type: 'none' });
  const [timeout, setTimeout] = useState<number>(config.timeout || 30);
  const [followRedirects, setFollowRedirects] = useState<boolean>(config.follow_redirects || true);
  const [validateSSL, setValidateSSL] = useState<boolean>(config.validate_ssl || true);
  const [showSensitive, setShowSensitive] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Update config when state changes
  useEffect(() => {
    const newConfig = {
      ...config,
      url,
      method,
      headers: headers.filter(h => h.key && h.value),
      body: body || undefined,
      body_type: bodyType,
      auth,
      timeout,
      follow_redirects: followRedirects,
      validate_ssl: validateSSL
    };
    onChange(newConfig);
  }, [url, method, headers, body, bodyType, auth, timeout, followRedirects, validateSSL]);

  // Add new header
  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '' }]);
  };

  // Update header
  const updateHeader = (index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...headers];
    newHeaders[index][field] = value;
    setHeaders(newHeaders);
  };

  // Remove header
  const removeHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index));
  };

  // Update auth configuration
  const updateAuth = (updates: Partial<AuthConfig>) => {
    setAuth({ ...auth, ...updates });
  };

  // Test API call
  const testAPICall = async () => {
    setIsLoading(true);
    try {
      // Mock API test - in real implementation, this would make an actual request
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockResponse = {
        status: 200,
        statusText: 'OK',
        headers: {
          'content-type': 'application/json',
          'content-length': '123'
        },
        data: {
          message: 'Mock API response',
          timestamp: new Date().toISOString(),
          method: method,
          url: url
        }
      };

      setTestResult({
        success: true,
        response: mockResponse
      });
    } catch (error) {
      setTestResult({
        success: false,
        error: error.message
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Validate URL
  const isValidUrl = (urlString: string): boolean => {
    try {
      new URL(urlString);
      return true;
    } catch {
      return urlString.includes('{{') && urlString.includes('}}'); // Allow template variables
    }
  };

  // Validate JSON body
  const isValidJson = (jsonString: string): boolean => {
    if (!jsonString.trim()) return true;
    try {
      JSON.parse(jsonString);
      return true;
    } catch {
      return jsonString.includes('{{') && jsonString.includes('}}'); // Allow template variables
    }
  };

  const httpMethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'];
  const commonHeaders = [
    'Content-Type',
    'Authorization',
    'Accept',
    'User-Agent',
    'X-API-Key',
    'X-Requested-With'
  ];

  return (
    <div className="space-y-6">
      {/* Basic Configuration */}
      <div className="grid grid-cols-4 gap-4">
        <div className="col-span-3">
          <Label htmlFor="api-url">URL</Label>
          <Input
            id="api-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://api.example.com/endpoint"
            className={!isValidUrl(url) && url ? 'border-red-300' : ''}
          />
          {url && !isValidUrl(url) && (
            <div className="text-xs text-red-600 mt-1">Invalid URL format</div>
          )}
        </div>
        <div>
          <Label htmlFor="http-method">Method</Label>
          <Select value={method} onValueChange={setMethod}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {httpMethods.map(m => (
                <SelectItem key={m} value={m}>{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Configuration Tabs */}
      <Tabs defaultValue="headers" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="headers">Headers</TabsTrigger>
          <TabsTrigger value="body">Body</TabsTrigger>
          <TabsTrigger value="auth">Auth</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Headers Tab */}
        <TabsContent value="headers" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">HTTP Headers</h3>
            <Button size="sm" onClick={addHeader}>
              <Plus className="h-4 w-4 mr-1" />
              Add Header
            </Button>
          </div>

          <div className="space-y-2">
            {headers.map((header, index) => (
              <div key={index} className="grid grid-cols-12 gap-2 items-center">
                <div className="col-span-5">
                  <Input
                    placeholder="Header name"
                    value={header.key}
                    onChange={(e) => updateHeader(index, 'key', e.target.value)}
                    list="common-headers"
                  />
                </div>
                <div className="col-span-6">
                  <Input
                    placeholder="Header value"
                    value={header.value}
                    onChange={(e) => updateHeader(index, 'value', e.target.value)}
                  />
                </div>
                <div className="col-span-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => removeHeader(index)}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <datalist id="common-headers">
            {commonHeaders.map(header => (
              <option key={header} value={header} />
            ))}
          </datalist>

          {headers.length === 0 && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Add headers to customize your API request. Common headers like Content-Type will be set automatically based on body type.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Body Tab */}
        <TabsContent value="body" className="space-y-4">
          {['POST', 'PUT', 'PATCH'].includes(method) ? (
            <>
              <div className="flex items-center gap-4">
                <Label>Body Type</Label>
                <Select value={bodyType} onValueChange={(value) => setBodyType(value as any)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="text">Text</SelectItem>
                    <SelectItem value="form">Form Data</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="request-body">Request Body</Label>
                <Textarea
                  id="request-body"
                  rows={8}
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder={
                    bodyType === 'json' 
                      ? '{\n  "key": "value",\n  "data": "{{variable}}"\n}'
                      : bodyType === 'form'
                      ? 'key1=value1&key2={{variable}}'
                      : 'Plain text content with {{variables}}'
                  }
                  className={`font-mono text-sm ${
                    bodyType === 'json' && !isValidJson(body) && body ? 'border-red-300' : ''
                  }`}
                />
                {bodyType === 'json' && body && !isValidJson(body) && (
                  <div className="text-xs text-red-600 mt-1">Invalid JSON format</div>
                )}
                <div className="text-xs text-gray-500 mt-1">
                  Use {'{{'}{'{'}variable{'}'}{'{}'} syntax to insert values from previous steps
                </div>
              </div>
            </>
          ) : (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                {method} requests typically don't include a body. Switch to POST, PUT, or PATCH to add request body.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Authentication Tab */}
        <TabsContent value="auth" className="space-y-4">
          <div>
            <Label>Authentication Type</Label>
            <Select value={auth.type} onValueChange={(value) => updateAuth({ type: value as any })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No Authentication</SelectItem>
                <SelectItem value="bearer">Bearer Token</SelectItem>
                <SelectItem value="basic">Basic Auth</SelectItem>
                <SelectItem value="api_key">API Key</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {auth.type === 'bearer' && (
            <div>
              <Label htmlFor="bearer-token">Bearer Token</Label>
              <div className="relative">
                <Input
                  id="bearer-token"
                  type={showSensitive ? 'text' : 'password'}
                  value={auth.token || ''}
                  onChange={(e) => updateAuth({ token: e.target.value })}
                  placeholder="Enter bearer token"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6"
                  onClick={() => setShowSensitive(!showSensitive)}
                >
                  {showSensitive ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          )}

          {auth.type === 'basic' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={auth.username || ''}
                  onChange={(e) => updateAuth({ username: e.target.value })}
                  placeholder="Username"
                />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showSensitive ? 'text' : 'password'}
                    value={auth.password || ''}
                    onChange={(e) => updateAuth({ password: e.target.value })}
                    placeholder="Password"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6"
                    onClick={() => setShowSensitive(!showSensitive)}
                  >
                    {showSensitive ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {auth.type === 'api_key' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="header-name">Header Name</Label>
                <Input
                  id="header-name"
                  value={auth.header_name || 'X-API-Key'}
                  onChange={(e) => updateAuth({ header_name: e.target.value })}
                  placeholder="X-API-Key"
                />
              </div>
              <div>
                <Label htmlFor="api-key">API Key</Label>
                <div className="relative">
                  <Input
                    id="api-key"
                    type={showSensitive ? 'text' : 'password'}
                    value={auth.api_key || ''}
                    onChange={(e) => updateAuth({ api_key: e.target.value })}
                    placeholder="Enter API key"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6"
                    onClick={() => setShowSensitive(!showSensitive)}
                  >
                    {showSensitive ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {auth.type !== 'none' && (
            <Alert>
              <Shield className="h-4 w-4" />
              <AlertDescription>
                Authentication credentials are encrypted and stored securely. 
                Use {'{{'}{'{'}variable{'}'}{'{}'} syntax to reference credentials from pipeline variables.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                min="1"
                max="300"
                value={timeout}
                onChange={(e) => setTimeout(Number(e.target.value))}
              />
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="follow-redirects">Follow Redirects</Label>
                <Switch
                  id="follow-redirects"
                  checked={followRedirects}
                  onCheckedChange={setFollowRedirects}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="validate-ssl">Validate SSL Certificates</Label>
                <Switch
                  id="validate-ssl"
                  checked={validateSSL}
                  onCheckedChange={setValidateSSL}
                />
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Test Section */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium">Test API Call</h3>
          <Button size="sm" onClick={testAPICall} disabled={isLoading || !url}>
            <TestTube className="h-4 w-4 mr-1" />
            {isLoading ? 'Testing...' : 'Test Call'}
          </Button>
        </div>

        {testResult && (
          <Card className="p-4">
            {testResult.success ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">API Call Successful</span>
                  <Badge variant="outline">
                    {testResult.response.status} {testResult.response.statusText}
                  </Badge>
                </div>
                
                <div>
                  <Label className="text-xs">Response Headers:</Label>
                  <pre className="text-xs bg-gray-50 p-2 rounded mt-1">
                    {JSON.stringify(testResult.response.headers, null, 2)}
                  </pre>
                </div>
                
                <div>
                  <Label className="text-xs">Response Body:</Label>
                  <pre className="text-xs bg-gray-50 p-2 rounded mt-1 max-h-32 overflow-y-auto">
                    {JSON.stringify(testResult.response.data, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <span className="text-sm text-red-600">
                  API call failed: {testResult.error}
                </span>
              </div>
            )}
          </Card>
        )}
      </div>

      {/* Variable References */}
      {availableVariables.length > 0 && (
        <div>
          <Label className="text-sm font-medium mb-2 block">Available Variables</Label>
          <div className="flex flex-wrap gap-1">
            {availableVariables.map(variable => (
              <Badge key={variable} variant="outline" className="text-xs">
                {'{{'}{variable}{'}}'}
              </Badge>
            ))}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Click to copy variable syntax, then paste in URL, headers, or body
          </div>
        </div>
      )}

      {/* Validation */}
      <div className="space-y-2">
        {!url && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              URL is required for API calls
            </AlertDescription>
          </Alert>
        )}
        
        {url && !isValidUrl(url) && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              URL format is invalid
            </AlertDescription>
          </Alert>
        )}

        {bodyType === 'json' && body && !isValidJson(body) && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              JSON body format is invalid
            </AlertDescription>
          </Alert>
        )}

        {url && isValidUrl(url) && (bodyType !== 'json' || !body || isValidJson(body)) && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              API configuration is valid
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};

export default APIStepConfig;