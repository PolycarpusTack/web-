import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LLMStepConfig } from '@/types/pipeline';

interface LLMStepConfigProps {
  config: LLMStepConfig;
  onChange: (config: LLMStepConfig) => void;
  availableModels: Array<{
    id: string;
    name: string;
    provider: string;
    capabilities?: string[];
    context_window?: number;
    max_output_tokens?: number;
  }>;
}

export const LLMStepConfigComponent: React.FC<LLMStepConfigProps> = ({
  config,
  onChange,
  availableModels = []
}) => {
  const [localConfig, setLocalConfig] = useState<LLMStepConfig>(config);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [promptVariables, setPromptVariables] = useState<string[]>([]);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  useEffect(() => {
    // Extract variables from prompt template
    const variables = extractVariables(localConfig.prompt || '');
    setPromptVariables(variables);
  }, [localConfig.prompt]);

  const extractVariables = (template: string): string[] => {
    const regex = /\{\{(\w+)\}\}/g;
    const variables: string[] = [];
    let match;
    while ((match = regex.exec(template)) !== null) {
      if (!variables.includes(match[1])) {
        variables.push(match[1]);
      }
    }
    return variables;
  };

  const handleConfigChange = (field: keyof LLMStepConfig, value: any) => {
    const newConfig = { ...localConfig, [field]: value };
    setLocalConfig(newConfig);
    onChange(newConfig);
  };

  const selectedModel = availableModels.find(m => m.id === localConfig.model_id);

  const getModelStatusColor = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'ollama': return 'bg-green-100 text-green-800';
      case 'openai': return 'bg-blue-100 text-blue-800';
      case 'anthropic': return 'bg-purple-100 text-purple-800';
      case 'mistral': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          LLM Configuration
          <Badge variant="outline" className="text-xs">
            {selectedModel?.provider || 'No Model'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Model Selection */}
        <div className="space-y-2">
          <Label htmlFor="model-select" className="text-sm font-medium">
            Model *
          </Label>
          <Select
            value={localConfig.model_id}
            onValueChange={(value) => handleConfigChange('model_id', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a model" />
            </SelectTrigger>
            <SelectContent>
              {availableModels.map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <div className="flex items-center justify-between w-full">
                    <span>{model.name}</span>
                    <Badge 
                      variant="secondary" 
                      className={`ml-2 text-xs ${getModelStatusColor(model.provider)}`}
                    >
                      {model.provider}
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedModel && (
            <div className="text-xs text-gray-500 mt-1">
              Context: {selectedModel.context_window?.toLocaleString() || 'Unknown'} tokens
              {selectedModel.max_output_tokens && (
                <>, Max output: {selectedModel.max_output_tokens.toLocaleString()}</>
              )}
            </div>
          )}
        </div>

        {/* System Prompt */}
        <div className="space-y-2">
          <Label htmlFor="system-prompt" className="text-sm font-medium">
            System Prompt
          </Label>
          <Textarea
            id="system-prompt"
            placeholder="You are a helpful assistant..."
            value={localConfig.system_prompt || ''}
            onChange={(e) => handleConfigChange('system_prompt', e.target.value)}
            rows={3}
          />
        </div>

        {/* Main Prompt */}
        <div className="space-y-2">
          <Label htmlFor="prompt" className="text-sm font-medium">
            Prompt Template *
          </Label>
          <Textarea
            id="prompt"
            placeholder="Enter your prompt template here. Use {{variableName}} for dynamic values."
            value={localConfig.prompt}
            onChange={(e) => handleConfigChange('prompt', e.target.value)}
            rows={6}
            className="font-mono"
          />
          {promptVariables.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              <span className="text-xs text-gray-500">Variables:</span>
              {promptVariables.map((variable) => (
                <Badge key={variable} variant="outline" className="text-xs">
                  {`{{${variable}}}`}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Response Format */}
        <div className="space-y-2">
          <Label htmlFor="response-format" className="text-sm font-medium">
            Response Format
          </Label>
          <Select
            value={localConfig.response_format || 'text'}
            onValueChange={(value) => handleConfigChange('response_format', value as 'text' | 'json')}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="text">Text</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Basic Parameters */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="max-tokens" className="text-sm font-medium">
              Max Tokens
            </Label>
            <Input
              id="max-tokens"
              type="number"
              min="1"
              max="100000"
              value={localConfig.max_tokens}
              onChange={(e) => handleConfigChange('max_tokens', parseInt(e.target.value))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="temperature" className="text-sm font-medium">
              Temperature: {localConfig.temperature}
            </Label>
            <Slider
              id="temperature"
              min={0}
              max={2}
              step={0.1}
              value={[localConfig.temperature]}
              onValueChange={(value) => handleConfigChange('temperature', value[0])}
              className="w-full"
            />
          </div>
        </div>

        {/* Advanced Settings Toggle */}
        <div className="flex items-center space-x-2">
          <Switch
            id="show-advanced"
            checked={showAdvanced}
            onCheckedChange={setShowAdvanced}
          />
          <Label htmlFor="show-advanced" className="text-sm">
            Show Advanced Settings
          </Label>
        </div>

        {showAdvanced && (
          <>
            <Separator />
            
            {/* Advanced Parameters */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-700">Advanced Parameters</h4>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="top-p" className="text-sm font-medium">
                    Top-p: {localConfig.top_p}
                  </Label>
                  <Slider
                    id="top-p"
                    min={0}
                    max={1}
                    step={0.05}
                    value={[localConfig.top_p || 1.0]}
                    onValueChange={(value) => handleConfigChange('top_p', value[0])}
                    className="w-full"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="frequency-penalty" className="text-sm font-medium">
                    Frequency Penalty: {localConfig.frequency_penalty || 0}
                  </Label>
                  <Slider
                    id="frequency-penalty"
                    min={-2}
                    max={2}
                    step={0.1}
                    value={[localConfig.frequency_penalty || 0]}
                    onValueChange={(value) => handleConfigChange('frequency_penalty', value[0])}
                    className="w-full"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="presence-penalty" className="text-sm font-medium">
                    Presence Penalty: {localConfig.presence_penalty || 0}
                  </Label>
                  <Slider
                    id="presence-penalty"
                    min={-2}
                    max={2}
                    step={0.1}
                    value={[localConfig.presence_penalty || 0]}
                    onValueChange={(value) => handleConfigChange('presence_penalty', value[0])}
                    className="w-full"
                  />
                </div>
                
                <div className="space-y-2 flex items-center">
                  <Switch
                    id="stream"
                    checked={localConfig.stream || false}
                    onCheckedChange={(checked) => handleConfigChange('stream', checked)}
                  />
                  <Label htmlFor="stream" className="text-sm ml-2">
                    Enable Streaming
                  </Label>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Validation Warnings */}
        {!localConfig.model_id && (
          <Alert>
            <AlertDescription>
              Please select a model to continue.
            </AlertDescription>
          </Alert>
        )}

        {!localConfig.prompt && (
          <Alert>
            <AlertDescription>
              Please enter a prompt template.
            </AlertDescription>
          </Alert>
        )}

        {selectedModel && localConfig.max_tokens > (selectedModel.max_output_tokens || Infinity) && (
          <Alert>
            <AlertDescription>
              Max tokens exceeds model limit of {selectedModel.max_output_tokens?.toLocaleString()}.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default LLMStepConfigComponent;