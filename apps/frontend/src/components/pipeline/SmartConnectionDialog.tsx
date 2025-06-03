import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  ArrowRight, 
  Zap,
  Info,
  ThumbsUp
} from 'lucide-react';

import { PipelineStep, PipelineConnection } from '@/types/pipeline';
import { ConnectionValidator, STEP_CAPABILITIES } from './ConnectionValidator';

interface SmartConnectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sourceStep: PipelineStep | null;
  targetStep: PipelineStep | null;
  existingConnections: PipelineConnection[];
  onConnect: (sourceOutput: string, targetInput: string) => void;
}

export const SmartConnectionDialog: React.FC<SmartConnectionDialogProps> = ({
  open,
  onOpenChange,
  sourceStep,
  targetStep,
  existingConnections,
  onConnect
}) => {
  const [selectedConnection, setSelectedConnection] = useState<{
    sourceOutput: string;
    targetInput: string;
  } | null>(null);

  const [validationResult, setValidationResult] = useState<any>(null);

  // Get suggestions when dialog opens
  const suggestions = sourceStep && targetStep 
    ? ConnectionValidator.getConnectionSuggestions(sourceStep, targetStep)
    : [];

  // Validate selected connection
  useEffect(() => {
    if (sourceStep && targetStep && selectedConnection) {
      const result = ConnectionValidator.validateConnection(
        sourceStep,
        targetStep,
        selectedConnection.sourceOutput,
        selectedConnection.targetInput,
        existingConnections
      );
      setValidationResult(result);
    } else {
      setValidationResult(null);
    }
  }, [sourceStep, targetStep, selectedConnection, existingConnections]);

  const handleConnect = () => {
    if (selectedConnection && validationResult?.valid) {
      onConnect(selectedConnection.sourceOutput, selectedConnection.targetInput);
      onOpenChange(false);
      setSelectedConnection(null);
    }
  };

  const getCompatibilityColor = (compatibility: number) => {
    if (compatibility >= 80) return 'bg-green-100 text-green-800 border-green-200';
    if (compatibility >= 60) return 'bg-blue-100 text-blue-800 border-blue-200';
    if (compatibility >= 40) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getCompatibilityIcon = (compatibility: number) => {
    if (compatibility >= 80) return <ThumbsUp className="h-3 w-3" />;
    if (compatibility >= 60) return <CheckCircle className="h-3 w-3" />;
    if (compatibility >= 40) return <Info className="h-3 w-3" />;
    return <AlertTriangle className="h-3 w-3" />;
  };

  if (!sourceStep || !targetStep) {
    return null;
  }

  const sourceCapability = STEP_CAPABILITIES[sourceStep.type];
  const targetCapability = STEP_CAPABILITIES[targetStep.type];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-600" />
            Smart Connection Assistant
          </DialogTitle>
          <div className="text-sm text-gray-500">
            Connect "{sourceStep.name}" to "{targetStep.name}"
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Suggested Connections */}
          {suggestions.length > 0 ? (
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Suggested Connections</h3>
              <div className="space-y-2">
                {suggestions.slice(0, 5).map((suggestion, index) => (
                  <Card 
                    key={`${suggestion.sourceOutput}-${suggestion.targetInput}`}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedConnection?.sourceOutput === suggestion.sourceOutput &&
                      selectedConnection?.targetInput === suggestion.targetInput
                        ? 'ring-2 ring-blue-500 border-blue-200'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedConnection({
                      sourceOutput: suggestion.sourceOutput,
                      targetInput: suggestion.targetInput
                    })}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className="text-xs">
                            {index === 0 ? 'Best Match' : `Rank ${index + 1}`}
                          </Badge>
                          <div className="flex items-center gap-2 text-sm">
                            <code className="bg-blue-50 text-blue-700 px-2 py-1 rounded">
                              {suggestion.sourceOutput}
                            </code>
                            <ArrowRight className="h-4 w-4 text-gray-400" />
                            <code className="bg-green-50 text-green-700 px-2 py-1 rounded">
                              {suggestion.targetInput}
                            </code>
                          </div>
                        </div>
                        <Badge 
                          className={`text-xs ${getCompatibilityColor(suggestion.compatibility)}`}
                        >
                          {getCompatibilityIcon(suggestion.compatibility)}
                          {suggestion.compatibility}% match
                        </Badge>
                      </div>
                      
                      <div className="mt-2 text-xs text-gray-500 grid grid-cols-2 gap-4">
                        <div>
                          <span className="font-medium">Output:</span> {
                            sourceCapability.outputs.find(o => o.name === suggestion.sourceOutput)?.description
                          }
                        </div>
                        <div>
                          <span className="font-medium">Input:</span> {
                            targetCapability.inputs.find(i => i.name === suggestion.targetInput)?.description
                          }
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                No automatic suggestions available. You can manually select outputs and inputs below.
              </AlertDescription>
            </Alert>
          )}

          <Separator />

          {/* Manual Selection */}
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Manual Connection</h3>
            <div className="grid grid-cols-2 gap-6">
              {/* Source Outputs */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Available Outputs from "{sourceStep.name}"
                </h4>
                <div className="space-y-1">
                  {sourceCapability.outputs.map((output) => (
                    <div
                      key={output.name}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedConnection?.sourceOutput === output.name
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedConnection(prev => ({
                        sourceOutput: output.name,
                        targetInput: prev?.targetInput || ''
                      }))}
                    >
                      <div className="flex items-center justify-between">
                        <code className="text-sm font-medium">{output.name}</code>
                        <Badge variant="outline" className="text-xs">
                          {output.type}
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {output.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Target Inputs */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Available Inputs for "{targetStep.name}"
                </h4>
                <div className="space-y-1">
                  {targetCapability.inputs.map((input) => {
                    const isConnected = existingConnections.some(
                      conn => conn.target_step_id === targetStep.id && conn.target_input === input.name
                    );

                    return (
                      <div
                        key={input.name}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          isConnected
                            ? 'border-gray-300 bg-gray-100 opacity-60 cursor-not-allowed'
                            : selectedConnection?.targetInput === input.name
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                        onClick={() => !isConnected && setSelectedConnection(prev => ({
                          sourceOutput: prev?.sourceOutput || '',
                          targetInput: input.name
                        }))}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <code className="text-sm font-medium">{input.name}</code>
                            {input.required && (
                              <Badge variant="destructive" className="text-xs">
                                Required
                              </Badge>
                            )}
                            {isConnected && (
                              <Badge variant="secondary" className="text-xs">
                                Connected
                              </Badge>
                            )}
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {input.type}
                          </Badge>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {input.description}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Validation Result */}
          {validationResult && selectedConnection && (
            <div>
              <Separator />
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Connection Validation</h4>
                
                {validationResult.valid ? (
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      Connection is valid and ready to create!
                    </AlertDescription>
                  </Alert>
                ) : (
                  <Alert className="border-red-200 bg-red-50">
                    <XCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">
                      {validationResult.error}
                    </AlertDescription>
                  </Alert>
                )}

                {validationResult.warning && (
                  <Alert className="border-yellow-200 bg-yellow-50">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <AlertDescription className="text-yellow-800">
                      {validationResult.warning}
                    </AlertDescription>
                  </Alert>
                )}

                {validationResult.suggestions && validationResult.suggestions.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Suggestions:</div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {validationResult.suggestions.map((suggestion: string, index: number) => (
                        <li key={index} className="flex items-center gap-2">
                          <div className="w-1 h-1 bg-gray-400 rounded-full" />
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleConnect}
            disabled={!selectedConnection || !validationResult?.valid}
          >
            Create Connection
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SmartConnectionDialog;