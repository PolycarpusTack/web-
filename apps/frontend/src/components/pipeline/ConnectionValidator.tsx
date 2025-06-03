import { StepType, PipelineStep, PipelineConnection } from '@/types/pipeline';

export interface ConnectionValidationResult {
  valid: boolean;
  error?: string;
  warning?: string;
  suggestions?: string[];
}

export interface ConnectionCapability {
  stepType: StepType;
  inputs: {
    name: string;
    type: 'text' | 'json' | 'file' | 'number' | 'boolean' | 'array' | 'any';
    required: boolean;
    description: string;
  }[];
  outputs: {
    name: string;
    type: 'text' | 'json' | 'file' | 'number' | 'boolean' | 'array' | 'any';
    description: string;
  }[];
}

// Define step capabilities and connection rules
export const STEP_CAPABILITIES: Record<StepType, ConnectionCapability> = {
  [StepType.LLM]: {
    stepType: StepType.LLM,
    inputs: [
      { name: 'prompt', type: 'text', required: true, description: 'The prompt text for the LLM' },
      { name: 'system_prompt', type: 'text', required: false, description: 'System prompt for context' },
      { name: 'context', type: 'text', required: false, description: 'Additional context' },
      { name: 'variables', type: 'json', required: false, description: 'Template variables' }
    ],
    outputs: [
      { name: 'text', type: 'text', description: 'Generated text response' },
      { name: 'json', type: 'json', description: 'Structured JSON response (if requested)' },
      { name: 'tokens', type: 'number', description: 'Number of tokens used' },
      { name: 'cost', type: 'number', description: 'Execution cost' }
    ]
  },
  [StepType.CODE]: {
    stepType: StepType.CODE,
    inputs: [
      { name: 'code', type: 'text', required: true, description: 'Code to execute' },
      { name: 'variables', type: 'json', required: false, description: 'Variables available to code' },
      { name: 'input_data', type: 'any', required: false, description: 'Data to process' }
    ],
    outputs: [
      { name: 'result', type: 'any', description: 'Code execution result' },
      { name: 'logs', type: 'array', description: 'Execution logs' },
      { name: 'errors', type: 'array', description: 'Execution errors' }
    ]
  },
  [StepType.API]: {
    stepType: StepType.API,
    inputs: [
      { name: 'url', type: 'text', required: true, description: 'API endpoint URL' },
      { name: 'method', type: 'text', required: true, description: 'HTTP method' },
      { name: 'headers', type: 'json', required: false, description: 'Request headers' },
      { name: 'body', type: 'json', required: false, description: 'Request body' },
      { name: 'auth', type: 'json', required: false, description: 'Authentication details' }
    ],
    outputs: [
      { name: 'response', type: 'json', description: 'API response data' },
      { name: 'status', type: 'number', description: 'HTTP status code' },
      { name: 'headers', type: 'json', description: 'Response headers' }
    ]
  },
  [StepType.TRANSFORM]: {
    stepType: StepType.TRANSFORM,
    inputs: [
      { name: 'data', type: 'any', required: true, description: 'Data to transform' },
      { name: 'mapping', type: 'json', required: false, description: 'Field mapping configuration' },
      { name: 'filter', type: 'json', required: false, description: 'Filter conditions' }
    ],
    outputs: [
      { name: 'result', type: 'any', description: 'Transformed data' },
      { name: 'metadata', type: 'json', description: 'Transformation metadata' }
    ]
  },
  [StepType.CONDITION]: {
    stepType: StepType.CONDITION,
    inputs: [
      { name: 'data', type: 'any', required: true, description: 'Data to evaluate' },
      { name: 'condition', type: 'text', required: true, description: 'Condition expression' }
    ],
    outputs: [
      { name: 'result', type: 'boolean', description: 'Condition evaluation result' },
      { name: 'value', type: 'any', description: 'Original input value' },
      { name: 'true_path', type: 'any', description: 'Value if condition is true' },
      { name: 'false_path', type: 'any', description: 'Value if condition is false' }
    ]
  },
  [StepType.MERGE]: {
    stepType: StepType.MERGE,
    inputs: [
      { name: 'data1', type: 'any', required: true, description: 'First data input' },
      { name: 'data2', type: 'any', required: true, description: 'Second data input' },
      { name: 'strategy', type: 'text', required: false, description: 'Merge strategy' }
    ],
    outputs: [
      { name: 'result', type: 'any', description: 'Merged data' }
    ]
  },
  [StepType.INPUT]: {
    stepType: StepType.INPUT,
    inputs: [],
    outputs: [
      { name: 'value', type: 'any', description: 'Input value from pipeline start' }
    ]
  },
  [StepType.OUTPUT]: {
    stepType: StepType.OUTPUT,
    inputs: [
      { name: 'data', type: 'any', required: true, description: 'Data to output' }
    ],
    outputs: []
  }
};

export class ConnectionValidator {
  /**
   * Validate a proposed connection between two steps
   */
  static validateConnection(
    sourceStep: PipelineStep,
    targetStep: PipelineStep,
    sourceOutput: string,
    targetInput: string,
    existingConnections: PipelineConnection[] = []
  ): ConnectionValidationResult {
    // Get step capabilities
    const sourceCapability = STEP_CAPABILITIES[sourceStep.type];
    const targetCapability = STEP_CAPABILITIES[targetStep.type];

    if (!sourceCapability || !targetCapability) {
      return {
        valid: false,
        error: 'Unknown step type detected'
      };
    }

    // Check if source has the specified output
    const sourceOutputDef = sourceCapability.outputs.find(o => o.name === sourceOutput);
    if (!sourceOutputDef) {
      return {
        valid: false,
        error: `Source step '${sourceStep.name}' does not have output '${sourceOutput}'`,
        suggestions: sourceCapability.outputs.map(o => o.name)
      };
    }

    // Check if target has the specified input
    const targetInputDef = targetCapability.inputs.find(i => i.name === targetInput);
    if (!targetInputDef) {
      return {
        valid: false,
        error: `Target step '${targetStep.name}' does not have input '${targetInput}'`,
        suggestions: targetCapability.inputs.map(i => i.name)
      };
    }

    // Check type compatibility
    const typeCompatible = this.isTypeCompatible(sourceOutputDef.type, targetInputDef.type);
    if (!typeCompatible) {
      return {
        valid: false,
        error: `Type mismatch: ${sourceOutputDef.type} cannot connect to ${targetInputDef.type}`,
        warning: 'Consider adding a transform step to convert between types'
      };
    }

    // Check for circular dependencies
    const wouldCreateCycle = this.wouldCreateCycle(sourceStep, targetStep, existingConnections);
    if (wouldCreateCycle) {
      return {
        valid: false,
        error: 'Connection would create a circular dependency'
      };
    }

    // Check if target input is already connected
    const existingConnection = existingConnections.find(
      conn => conn.target_step_id === targetStep.id && conn.target_input === targetInput
    );
    if (existingConnection) {
      return {
        valid: false,
        error: `Input '${targetInput}' is already connected`,
        warning: 'Disconnect the existing connection first'
      };
    }

    // All checks passed
    return { valid: true };
  }

  /**
   * Check if two data types are compatible
   */
  private static isTypeCompatible(sourceType: string, targetType: string): boolean {
    // 'any' type is compatible with everything
    if (sourceType === 'any' || targetType === 'any') {
      return true;
    }

    // Exact match
    if (sourceType === targetType) {
      return true;
    }

    // Text can be converted to most types
    if (sourceType === 'text') {
      return ['text', 'json', 'number', 'boolean'].includes(targetType);
    }

    // JSON can be converted to text
    if (sourceType === 'json' && targetType === 'text') {
      return true;
    }

    // Number can be converted to text
    if (sourceType === 'number' && ['text', 'boolean'].includes(targetType)) {
      return true;
    }

    // Boolean can be converted to text or number
    if (sourceType === 'boolean' && ['text', 'number'].includes(targetType)) {
      return true;
    }

    // Array can be converted to text (as JSON string)
    if (sourceType === 'array' && targetType === 'text') {
      return true;
    }

    return false;
  }

  /**
   * Check if adding a connection would create a circular dependency
   */
  private static wouldCreateCycle(
    sourceStep: PipelineStep,
    targetStep: PipelineStep,
    existingConnections: PipelineConnection[]
  ): boolean {
    // If source step depends on target step (directly or indirectly), adding this connection would create a cycle
    const dependencies = this.getAllDependencies(sourceStep.id, existingConnections);
    return dependencies.includes(targetStep.id);
  }

  /**
   * Get all dependencies (direct and indirect) of a step
   */
  private static getAllDependencies(
    stepId: string,
    connections: PipelineConnection[],
    visited: Set<string> = new Set()
  ): string[] {
    if (visited.has(stepId)) {
      return []; // Avoid infinite recursion
    }
    visited.add(stepId);

    const directDependencies = connections
      .filter(conn => conn.source_step_id === stepId)
      .map(conn => conn.target_step_id);

    const allDependencies = [...directDependencies];

    // Recursively get dependencies of dependencies
    for (const depId of directDependencies) {
      allDependencies.push(...this.getAllDependencies(depId, connections, visited));
    }

    return [...new Set(allDependencies)]; // Remove duplicates
  }

  /**
   * Get suggestions for connecting two steps
   */
  static getConnectionSuggestions(
    sourceStep: PipelineStep,
    targetStep: PipelineStep
  ): Array<{ sourceOutput: string; targetInput: string; compatibility: number }> {
    const sourceCapability = STEP_CAPABILITIES[sourceStep.type];
    const targetCapability = STEP_CAPABILITIES[targetStep.type];

    if (!sourceCapability || !targetCapability) {
      return [];
    }

    const suggestions: Array<{ sourceOutput: string; targetInput: string; compatibility: number }> = [];

    // Try all output-input combinations
    for (const output of sourceCapability.outputs) {
      for (const input of targetCapability.inputs) {
        if (input.required || suggestions.length < 5) { // Prioritize required inputs
          const compatibility = this.calculateCompatibility(output, input);
          if (compatibility > 0) {
            suggestions.push({
              sourceOutput: output.name,
              targetInput: input.name,
              compatibility
            });
          }
        }
      }
    }

    // Sort by compatibility score (highest first)
    return suggestions.sort((a, b) => b.compatibility - a.compatibility);
  }

  /**
   * Calculate compatibility score between an output and input
   */
  private static calculateCompatibility(
    output: { name: string; type: string; description: string },
    input: { name: string; type: string; required: boolean; description: string }
  ): number {
    let score = 0;

    // Type compatibility
    if (this.isTypeCompatible(output.type, input.type)) {
      score += output.type === input.type ? 100 : 50; // Exact match gets higher score
    } else {
      return 0; // No compatibility if types don't match
    }

    // Name similarity
    if (output.name === input.name) {
      score += 50;
    } else if (output.name.includes(input.name) || input.name.includes(output.name)) {
      score += 25;
    }

    // Required inputs get priority
    if (input.required) {
      score += 30;
    }

    // Common patterns
    const commonMappings = [
      { output: 'text', input: 'prompt' },
      { output: 'result', input: 'data' },
      { output: 'response', input: 'input_data' },
      { output: 'json', input: 'variables' }
    ];

    for (const mapping of commonMappings) {
      if (output.name === mapping.output && input.name === mapping.input) {
        score += 40;
        break;
      }
    }

    return score;
  }

  /**
   * Validate an entire pipeline's connections
   */
  static validatePipelineConnections(
    steps: PipelineStep[],
    connections: PipelineConnection[]
  ): { valid: boolean; errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate each connection
    for (const connection of connections) {
      const sourceStep = steps.find(s => s.id === connection.source_step_id);
      const targetStep = steps.find(s => s.id === connection.target_step_id);

      if (!sourceStep) {
        errors.push(`Connection references non-existent source step: ${connection.source_step_id}`);
        continue;
      }

      if (!targetStep) {
        errors.push(`Connection references non-existent target step: ${connection.target_step_id}`);
        continue;
      }

      const validation = this.validateConnection(
        sourceStep,
        targetStep,
        connection.source_output,
        connection.target_input,
        connections
      );

      if (!validation.valid) {
        errors.push(`${sourceStep.name} → ${targetStep.name}: ${validation.error}`);
      }

      if (validation.warning) {
        warnings.push(`${sourceStep.name} → ${targetStep.name}: ${validation.warning}`);
      }
    }

    // Check for required inputs that are not connected
    for (const step of steps) {
      const capability = STEP_CAPABILITIES[step.type];
      if (!capability) continue;

      for (const input of capability.inputs) {
        if (input.required) {
          const isConnected = connections.some(
            conn => conn.target_step_id === step.id && conn.target_input === input.name
          );

          if (!isConnected) {
            // Check if the input is provided in step config
            const hasConfigValue = step.config && step.config[input.name];
            if (!hasConfigValue) {
              warnings.push(`Step '${step.name}' has unconnected required input: ${input.name}`);
            }
          }
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Suggest optimal connections for a pipeline
   */
  static suggestConnections(steps: PipelineStep[]): PipelineConnection[] {
    const suggestions: PipelineConnection[] = [];
    const stepsByOrder = [...steps].sort((a, b) => (a.position?.y || 0) - (b.position?.y || 0));

    for (let i = 0; i < stepsByOrder.length - 1; i++) {
      const sourceStep = stepsByOrder[i];
      const targetStep = stepsByOrder[i + 1];

      const connectionSuggestions = this.getConnectionSuggestions(sourceStep, targetStep);
      
      if (connectionSuggestions.length > 0) {
        const best = connectionSuggestions[0];
        suggestions.push({
          id: `suggested_${sourceStep.id}_${targetStep.id}`,
          source_step_id: sourceStep.id,
          target_step_id: targetStep.id,
          source_output: best.sourceOutput,
          target_input: best.targetInput,
          label: `${best.sourceOutput} → ${best.targetInput}`
        });
      }
    }

    return suggestions;
  }
}

export default ConnectionValidator;