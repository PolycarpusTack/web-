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
  GitBranch, 
  Code, 
  TestTube,
  Info,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  ArrowDown
} from 'lucide-react';

import { PipelineStepConfig } from '@/types/pipeline-config';

interface Condition {
  id: string;
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'contains' | 'exists' | 'regex';
  value: string;
  type: 'string' | 'number' | 'boolean' | 'array';
  description?: string;
}

interface ConditionalBranch {
  condition: string; // true or false
  steps: string[];
  description?: string;
}

interface ConditionStepConfigProps {
  config: PipelineStepConfig;
  onChange: (config: PipelineStepConfig) => void;
  availableVariables?: string[];
}

export const ConditionStepConfig: React.FC<ConditionStepConfigProps> = ({
  config,
  onChange,
  availableVariables = []
}) => {
  const [conditionMode, setConditionMode] = useState<'simple' | 'complex' | 'expression'>(
    config.condition_mode || 'simple'
  );
  const [conditions, setConditions] = useState<Condition[]>(
    (config.conditions || []).map(c => ({
      ...c,
      operator: c.operator as Condition['operator'],
      type: c.type as Condition['type']
    }))
  );
  const [logicalOperator, setLogicalOperator] = useState<'AND' | 'OR'>(config.logical_operator || 'AND');
  const [customExpression, setCustomExpression] = useState<string>(config.custom_expression || '');
  const [branches, setBranches] = useState<ConditionalBranch[]>(config.branches || []);
  const [defaultBranch, setDefaultBranch] = useState<string>(config.default_branch || 'false');
  const [testData, setTestData] = useState<any>(config.test_data || {});
  const [testResult, setTestResult] = useState<any>(null);

  // Update config when state changes
  useEffect(() => {
    const newConfig = {
      ...config,
      condition_mode: conditionMode,
      conditions,
      logical_operator: logicalOperator,
      custom_expression: customExpression,
      branches,
      default_branch: defaultBranch,
      test_data: testData
    };
    onChange(newConfig);
  }, [conditionMode, conditions, logicalOperator, customExpression, branches, defaultBranch, testData]);

  // Add new condition
  const addCondition = () => {
    const newCondition: Condition = {
      id: `condition_${Date.now()}`,
      field: '',
      operator: 'eq',
      value: '',
      type: 'string'
    };
    setConditions([...conditions, newCondition]);
  };

  // Update condition
  const updateCondition = (id: string, updates: Partial<Condition>) => {
    setConditions(conditions.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  // Remove condition
  const removeCondition = (id: string) => {
    setConditions(conditions.filter(c => c.id !== id));
  };

  // Add branch
  const addBranch = () => {
    const newBranch: ConditionalBranch = {
      condition: 'true',
      steps: [],
      description: ''
    };
    setBranches([...branches, newBranch]);
  };

  // Update branch
  const updateBranch = (index: number, updates: Partial<ConditionalBranch>) => {
    const newBranches = [...branches];
    newBranches[index] = { ...newBranches[index], ...updates };
    setBranches(newBranches);
  };

  // Remove branch
  const removeBranch = (index: number) => {
    setBranches(branches.filter((_, i) => i !== index));
  };

  // Test condition evaluation
  const testCondition = () => {
    try {
      let result = false;

      if (conditionMode === 'simple' && conditions.length > 0) {
        const results = conditions.map(condition => {
          const fieldValue = getNestedValue(testData, condition.field);
          return evaluateCondition(fieldValue, condition);
        });

        result = logicalOperator === 'AND' 
          ? results.every(r => r)
          : results.some(r => r);
      } else if (conditionMode === 'expression' && customExpression) {
        // Simple expression evaluation (in real app, this would be more sophisticated)
        const expression = customExpression
          .replace(/{{(\w+)}}/g, (match, key) => {
            const value = getNestedValue(testData, key);
            return typeof value === 'string' ? `"${value}"` : String(value);
          });
        
        // Basic expression evaluation (simplified)
        result = Boolean(eval(expression));
      }

      setTestResult({
        success: true,
        result,
        branch: result ? 'true' : 'false',
        evaluation: conditions.map(c => ({
          condition: c,
          fieldValue: getNestedValue(testData, c.field),
          result: evaluateCondition(getNestedValue(testData, c.field), c)
        }))
      });
    } catch (error) {
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : String(error)
      });
    }
  };

  // Helper function to get nested value
  const getNestedValue = (obj: any, path: string): any => {
    if (!path) return obj;
    return path.split('.').reduce((current, key) => 
      current && typeof current === 'object' ? current[key] : undefined, obj
    );
  };

  // Helper function to evaluate a single condition
  const evaluateCondition = (fieldValue: any, condition: Condition): boolean => {
    const { operator, value, type } = condition;
    
    let conditionValue: any = value;
    if (type === 'number') conditionValue = Number(value);
    else if (type === 'boolean') conditionValue = value === 'true';
    else if (type === 'array') conditionValue = value.split(',').map(v => v.trim());

    switch (operator) {
      case 'eq': return fieldValue === conditionValue;
      case 'ne': return fieldValue !== conditionValue;
      case 'gt': return fieldValue > conditionValue;
      case 'lt': return fieldValue < conditionValue;
      case 'gte': return fieldValue >= conditionValue;
      case 'lte': return fieldValue <= conditionValue;
      case 'in': 
        return Array.isArray(conditionValue) 
          ? conditionValue.includes(fieldValue)
          : String(conditionValue).includes(String(fieldValue));
      case 'contains':
        return Array.isArray(fieldValue) 
          ? fieldValue.includes(conditionValue)
          : String(fieldValue).includes(String(conditionValue));
      case 'exists': return fieldValue !== undefined && fieldValue !== null;
      case 'regex':
        try {
          return new RegExp(String(conditionValue)).test(String(fieldValue));
        } catch {
          return false;
        }
      default: return false;
    }
  };

  const getOperatorDisplay = (operator: string) => {
    const operators = {
      eq: 'equals',
      ne: 'not equals',
      gt: 'greater than',
      lt: 'less than',
      gte: 'greater or equal',
      lte: 'less or equal',
      in: 'in',
      contains: 'contains',
      exists: 'exists',
      regex: 'matches regex'
    };
    return operators[operator as keyof typeof operators] || operator;
  };

  return (
    <div className="space-y-6">
      {/* Condition Mode Selection */}
      <div>
        <Label className="text-sm font-medium mb-2 block">Condition Mode</Label>
        <Select value={conditionMode} onValueChange={(value) => setConditionMode(value as any)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="simple">Simple Conditions</SelectItem>
            <SelectItem value="complex">Complex Logic</SelectItem>
            <SelectItem value="expression">Custom Expression</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Configuration based on mode */}
      <Tabs value={conditionMode} className="w-full">
        <TabsContent value="simple" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Conditions</h3>
            <div className="flex items-center gap-2">
              <Select value={logicalOperator} onValueChange={(value) => setLogicalOperator(value as any)}>
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="AND">AND</SelectItem>
                  <SelectItem value="OR">OR</SelectItem>
                </SelectContent>
              </Select>
              <Button size="sm" onClick={addCondition}>
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            </div>
          </div>

          <div className="space-y-3">
            {conditions.map((condition, index) => (
              <Card key={condition.id} className="p-4">
                <div className="grid grid-cols-12 gap-2 items-center">
                  <div className="col-span-3">
                    <Input
                      placeholder="Field path"
                      value={condition.field}
                      onChange={(e) => updateCondition(condition.id, { field: e.target.value })}
                      list="variable-suggestions"
                    />
                  </div>
                  <div className="col-span-2">
                    <Select 
                      value={condition.operator} 
                      onValueChange={(value) => updateCondition(condition.id, { operator: value as any })}
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
                        <SelectItem value="in">In</SelectItem>
                        <SelectItem value="contains">Contains</SelectItem>
                        <SelectItem value="exists">Exists</SelectItem>
                        <SelectItem value="regex">Regex</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-3">
                    {condition.operator !== 'exists' && (
                      <Input
                        placeholder="Value"
                        value={condition.value}
                        onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
                      />
                    )}
                  </div>
                  <div className="col-span-2">
                    <Select 
                      value={condition.type} 
                      onValueChange={(value) => updateCondition(condition.id, { type: value as any })}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="string">String</SelectItem>
                        <SelectItem value="number">Number</SelectItem>
                        <SelectItem value="boolean">Boolean</SelectItem>
                        <SelectItem value="array">Array</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeCondition(condition.id)}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="col-span-1 text-center">
                    {index < conditions.length - 1 && (
                      <Badge variant="outline" className="text-xs">
                        {logicalOperator}
                      </Badge>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <datalist id="variable-suggestions">
            {availableVariables.map(variable => (
              <option key={variable} value={variable} />
            ))}
          </datalist>
        </TabsContent>

        <TabsContent value="complex" className="space-y-4">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Complex logic mode allows you to define custom branching paths based on condition results.
            </AlertDescription>
          </Alert>

          {/* Branches Configuration */}
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Conditional Branches</h3>
            <Button size="sm" onClick={addBranch}>
              <Plus className="h-4 w-4 mr-1" />
              Add Branch
            </Button>
          </div>

          <div className="space-y-3">
            {branches.map((branch, index) => (
              <Card key={index} className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-4 w-4" />
                    <Select 
                      value={branch.condition} 
                      onValueChange={(value) => updateBranch(index, { condition: value })}
                    >
                      <SelectTrigger className="w-24">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="true">True</SelectItem>
                        <SelectItem value="false">False</SelectItem>
                      </SelectContent>
                    </Select>
                    <span className="text-sm text-gray-500">branch</span>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => removeBranch(index)}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                </div>
                <Input
                  placeholder="Branch description"
                  value={branch.description || ''}
                  onChange={(e) => updateBranch(index, { description: e.target.value })}
                  className="text-sm"
                />
              </Card>
            ))}
          </div>

          <div>
            <Label htmlFor="default-branch">Default Branch</Label>
            <Select value={defaultBranch} onValueChange={setDefaultBranch}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="true">True branch</SelectItem>
                <SelectItem value="false">False branch</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </TabsContent>

        <TabsContent value="expression" className="space-y-4">
          <div>
            <Label htmlFor="custom-expression">Custom Expression</Label>
            <Textarea
              id="custom-expression"
              rows={4}
              value={customExpression}
              onChange={(e) => setCustomExpression(e.target.value)}
              placeholder="Enter JavaScript expression, e.g., {{age}} > 18 && {{status}} === 'active'"
              className="font-mono text-sm"
            />
            <div className="text-xs text-gray-500 mt-1">
              Use {'{{field}}'} syntax to reference data fields. Expression should return boolean.
            </div>
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Examples:
              <br />• <code>{'{{'}{'{'}age{'}'} {'>='} 21</code>
              <br />• <code>{'{{'}{'{'}status{'}'} === 'active' {'&&'} {'{{'}{'{'}verified{'}'} === true</code>
              <br />• <code>{'{{'}{'{'}items{'}'}.length {'>'} 0</code>
            </AlertDescription>
          </Alert>
        </TabsContent>
      </Tabs>

      {/* Test Section */}
      <div className="border-t pt-4">
        <h3 className="text-sm font-medium mb-3">Test Condition</h3>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <Label htmlFor="test-data">Test Data (JSON)</Label>
            <Textarea
              id="test-data"
              rows={4}
              value={JSON.stringify(testData, null, 2)}
              onChange={(e) => {
                try {
                  const data = JSON.parse(e.target.value);
                  setTestData(data);
                } catch (error) {
                  // Invalid JSON, don't update
                }
              }}
              className="font-mono text-xs"
              placeholder='{"age": 25, "status": "active", "verified": true}'
            />
          </div>
          <div>
            <Label>Test Result</Label>
            <div className="space-y-2">
              <Button size="sm" onClick={testCondition} className="w-full">
                <TestTube className="h-4 w-4 mr-1" />
                Test Condition
              </Button>
              
              {testResult && (
                <Card className="p-3">
                  {testResult.success ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="text-sm font-medium">
                          Result: {testResult.result ? 'TRUE' : 'FALSE'}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Branch: {testResult.branch}
                      </div>
                      {testResult.evaluation && (
                        <div className="space-y-1">
                          {testResult.evaluation.map((evalItem: any, index: number) => (
                            <div key={index} className="text-xs">
                              <code>{evalItem.condition.field}</code> {getOperatorDisplay(evalItem.condition.operator)} <code>{evalItem.condition.value}</code> 
                              <ArrowRight className="inline h-3 w-3 mx-1" />
                              <Badge variant={evalItem.result ? "default" : "secondary"} className="text-xs">
                                {evalItem.result ? 'TRUE' : 'FALSE'}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      <span className="text-sm text-red-600">
                        Error: {testResult.error}
                      </span>
                    </div>
                  )}
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Validation */}
      <div className="space-y-2">
        {conditionMode === 'simple' && conditions.length === 0 && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              Add at least one condition for simple mode
            </AlertDescription>
          </Alert>
        )}
        
        {conditionMode === 'expression' && !customExpression && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              Custom expression is required for expression mode
            </AlertDescription>
          </Alert>
        )}

        {((conditionMode === 'simple' && conditions.length > 0) || 
          (conditionMode === 'expression' && customExpression)) && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Condition configuration is valid
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};

export default ConditionStepConfig;