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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Plus, 
  Minus, 
  ArrowRight, 
  Settings, 
  Code, 
  Filter, 
  Shuffle,
  Eye,
  Copy,
  Trash2,
  Info,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

import { PipelineStepConfig } from '@/types/pipeline-config';

interface TransformMapping {
  id: string;
  sourceField: string;
  targetField: string;
  transformation?: string;
  type: 'direct' | 'function' | 'expression';
  description?: string;
}

interface FilterCondition {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'startswith' | 'endswith' | 'regex';
  value: string;
  type: 'string' | 'number' | 'boolean';
}

interface DataTransformConfigProps {
  config: PipelineStepConfig;
  onChange: (config: PipelineStepConfig) => void;
  availableVariables?: string[];
}

export const DataTransformConfig: React.FC<DataTransformConfigProps> = ({
  config,
  onChange,
  availableVariables = []
}) => {
  const [transformType, setTransformType] = useState<string>(config.type || 'extract');
  const [mappings, setMappings] = useState<TransformMapping[]>(config.mappings || []);
  const [filterConditions, setFilterConditions] = useState<FilterCondition[]>(config.filter_conditions || []);
  const [sourcePath, setSourcePath] = useState<string>(config.source_path || '');
  const [targetKey, setTargetKey] = useState<string>(config.target_key || 'result');
  const [customExpression, setCustomExpression] = useState<string>(config.custom_expression || '');
  const [previewData, setPreviewData] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Sample data for preview
  const sampleData = {
    users: [
      { id: 1, name: 'John Doe', email: 'john@example.com', age: 30, active: true },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com', age: 25, active: false },
      { id: 3, name: 'Bob Johnson', email: 'bob@example.com', age: 35, active: true }
    ],
    metadata: { total: 3, page: 1 },
    timestamp: '2024-01-01T00:00:00Z'
  };

  // Update config when state changes
  useEffect(() => {
    const newConfig = {
      ...config,
      type: transformType,
      mappings,
      filter_conditions: filterConditions,
      source_path: sourcePath,
      target_key: targetKey,
      custom_expression: customExpression
    };
    onChange(newConfig);
  }, [transformType, mappings, filterConditions, sourcePath, targetKey, customExpression]);

  // Add new mapping
  const addMapping = () => {
    const newMapping: TransformMapping = {
      id: `mapping_${Date.now()}`,
      sourceField: '',
      targetField: '',
      type: 'direct'
    };
    setMappings([...mappings, newMapping]);
  };

  // Update mapping
  const updateMapping = (id: string, updates: Partial<TransformMapping>) => {
    setMappings(mappings.map(m => m.id === id ? { ...m, ...updates } : m));
  };

  // Remove mapping
  const removeMapping = (id: string) => {
    setMappings(mappings.filter(m => m.id !== id));
  };

  // Add filter condition
  const addFilterCondition = () => {
    const newCondition: FilterCondition = {
      field: '',
      operator: 'eq',
      value: '',
      type: 'string'
    };
    setFilterConditions([...filterConditions, newCondition]);
  };

  // Update filter condition
  const updateFilterCondition = (index: number, updates: Partial<FilterCondition>) => {
    const newConditions = [...filterConditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    setFilterConditions(newConditions);
  };

  // Remove filter condition
  const removeFilterCondition = (index: number) => {
    setFilterConditions(filterConditions.filter((_, i) => i !== index));
  };

  // Generate preview
  const generatePreview = () => {
    try {
      let result = sampleData;
      
      // Apply source path
      if (sourcePath) {
        const path = sourcePath.split('.');
        for (const key of path) {
          if (result && typeof result === 'object' && key in result) {
            result = result[key];
          } else {
            result = null;
            break;
          }
        }
      }

      // Apply transformations based on type
      switch (transformType) {
        case 'extract':
          if (mappings.length > 0) {
            if (Array.isArray(result)) {
              result = result.map(item => {
                const extracted = {};
                mappings.forEach(mapping => {
                  if (mapping.sourceField && mapping.targetField) {
                    extracted[mapping.targetField] = item[mapping.sourceField];
                  }
                });
                return extracted;
              });
            } else if (result && typeof result === 'object') {
              const extracted = {};
              mappings.forEach(mapping => {
                if (mapping.sourceField && mapping.targetField) {
                  extracted[mapping.targetField] = result[mapping.sourceField];
                }
              });
              result = extracted;
            }
          }
          break;

        case 'filter':
          if (Array.isArray(result) && filterConditions.length > 0) {
            result = result.filter(item => {
              return filterConditions.every(condition => {
                const fieldValue = item[condition.field];
                const conditionValue = condition.type === 'number' ? Number(condition.value) : 
                                     condition.type === 'boolean' ? condition.value === 'true' : 
                                     condition.value;

                switch (condition.operator) {
                  case 'eq': return fieldValue === conditionValue;
                  case 'ne': return fieldValue !== conditionValue;
                  case 'gt': return fieldValue > conditionValue;
                  case 'lt': return fieldValue < conditionValue;
                  case 'gte': return fieldValue >= conditionValue;
                  case 'lte': return fieldValue <= conditionValue;
                  case 'contains': return String(fieldValue).includes(String(conditionValue));
                  case 'startswith': return String(fieldValue).startsWith(String(conditionValue));
                  case 'endswith': return String(fieldValue).endsWith(String(conditionValue));
                  case 'regex': 
                    try {
                      return new RegExp(String(conditionValue)).test(String(fieldValue));
                    } catch {
                      return false;
                    }
                  default: return true;
                }
              });
            });
          }
          break;

        case 'format':
          if (customExpression && result) {
            // Simple template formatting
            let formatted = customExpression;
            if (typeof result === 'object') {
              Object.keys(result).forEach(key => {
                formatted = formatted.replace(new RegExp(`{{${key}}}`, 'g'), String(result[key]));
              });
            }
            result = formatted;
          }
          break;

        case 'aggregate':
          if (Array.isArray(result)) {
            result = {
              count: result.length,
              items: result
            };
          }
          break;
      }

      setPreviewData(result);
    } catch (error) {
      setPreviewData({ error: 'Preview generation failed', details: error.message });
    }
  };

  const getFieldSuggestions = () => {
    // Extract field names from sample data for autocomplete
    const extractFields = (obj: any, prefix = ''): string[] => {
      if (!obj || typeof obj !== 'object') return [];
      
      const fields: string[] = [];
      Object.keys(obj).forEach(key => {
        const fullKey = prefix ? `${prefix}.${key}` : key;
        fields.push(fullKey);
        
        if (typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
          fields.push(...extractFields(obj[key], fullKey));
        }
      });
      return fields;
    };

    return extractFields(sampleData);
  };

  return (
    <div className="space-y-6">
      {/* Transform Type Selection */}
      <div>
        <Label className="text-sm font-medium mb-2 block">Transformation Type</Label>
        <Select value={transformType} onValueChange={setTransformType}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="extract">Extract Fields</SelectItem>
            <SelectItem value="filter">Filter Data</SelectItem>
            <SelectItem value="format">Format Output</SelectItem>
            <SelectItem value="aggregate">Aggregate Data</SelectItem>
            <SelectItem value="custom">Custom Expression</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Common Settings */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="source-path">Source Path</Label>
          <Input
            id="source-path"
            value={sourcePath}
            onChange={(e) => setSourcePath(e.target.value)}
            placeholder="e.g., data.items"
          />
          <div className="text-xs text-gray-500 mt-1">
            Use dot notation to access nested data
          </div>
        </div>
        <div>
          <Label htmlFor="target-key">Target Key</Label>
          <Input
            id="target-key"
            value={targetKey}
            onChange={(e) => setTargetKey(e.target.value)}
            placeholder="result"
          />
        </div>
      </div>

      {/* Type-specific Configuration */}
      <Tabs value={transformType} className="w-full">
        <TabsContent value="extract" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Field Mappings</h3>
            <Button size="sm" onClick={addMapping}>
              <Plus className="h-4 w-4 mr-1" />
              Add Mapping
            </Button>
          </div>
          
          <div className="space-y-3">
            {mappings.map((mapping) => (
              <Card key={mapping.id} className="p-4">
                <div className="grid grid-cols-12 gap-2 items-center">
                  <div className="col-span-4">
                    <Input
                      placeholder="Source field"
                      value={mapping.sourceField}
                      onChange={(e) => updateMapping(mapping.id, { sourceField: e.target.value })}
                      list="field-suggestions"
                    />
                  </div>
                  <div className="col-span-1 text-center">
                    <ArrowRight className="h-4 w-4 text-gray-400" />
                  </div>
                  <div className="col-span-4">
                    <Input
                      placeholder="Target field"
                      value={mapping.targetField}
                      onChange={(e) => updateMapping(mapping.id, { targetField: e.target.value })}
                    />
                  </div>
                  <div className="col-span-2">
                    <Select 
                      value={mapping.type} 
                      onValueChange={(value) => updateMapping(mapping.id, { type: value as any })}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="direct">Direct</SelectItem>
                        <SelectItem value="function">Function</SelectItem>
                        <SelectItem value="expression">Expression</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeMapping(mapping.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                {mapping.type !== 'direct' && (
                  <div className="mt-2">
                    <Input
                      placeholder={mapping.type === 'function' ? 'Function name' : 'Expression'}
                      value={mapping.transformation || ''}
                      onChange={(e) => updateMapping(mapping.id, { transformation: e.target.value })}
                      className="text-xs"
                    />
                  </div>
                )}
              </Card>
            ))}
          </div>

          <datalist id="field-suggestions">
            {getFieldSuggestions().map(field => (
              <option key={field} value={field} />
            ))}
          </datalist>
        </TabsContent>

        <TabsContent value="filter" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Filter Conditions</h3>
            <Button size="sm" onClick={addFilterCondition}>
              <Plus className="h-4 w-4 mr-1" />
              Add Condition
            </Button>
          </div>
          
          <div className="space-y-3">
            {filterConditions.map((condition, index) => (
              <Card key={index} className="p-4">
                <div className="grid grid-cols-12 gap-2 items-center">
                  <div className="col-span-3">
                    <Input
                      placeholder="Field name"
                      value={condition.field}
                      onChange={(e) => updateFilterCondition(index, { field: e.target.value })}
                      list="field-suggestions"
                    />
                  </div>
                  <div className="col-span-2">
                    <Select 
                      value={condition.operator} 
                      onValueChange={(value) => updateFilterCondition(index, { operator: value as any })}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="eq">Equals</SelectItem>
                        <SelectItem value="ne">Not equals</SelectItem>
                        <SelectItem value="gt">Greater than</SelectItem>
                        <SelectItem value="lt">Less than</SelectItem>
                        <SelectItem value="gte">Greater or equal</SelectItem>
                        <SelectItem value="lte">Less or equal</SelectItem>
                        <SelectItem value="contains">Contains</SelectItem>
                        <SelectItem value="startswith">Starts with</SelectItem>
                        <SelectItem value="endswith">Ends with</SelectItem>
                        <SelectItem value="regex">Regex</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-3">
                    <Input
                      placeholder="Value"
                      value={condition.value}
                      onChange={(e) => updateFilterCondition(index, { value: e.target.value })}
                    />
                  </div>
                  <div className="col-span-2">
                    <Select 
                      value={condition.type} 
                      onValueChange={(value) => updateFilterCondition(index, { type: value as any })}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="string">String</SelectItem>
                        <SelectItem value="number">Number</SelectItem>
                        <SelectItem value="boolean">Boolean</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeFilterCondition(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="format" className="space-y-4">
          <div>
            <Label htmlFor="format-expression">Format Expression</Label>
            <Textarea
              id="format-expression"
              rows={4}
              value={customExpression}
              onChange={(e) => setCustomExpression(e.target.value)}
              placeholder="Enter format template, e.g., 'Hello {{name}}, you are {{age}} years old'"
              className="font-mono text-sm"
            />
            <div className="text-xs text-gray-500 mt-1">
              Use {{field}} syntax to insert field values
            </div>
          </div>
        </TabsContent>

        <TabsContent value="aggregate" className="space-y-4">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Aggregate mode will automatically count items and include metadata. 
              Additional aggregation functions can be configured in the custom expression.
            </AlertDescription>
          </Alert>
        </TabsContent>

        <TabsContent value="custom" className="space-y-4">
          <div>
            <Label htmlFor="custom-expression">Custom JavaScript Expression</Label>
            <Textarea
              id="custom-expression"
              rows={6}
              value={customExpression}
              onChange={(e) => setCustomExpression(e.target.value)}
              placeholder="// Transform data using JavaScript\nreturn data.map(item => ({\n  id: item.id,\n  fullName: `${item.firstName} ${item.lastName}`,\n  isActive: item.status === 'active'\n}));"
              className="font-mono text-sm"
            />
            <div className="text-xs text-gray-500 mt-1">
              Write JavaScript code to transform the data. Use 'data' variable to access input.
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Preview Section */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium">Preview</h3>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={generatePreview}>
              <Eye className="h-4 w-4 mr-1" />
              Generate Preview
            </Button>
            <Dialog open={showPreview} onOpenChange={setShowPreview}>
              <DialogTrigger asChild>
                <Button size="sm" variant="outline">
                  <Code className="h-4 w-4 mr-1" />
                  View Full
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Transformation Preview</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Sample Input Data:</h4>
                    <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                      {JSON.stringify(sampleData, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Transformed Output:</h4>
                    <pre className="bg-blue-50 p-3 rounded text-xs overflow-x-auto">
                      {JSON.stringify(previewData, null, 2)}
                    </pre>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {previewData && (
          <Card className="p-4">
            <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto max-h-40">
              {JSON.stringify(previewData, null, 2)}
            </pre>
          </Card>
        )}
      </div>

      {/* Validation */}
      <div className="space-y-2">
        {transformType === 'extract' && mappings.length === 0 && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              Add at least one field mapping for extraction
            </AlertDescription>
          </Alert>
        )}
        
        {transformType === 'filter' && filterConditions.length === 0 && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              Add at least one filter condition
            </AlertDescription>
          </Alert>
        )}
        
        {(transformType === 'format' || transformType === 'custom') && !customExpression && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              Expression is required for this transformation type
            </AlertDescription>
          </Alert>
        )}

        {transformType && targetKey && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Transformation configuration is valid
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};

export default DataTransformConfig;