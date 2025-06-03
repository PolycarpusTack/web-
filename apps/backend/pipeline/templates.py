"""
Pipeline Templates for Code Factory.

This module provides predefined templates for common pipeline configurations,
making it easier to create new pipelines with standard patterns.
"""

from typing import Dict, List, Any, Optional
import json

from db.pipeline_models import PipelineStepType


def create_step_config(
    step_type: PipelineStepType,
    name: str,
    config: Dict[str, Any],
    description: Optional[str] = None,
    order: int = 0,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a step configuration object.
    
    Args:
        step_type: The type of step
        name: The step name
        config: Step-specific configuration
        description: Optional description
        order: Step order
        input_mapping: Optional mapping for inputs
        output_mapping: Optional mapping for outputs
        
    Returns:
        Dictionary with step configuration
    """
    return {
        "type": step_type.value,
        "name": name,
        "description": description,
        "order": order,
        "config": config,
        "input_mapping": input_mapping,
        "output_mapping": output_mapping
    }


def create_prompt_step(
    name: str,
    model_id: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    description: Optional[str] = None,
    order: int = 0,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a prompt step configuration.
    
    Args:
        name: Step name
        model_id: ID of the model to use
        prompt: The prompt to send
        system_prompt: Optional system prompt
        description: Optional description
        order: Step order
        input_mapping: Optional mapping for inputs
        output_mapping: Optional mapping for outputs
        options: Optional model-specific options
        
    Returns:
        Dictionary with prompt step configuration
    """
    config = {
        "model_id": model_id,
        "prompt": prompt,
    }
    
    if system_prompt:
        config["system_prompt"] = system_prompt
    
    if options:
        config["options"] = options
    
    return create_step_config(
        step_type=PipelineStepType.PROMPT,
        name=name,
        config=config,
        description=description,
        order=order,
        input_mapping=input_mapping,
        output_mapping=output_mapping
    )


def create_code_step(
    name: str,
    code: str,
    language: str = "python",
    description: Optional[str] = None,
    order: int = 0,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a code step configuration.
    
    Args:
        name: Step name
        code: The code to execute
        language: Programming language
        description: Optional description
        order: Step order
        input_mapping: Optional mapping for inputs
        output_mapping: Optional mapping for outputs
        timeout: Optional timeout in seconds
        
    Returns:
        Dictionary with code step configuration
    """
    config = {
        "code": code,
        "language": language
    }
    
    if timeout:
        config["timeout"] = timeout
    
    return create_step_config(
        step_type=PipelineStepType.CODE,
        name=name,
        config=config,
        description=description,
        order=order,
        input_mapping=input_mapping,
        output_mapping=output_mapping
    )


def create_file_step(
    name: str,
    operation: str,
    file_path: str,
    content: Optional[str] = None,
    description: Optional[str] = None,
    order: int = 0,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a file step configuration.
    
    Args:
        name: Step name
        operation: Operation to perform ("read" or "write")
        file_path: Path to the file
        content: Content to write (for "write" operation)
        description: Optional description
        order: Step order
        input_mapping: Optional mapping for inputs
        output_mapping: Optional mapping for outputs
        
    Returns:
        Dictionary with file step configuration
    """
    config = {
        "operation": operation,
        "file_path": file_path
    }
    
    if operation == "write" and content is not None:
        config["content"] = content
    
    return create_step_config(
        step_type=PipelineStepType.FILE,
        name=name,
        config=config,
        description=description,
        order=order,
        input_mapping=input_mapping,
        output_mapping=output_mapping
    )


def create_api_step(
    name: str,
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    order: int = 0,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an API step configuration.
    
    Args:
        name: Step name
        url: API endpoint URL
        method: HTTP method
        headers: Optional HTTP headers
        data: Optional request data
        description: Optional description
        order: Step order
        input_mapping: Optional mapping for inputs
        output_mapping: Optional mapping for outputs
        
    Returns:
        Dictionary with API step configuration
    """
    config = {
        "url": url,
        "method": method
    }
    
    if headers:
        config["headers"] = headers
    
    if data:
        config["data"] = data
    
    return create_step_config(
        step_type=PipelineStepType.API,
        name=name,
        config=config,
        description=description,
        order=order,
        input_mapping=input_mapping,
        output_mapping=output_mapping
    )


def create_condition_step(
    name: str,
    condition: str,
    description: Optional[str] = None,
    order: int = 0,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a condition step configuration.
    
    Args:
        name: Step name
        condition: Condition expression
        description: Optional description
        order: Step order
        input_mapping: Optional mapping for inputs
        output_mapping: Optional mapping for outputs
        
    Returns:
        Dictionary with condition step configuration
    """
    config = {
        "condition": condition
    }
    
    return create_step_config(
        step_type=PipelineStepType.CONDITION,
        name=name,
        config=config,
        description=description,
        order=order,
        input_mapping=input_mapping,
        output_mapping=output_mapping
    )


def create_transform_step(
    name: str,
    transform_type: str,
    data_path: str,
    description: Optional[str] = None,
    order: int = 0,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a transform step configuration.
    
    Args:
        name: Step name
        transform_type: Type of transformation
        data_path: Path to data in context
        description: Optional description
        order: Step order
        input_mapping: Optional mapping for inputs
        output_mapping: Optional mapping for outputs
        
    Returns:
        Dictionary with transform step configuration
    """
    config = {
        "transform_type": transform_type,
        "data_path": data_path
    }
    
    return create_step_config(
        step_type=PipelineStepType.TRANSFORM,
        name=name,
        config=config,
        description=description,
        order=order,
        input_mapping=input_mapping,
        output_mapping=output_mapping
    )


# --- Pipeline Templates ---

def create_code_generation_pipeline(
    name: str,
    description: str,
    model_id: str,
    output_file_path: str,
    language: str
) -> Dict[str, Any]:
    """
    Create a simple code generation pipeline.
    
    Args:
        name: Pipeline name
        description: Pipeline description
        model_id: ID of the model to use
        output_file_path: Path to save generated code
        language: Programming language
        
    Returns:
        Dictionary with pipeline configuration
    """
    # Create prompt step
    generate_step = create_prompt_step(
        name="Generate Code",
        model_id=model_id,
        prompt="Generate {{language}} code to implement the following:\n\n{{input.requirements}}",
        system_prompt="You are an expert {{language}} developer. Create code that is efficient, well-documented, and follows best practices.",
        description=f"Generate {language} code based on requirements",
        order=0,
        input_mapping={
            "language": language,
            "requirements": {"source": "input", "path": "requirements"}
        },
        output_mapping={
            "code": "response"
        }
    )
    
    # Create file step to save the code
    save_step = create_file_step(
        name="Save Code",
        operation="write",
        file_path=output_file_path,
        description=f"Save generated code to {output_file_path}",
        order=1,
        input_mapping={
            "content": {"source": "output", "path": "code"}
        }
    )
    
    # Return pipeline configuration
    return {
        "name": name,
        "description": description,
        "is_public": False,
        "tags": ["code-generation", language],
        "config": {
            "language": language,
            "output_file": output_file_path
        },
        "steps": [
            generate_step,
            save_step
        ]
    }


def create_code_review_pipeline(
    name: str,
    description: str,
    model_id: str,
    input_file_path: str,
    language: str
) -> Dict[str, Any]:
    """
    Create a code review pipeline.
    
    Args:
        name: Pipeline name
        description: Pipeline description
        model_id: ID of the model to use
        input_file_path: Path to code to review
        language: Programming language
        
    Returns:
        Dictionary with pipeline configuration
    """
    # Create file step to read the code
    read_step = create_file_step(
        name="Read Code",
        operation="read",
        file_path=input_file_path,
        description=f"Read code from {input_file_path}",
        order=0,
        output_mapping={
            "source_code": "content"
        }
    )
    
    # Create prompt step for review
    review_step = create_prompt_step(
        name="Review Code",
        model_id=model_id,
        prompt="Review the following {{language}} code:\n\n```{{language}}\n{{input.source_code}}\n```\n\nProvide feedback on code quality, potential bugs, and suggestions for improvement.",
        system_prompt="You are an expert code reviewer specializing in {{language}}. Analyze code for bugs, inefficiencies, and readability issues. Suggest concrete improvements and explain your reasoning.",
        description=f"Review {language} code",
        order=1,
        input_mapping={
            "language": language,
            "source_code": {"source": "output", "path": "source_code"}
        },
        output_mapping={
            "review": "response"
        },
        options={
            "temperature": 0.2  # Low temperature for more consistent reviews
        }
    )
    
    # Return pipeline configuration
    return {
        "name": name,
        "description": description,
        "is_public": False,
        "tags": ["code-review", language],
        "config": {
            "language": language,
            "input_file": input_file_path
        },
        "steps": [
            read_step,
            review_step
        ]
    }


def create_documentation_pipeline(
    name: str,
    description: str,
    model_id: str,
    input_file_path: str,
    output_file_path: str,
    language: str
) -> Dict[str, Any]:
    """
    Create a code documentation pipeline.
    
    Args:
        name: Pipeline name
        description: Pipeline description
        model_id: ID of the model to use
        input_file_path: Path to code to document
        output_file_path: Path to save documentation
        language: Programming language
        
    Returns:
        Dictionary with pipeline configuration
    """
    # Create file step to read the code
    read_step = create_file_step(
        name="Read Code",
        operation="read",
        file_path=input_file_path,
        description=f"Read code from {input_file_path}",
        order=0,
        output_mapping={
            "source_code": "content"
        }
    )
    
    # Create prompt step for documentation
    document_step = create_prompt_step(
        name="Generate Documentation",
        model_id=model_id,
        prompt="Create comprehensive documentation for the following {{language}} code:\n\n```{{language}}\n{{input.source_code}}\n```\n\nInclude function descriptions, parameter explanations, return values, and examples.",
        system_prompt="You are a technical documentation expert. Create clear, concise, and accurate documentation that follows best practices.",
        description=f"Generate documentation for {language} code",
        order=1,
        input_mapping={
            "language": language,
            "source_code": {"source": "output", "path": "source_code"}
        },
        output_mapping={
            "documentation": "response"
        }
    )
    
    # Create file step to save the documentation
    save_step = create_file_step(
        name="Save Documentation",
        operation="write",
        file_path=output_file_path,
        description=f"Save documentation to {output_file_path}",
        order=2,
        input_mapping={
            "content": {"source": "output", "path": "documentation"}
        }
    )
    
    # Return pipeline configuration
    return {
        "name": name,
        "description": description,
        "is_public": False,
        "tags": ["documentation", language],
        "config": {
            "language": language,
            "input_file": input_file_path,
            "output_file": output_file_path
        },
        "steps": [
            read_step,
            document_step,
            save_step
        ]
    }


def create_code_transformation_pipeline(
    name: str,
    description: str,
    model_id: str,
    input_file_path: str,
    output_file_path: str,
    source_language: str,
    target_language: str
) -> Dict[str, Any]:
    """
    Create a code transformation pipeline (e.g. JS to TS, Python to Rust).
    
    Args:
        name: Pipeline name
        description: Pipeline description
        model_id: ID of the model to use
        input_file_path: Path to source code
        output_file_path: Path to save transformed code
        source_language: Source programming language
        target_language: Target programming language
        
    Returns:
        Dictionary with pipeline configuration
    """
    # Create file step to read the source code
    read_step = create_file_step(
        name="Read Source Code",
        operation="read",
        file_path=input_file_path,
        description=f"Read {source_language} code from {input_file_path}",
        order=0,
        output_mapping={
            "source_code": "content"
        }
    )
    
    # Create prompt step for transformation
    transform_step = create_prompt_step(
        name="Transform Code",
        model_id=model_id,
        prompt="Transform the following {{source_language}} code to {{target_language}}:\n\n```{{source_language}}\n{{input.source_code}}\n```\n\nEnsure the transformed code is idiomatic and follows best practices for {{target_language}}.",
        system_prompt="You are an expert programmer skilled in multiple languages. Convert code between languages while preserving functionality and improving readability.",
        description=f"Transform {source_language} code to {target_language}",
        order=1,
        input_mapping={
            "source_language": source_language,
            "target_language": target_language,
            "source_code": {"source": "output", "path": "source_code"}
        },
        output_mapping={
            "transformed_code": "response"
        },
        options={
            "temperature": 0.2  # Lower temperature for more precise transformations
        }
    )
    
    # Create post-processing step to extract code blocks
    process_step = create_code_step(
        name="Extract Code",
        code="""import re

# Extract code blocks from the response
def extract_code(text):
    # Look for code blocks with or without language specifier
    pattern = r'```(?:\w+)?\n([\s\S]+?)\n```'
    matches = re.findall(pattern, text)
    
    if matches:
        # Return the largest code block (assuming it's the complete transformed code)
        return max(matches, key=len)
    else:
        # If no code blocks, return the original text
        return text

# Process the input
input_text = globals().get('transformed_code', '')
cleaned_code = extract_code(input_text)

# Return the result
print(cleaned_code)
""",
        language="python",
        description="Extract code blocks from the LLM response",
        order=2,
        input_mapping={
            "transformed_code": {"source": "output", "path": "transformed_code"}
        },
        output_mapping={
            "clean_code": "stdout"
        }
    )
    
    # Create file step to save the transformed code
    save_step = create_file_step(
        name="Save Transformed Code",
        operation="write",
        file_path=output_file_path,
        description=f"Save {target_language} code to {output_file_path}",
        order=3,
        input_mapping={
            "content": {"source": "output", "path": "clean_code"}
        }
    )
    
    # Return pipeline configuration
    return {
        "name": name,
        "description": description,
        "is_public": False,
        "tags": ["code-transformation", source_language, target_language],
        "config": {
            "source_language": source_language,
            "target_language": target_language,
            "input_file": input_file_path,
            "output_file": output_file_path
        },
        "steps": [
            read_step,
            transform_step,
            process_step,
            save_step
        ]
    }