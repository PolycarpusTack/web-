import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CodeStepConfig } from '@/types/pipeline';
import { Code, Play, AlertTriangle, CheckCircle, Clock, MemoryStick } from 'lucide-react';

interface CodeStepConfigProps {
  config: CodeStepConfig;
  onChange: (config: CodeStepConfig) => void;
}

export const CodeStepConfigComponent: React.FC<CodeStepConfigProps> = ({
  config,
  onChange
}) => {
  const [localConfig, setLocalConfig] = useState<CodeStepConfig>(config);
  const [codeVariables, setCodeVariables] = useState<string[]>([]);
  const [securityWarnings, setSecurityWarnings] = useState<string[]>([]);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  useEffect(() => {
    // Check for security issues and extract variables
    analyzeCode(localConfig.code || '');
  }, [localConfig.code]);

  const analyzeCode = (code: string) => {
    const warnings: string[] = [];
    const variables: string[] = [];

    // Security checks
    const securityPatterns = [
      { pattern: /__import__/, message: 'Direct imports detected' },
      { pattern: /eval\(/, message: 'eval() usage detected' },
      { pattern: /exec\(/, message: 'exec() usage detected' },
      { pattern: /open\(/, message: 'File operations detected' },
      { pattern: /subprocess/, message: 'Subprocess usage detected' },
      { pattern: /os\./, message: 'OS module usage detected' },
      { pattern: /sys\./, message: 'System module usage detected' },
    ];

    if (localConfig.language === 'javascript') {
      securityPatterns.push(
        { pattern: /require\(/, message: 'require() usage detected' },
        { pattern: /import\s+/, message: 'ES6 imports detected' },
        { pattern: /fs\./, message: 'File system access detected' },
        { pattern: /process\./, message: 'Process access detected' },
        { pattern: /child_process/, message: 'Child process usage detected' }
      );
    }

    securityPatterns.forEach(({ pattern, message }) => {
      if (pattern.test(code)) {
        warnings.push(message);
      }
    });

    // Extract variable usage (simplified)
    const variablePattern = /\b(\w+)\s*=/g;
    let match;
    while ((match = variablePattern.exec(code)) !== null) {
      const varName = match[1];
      if (varName !== 'result' && !variables.includes(varName)) {
        variables.push(varName);
      }
    }

    setSecurityWarnings(warnings);
    setCodeVariables(variables);
  };

  const handleConfigChange = (field: keyof CodeStepConfig, value: any) => {
    const newConfig = { ...localConfig, [field]: value };
    setLocalConfig(newConfig);
    onChange(newConfig);
  };

  const handlePackageChange = (packages: string) => {
    const packageList = packages.split(',').map(p => p.trim()).filter(p => p);
    handleConfigChange('packages', packageList);
  };

  const getLanguageIcon = (language: string) => {
    switch (language) {
      case 'python': return '🐍';
      case 'javascript': return '🟨';
      default: return '💻';
    }
  };

  const getSecurityLevel = () => {
    if (securityWarnings.length === 0) return 'safe';
    if (securityWarnings.length <= 2) return 'warning';
    return 'danger';
  };

  const securityLevelColors = {
    safe: 'text-green-600 bg-green-100',
    warning: 'text-yellow-600 bg-yellow-100',
    danger: 'text-red-600 bg-red-100'
  };

  const codeTemplates = {
    python: {
      basic: "# Access pipeline variables and set result\nresult = input_data",
      dataProcessing: "# Data processing example\nimport json\n\n# Process input data\nprocessed = []\nfor item in input_data:\n    processed.append(item.upper())\n\nresult = processed",
      mathOperations: "# Math operations example\nimport math\n\n# Calculate statistics\nif isinstance(input_data, list):\n    result = {\n        'sum': sum(input_data),\n        'average': sum(input_data) / len(input_data),\n        'max': max(input_data),\n        'min': min(input_data)\n    }\nelse:\n    result = input_data"
    },
    javascript: {
      basic: "// Access pipeline variables and set result\nresult = input_data;",
      dataProcessing: "// Data processing example\nif (Array.isArray(input_data)) {\n  result = input_data.map(item => item.toUpperCase());\n} else {\n  result = input_data;\n}",
      mathOperations: "// Math operations example\nif (Array.isArray(input_data)) {\n  const sum = input_data.reduce((a, b) => a + b, 0);\n  result = {\n    sum: sum,\n    average: sum / input_data.length,\n    max: Math.max(...input_data),\n    min: Math.min(...input_data)\n  };\n} else {\n  result = input_data;\n}"
    }
  };

  const insertTemplate = (template: string) => {
    handleConfigChange('code', template);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Code Execution Configuration
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {getLanguageIcon(localConfig.language)} {localConfig.language}
            </Badge>
            <Badge 
              variant="outline" 
              className={`text-xs ${securityLevelColors[getSecurityLevel()]}`}
            >
              {getSecurityLevel() === 'safe' && <CheckCircle className="h-3 w-3 mr-1" />}
              {getSecurityLevel() === 'warning' && <AlertTriangle className="h-3 w-3 mr-1" />}
              {getSecurityLevel() === 'danger' && <AlertTriangle className="h-3 w-3 mr-1" />}
              {getSecurityLevel()}
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="editor" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="editor">Code Editor</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
          </TabsList>

          <TabsContent value="editor" className="space-y-4">
            {/* Language Selection */}
            <div className="space-y-2">
              <Label htmlFor="language" className="text-sm font-medium">
                Programming Language
              </Label>
              <Select
                value={localConfig.language}
                onValueChange={(value) => handleConfigChange('language', value as 'python' | 'javascript')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="python">
                    <div className="flex items-center gap-2">
                      <span>🐍</span>
                      Python
                    </div>
                  </SelectItem>
                  <SelectItem value="javascript">
                    <div className="flex items-center gap-2">
                      <span>🟨</span>
                      JavaScript (Node.js)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Code Editor */}
            <div className="space-y-2">
              <Label htmlFor="code" className="text-sm font-medium">
                Code *
              </Label>
              <Textarea
                id="code"
                placeholder={`Enter your ${localConfig.language} code here...`}
                value={localConfig.code}
                onChange={(e) => handleConfigChange('code', e.target.value)}
                rows={12}
                className="font-mono text-sm"
              />
              <div className="text-xs text-gray-500">
                Use 'result' variable to set the output. All pipeline variables are available.
              </div>
            </div>

            {/* Variable Analysis */}
            {codeVariables.length > 0 && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Variables Created</Label>
                <div className="flex flex-wrap gap-1">
                  {codeVariables.map((variable) => (
                    <Badge key={variable} variant="outline" className="text-xs">
                      {variable}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Security Warnings */}
            {securityWarnings.length > 0 && (
              <Alert className="border-yellow-200 bg-yellow-50">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <div className="font-medium mb-2">Security Warnings:</div>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {securityWarnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            {/* Execution Settings */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="timeout" className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Timeout (seconds)
                </Label>
                <Input
                  id="timeout"
                  type="number"
                  min="1"
                  max="300"
                  value={localConfig.timeout || 30}
                  onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="memory-limit" className="text-sm font-medium flex items-center gap-2">
                  <MemoryStick className="h-4 w-4" />
                  Memory Limit (MB)
                </Label>
                <Input
                  id="memory-limit"
                  type="number"
                  min="1"
                  max="1024"
                  value={localConfig.memory_limit || 128}
                  onChange={(e) => handleConfigChange('memory_limit', parseInt(e.target.value))}
                />
              </div>
            </div>

            {/* Package Management (Python only) */}
            {localConfig.language === 'python' && (
              <div className="space-y-2">
                <Label htmlFor="packages" className="text-sm font-medium">
                  Allowed Packages
                </Label>
                <Input
                  id="packages"
                  placeholder="numpy, pandas, requests (comma-separated)"
                  value={localConfig.packages?.join(', ') || ''}
                  onChange={(e) => handlePackageChange(e.target.value)}
                />
                <div className="text-xs text-gray-500">
                  Allowed packages: numpy, pandas, requests, pillow, scipy
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="templates" className="space-y-4">
            <div className="space-y-3">
              <Label className="text-sm font-medium">Code Templates</Label>
              
              {Object.entries(codeTemplates[localConfig.language as keyof typeof codeTemplates]).map(([name, template]) => (
                <Card key={name} className="cursor-pointer hover:bg-gray-50" onClick={() => insertTemplate(template)}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium capitalize">{name.replace(/([A-Z])/g, ' $1')}</h4>
                        <p className="text-sm text-gray-500">
                          {name === 'basic' && 'Simple input/output processing'}
                          {name === 'dataProcessing' && 'Data transformation and manipulation'}
                          {name === 'mathOperations' && 'Mathematical calculations and statistics'}
                        </p>
                      </div>
                      <Button variant="outline" size="sm">
                        Use Template
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* Validation Errors */}
        {!localConfig.code && (
          <Alert>
            <AlertDescription>
              Please enter some code to execute.
            </AlertDescription>
          </Alert>
        )}

        {localConfig.timeout && localConfig.timeout > 60 && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Long timeout values may affect pipeline performance.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default CodeStepConfigComponent;