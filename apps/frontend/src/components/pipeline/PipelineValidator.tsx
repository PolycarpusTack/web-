import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Info,
  RefreshCw,
  FileCheck,
  Activity,
  DollarSign,
  Clock
} from 'lucide-react';

import { PipelineDefinition, ValidationResult, ValidationError } from '@/types/pipeline';
import { ConnectionValidator } from './ConnectionValidator';

interface PipelineValidatorProps {
  pipeline: PipelineDefinition;
  onValidationChange?: (result: ValidationResult) => void;
  autoValidate?: boolean;
  showEstimates?: boolean;
}

interface ValidationSummary {
  totalChecks: number;
  passed: number;
  warnings: number;
  errors: number;
  score: number;
}

interface ExecutionEstimate {
  estimatedDuration: number; // seconds
  estimatedCost: number; // dollars
  estimatedTokens: number;
  complexity: 'low' | 'medium' | 'high';
}

export const PipelineValidator: React.FC<PipelineValidatorProps> = ({
  pipeline,
  onValidationChange,
  autoValidate = true,
  showEstimates = true
}) => {
  const [validationResult, setValidationResult] = useState<ValidationResult>({
    valid: true,
    errors: [],
    warnings: []
  });
  
  const [isValidating, setIsValidating] = useState(false);
  const [lastValidated, setLastValidated] = useState<Date | null>(null);

  // Comprehensive validation
  const validatePipeline = useMemo(() => {
    return (): ValidationResult => {
      const errors: ValidationError[] = [];
      const warnings: ValidationError[] = [];

      // Basic pipeline structure validation
      if (!pipeline.name || pipeline.name.trim() === '') {
        errors.push({
          message: 'Pipeline name is required',
          severity: 'error'
        });
      }

      if (pipeline.steps.length === 0) {
        warnings.push({
          message: 'Pipeline has no steps',
          severity: 'warning'
        });
      }

      // Step validation
      pipeline.steps.forEach((step, index) => {
        const stepPrefix = `Step "${step.name}" (${index + 1})`;

        // Step name validation
        if (!step.name || step.name.trim() === '') {
          errors.push({
            step_id: step.id,
            step_name: step.name,
            message: `${stepPrefix}: Step name is required`,
            severity: 'error'
          });
        }

        // Check for duplicate step names
        const duplicateNames = pipeline.steps.filter(s => s.name === step.name);
        if (duplicateNames.length > 1) {
          warnings.push({
            step_id: step.id,
            step_name: step.name,
            message: `${stepPrefix}: Duplicate step name found`,
            severity: 'warning'
          });
        }

        // Step-specific validation
        switch (step.type) {
          case 'llm':
            if (!step.config?.model_id) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'model_id',
                message: `${stepPrefix}: Model selection is required`,
                severity: 'error'
              });
            }
            if (!step.config?.prompt) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'prompt',
                message: `${stepPrefix}: Prompt is required`,
                severity: 'error'
              });
            }
            if (step.config?.max_tokens && (step.config.max_tokens < 1 || step.config.max_tokens > 100000)) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'max_tokens',
                message: `${stepPrefix}: Max tokens must be between 1 and 100,000`,
                severity: 'error'
              });
            }
            if (step.config?.temperature && (step.config.temperature < 0 || step.config.temperature > 2)) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'temperature',
                message: `${stepPrefix}: Temperature must be between 0 and 2`,
                severity: 'error'
              });
            }
            break;

          case 'code':
            if (!step.config?.code) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'code',
                message: `${stepPrefix}: Code is required`,
                severity: 'error'
              });
            }
            if (!step.config?.language) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'language',
                message: `${stepPrefix}: Programming language must be specified`,
                severity: 'error'
              });
            }
            if (step.config?.timeout && step.config.timeout > 300) {
              warnings.push({
                step_id: step.id,
                step_name: step.name,
                field: 'timeout',
                message: `${stepPrefix}: Long timeout may affect performance`,
                severity: 'warning'
              });
            }
            // Check for potentially unsafe code patterns
            if (step.config?.code) {
              const unsafePatterns = ['__import__', 'eval(', 'exec(', 'open('];
              for (const pattern of unsafePatterns) {
                if (step.config.code.includes(pattern)) {
                  warnings.push({
                    step_id: step.id,
                    step_name: step.name,
                    field: 'code',
                    message: `${stepPrefix}: Code contains potentially unsafe pattern: ${pattern}`,
                    severity: 'warning'
                  });
                }
              }
            }
            break;

          case 'api':
            if (!step.config?.url) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'url',
                message: `${stepPrefix}: API URL is required`,
                severity: 'error'
              });
            } else {
              try {
                new URL(step.config.url);
              } catch {
                errors.push({
                  step_id: step.id,
                  step_name: step.name,
                  field: 'url',
                  message: `${stepPrefix}: Invalid URL format`,
                  severity: 'error'
                });
              }
            }
            if (!step.config?.method) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'method',
                message: `${stepPrefix}: HTTP method is required`,
                severity: 'error'
              });
            }
            break;

          case 'transform':
            if (!step.config?.type) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'type',
                message: `${stepPrefix}: Transform type is required`,
                severity: 'error'
              });
            }
            break;

          case 'condition':
            if (!step.config?.condition) {
              errors.push({
                step_id: step.id,
                step_name: step.name,
                field: 'condition',
                message: `${stepPrefix}: Condition expression is required`,
                severity: 'error'
              });
            }
            break;
        }

        // Timeout validation
        if (step.timeout && step.timeout <= 0) {
          errors.push({
            step_id: step.id,
            step_name: step.name,
            field: 'timeout',
            message: `${stepPrefix}: Timeout must be positive`,
            severity: 'error'
          });
        }

        // Check if step is disabled without reason
        if (!step.enabled) {
          warnings.push({
            step_id: step.id,
            step_name: step.name,
            message: `${stepPrefix}: Step is disabled`,
            severity: 'warning'
          });
        }
      });

      // Connection validation using ConnectionValidator
      const connectionValidation = ConnectionValidator.validatePipelineConnections(
        pipeline.steps,
        pipeline.connections
      );

      // Add connection errors and warnings
      connectionValidation.errors.forEach(error => {
        errors.push({
          message: error,
          severity: 'error'
        });
      });

      connectionValidation.warnings.forEach(warning => {
        warnings.push({
          message: warning,
          severity: 'warning'
        });
      });

      // Check for isolated steps
      pipeline.steps.forEach(step => {
        const hasIncomingConnection = pipeline.connections.some(conn => conn.target_step_id === step.id);
        const hasOutgoingConnection = pipeline.connections.some(conn => conn.source_step_id === step.id);
        
        if (!hasIncomingConnection && !hasOutgoingConnection && pipeline.steps.length > 1) {
          warnings.push({
            step_id: step.id,
            step_name: step.name,
            message: `Step "${step.name}" is not connected to any other steps`,
            severity: 'warning'
          });
        }
      });

      // Pipeline variables validation
      if (pipeline.variables) {
        try {
          JSON.stringify(pipeline.variables);
        } catch {
          errors.push({
            message: 'Pipeline variables contain invalid JSON',
            severity: 'error'
          });
        }
      }

      return {
        valid: errors.length === 0,
        errors,
        warnings
      };
    };
  }, [pipeline]);

  // Auto-validation
  useEffect(() => {
    if (autoValidate) {
      setIsValidating(true);
      
      // Debounce validation
      const timer = setTimeout(() => {
        const result = validatePipeline();
        setValidationResult(result);
        setLastValidated(new Date());
        setIsValidating(false);
        onValidationChange?.(result);
      }, 300);

      return () => clearTimeout(timer);
    }
  }, [pipeline, validatePipeline, autoValidate, onValidationChange]);

  // Manual validation
  const runValidation = () => {
    setIsValidating(true);
    setTimeout(() => {
      const result = validatePipeline();
      setValidationResult(result);
      setLastValidated(new Date());
      setIsValidating(false);
      onValidationChange?.(result);
    }, 100);
  };

  // Calculate validation summary
  const summary: ValidationSummary = useMemo(() => {
    const totalChecks = pipeline.steps.length * 3 + pipeline.connections.length + 2; // Rough estimate
    const errors = validationResult.errors.length;
    const warnings = validationResult.warnings.length;
    const passed = Math.max(0, totalChecks - errors - warnings);
    const score = totalChecks > 0 ? Math.round((passed / totalChecks) * 100) : 100;

    return {
      totalChecks,
      passed,
      warnings,
      errors,
      score
    };
  }, [validationResult, pipeline]);

  // Calculate execution estimates
  const estimates: ExecutionEstimate = useMemo(() => {
    let estimatedDuration = 0;
    let estimatedCost = 0;
    let estimatedTokens = 0;
    let complexityFactors = 0;

    pipeline.steps.forEach(step => {
      if (!step.enabled) return;

      switch (step.type) {
        case 'llm':
          estimatedDuration += 3; // 3 seconds average
          estimatedTokens += step.config?.max_tokens || 1000;
          estimatedCost += (estimatedTokens / 1000) * 0.02; // Rough estimate
          complexityFactors += 2;
          break;
        case 'code':
          estimatedDuration += step.config?.timeout || 30;
          complexityFactors += 3;
          break;
        case 'api':
          estimatedDuration += 2; // 2 seconds average for API call
          complexityFactors += 1;
          break;
        case 'transform':
          estimatedDuration += 0.5;
          complexityFactors += 1;
          break;
        case 'condition':
          estimatedDuration += 0.1;
          complexityFactors += 0.5;
          break;
      }
    });

    const avgComplexity = complexityFactors / Math.max(pipeline.steps.length, 1);
    const complexity = avgComplexity > 2 ? 'high' : avgComplexity > 1 ? 'medium' : 'low';

    return {
      estimatedDuration,
      estimatedCost,
      estimatedTokens,
      complexity
    };
  }, [pipeline]);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Pipeline Validation
          </div>
          <div className="flex items-center gap-2">
            {isValidating && <RefreshCw className="h-4 w-4 animate-spin" />}
            <Button variant="outline" size="sm" onClick={runValidation} disabled={isValidating}>
              <FileCheck className="h-4 w-4 mr-1" />
              Validate
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="summary" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="errors">
              Errors ({validationResult.errors.length})
            </TabsTrigger>
            <TabsTrigger value="warnings">
              Warnings ({validationResult.warnings.length})
            </TabsTrigger>
            {showEstimates && <TabsTrigger value="estimates">Estimates</TabsTrigger>}
          </TabsList>

          <TabsContent value="summary" className="space-y-4">
            {/* Validation Score */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Validation Score</span>
                <span className={`text-lg font-bold ${getScoreColor(summary.score)}`}>
                  {summary.score}%
                </span>
              </div>
              <Progress value={summary.score} className="h-2" />
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{summary.passed}</div>
                <div className="text-xs text-gray-500">Passed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{summary.warnings}</div>
                <div className="text-xs text-gray-500">Warnings</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{summary.errors}</div>
                <div className="text-xs text-gray-500">Errors</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{pipeline.steps.length}</div>
                <div className="text-xs text-gray-500">Steps</div>
              </div>
            </div>

            {/* Overall Status */}
            <Alert className={validationResult.valid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
              {validationResult.valid ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 text-red-600" />
              )}
              <AlertDescription className={validationResult.valid ? 'text-green-800' : 'text-red-800'}>
                {validationResult.valid
                  ? 'Pipeline is valid and ready for execution!'
                  : `Pipeline has ${validationResult.errors.length} error(s) that must be fixed before execution.`
                }
              </AlertDescription>
            </Alert>

            {lastValidated && (
              <div className="text-xs text-gray-500 text-right">
                Last validated: {lastValidated.toLocaleTimeString()}
              </div>
            )}
          </TabsContent>

          <TabsContent value="errors" className="space-y-2">
            <ScrollArea className="h-64">
              {validationResult.errors.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  No errors found!
                </div>
              ) : (
                <div className="space-y-2">
                  {validationResult.errors.map((error, index) => (
                    <Alert key={index} className="border-red-200 bg-red-50">
                      <XCircle className="h-4 w-4 text-red-600" />
                      <AlertDescription className="text-red-800">
                        <div>{error.message}</div>
                        {error.field && (
                          <div className="text-xs mt-1">Field: {error.field}</div>
                        )}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="warnings" className="space-y-2">
            <ScrollArea className="h-64">
              {validationResult.warnings.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  No warnings!
                </div>
              ) : (
                <div className="space-y-2">
                  {validationResult.warnings.map((warning, index) => (
                    <Alert key={index} className="border-yellow-200 bg-yellow-50">
                      <AlertTriangle className="h-4 w-4 text-yellow-600" />
                      <AlertDescription className="text-yellow-800">
                        <div>{warning.message}</div>
                        {warning.field && (
                          <div className="text-xs mt-1">Field: {warning.field}</div>
                        )}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          {showEstimates && (
            <TabsContent value="estimates" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="h-4 w-4 text-blue-600" />
                      <span className="font-medium">Execution Time</span>
                    </div>
                    <div className="text-2xl font-bold text-blue-600">
                      {estimates.estimatedDuration < 60
                        ? `${Math.round(estimates.estimatedDuration)}s`
                        : `${Math.round(estimates.estimatedDuration / 60)}m ${Math.round(estimates.estimatedDuration % 60)}s`
                      }
                    </div>
                    <div className="text-xs text-gray-500">Estimated duration</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <span className="font-medium">Estimated Cost</span>
                    </div>
                    <div className="text-2xl font-bold text-green-600">
                      ${estimates.estimatedCost.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {estimates.estimatedTokens.toLocaleString()} tokens
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Complexity</span>
                  <Badge className={getComplexityColor(estimates.complexity)}>
                    {estimates.complexity.toUpperCase()}
                  </Badge>
                </div>
                <div className="text-sm text-gray-600">
                  Based on step types, configurations, and connections
                </div>
              </div>

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  These are rough estimates based on step types and configurations. 
                  Actual execution time and cost may vary depending on model performance, 
                  network conditions, and data complexity.
                </AlertDescription>
              </Alert>
            </TabsContent>
          )}
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default PipelineValidator;