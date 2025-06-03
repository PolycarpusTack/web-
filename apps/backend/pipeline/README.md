# Code Factory Pipeline Module

The Pipeline module provides a powerful and flexible system for creating and executing multi-step pipelines for code generation, transformation, and analysis. This enables users to build sequences of operations that transform inputs into useful outputs, such as code, documentation, or formatted data.

## Features

- Create and manage sophisticated pipeline configurations
- Execute pipelines with various specialized step types
- Track pipeline executions, results, and performance metrics
- Reuse pipeline templates for common tasks
- Validate inputs and handle errors gracefully
- Support for complex data transformations

## Pipeline Architecture

### Components

1. **Pipeline Model** - A pipeline is a sequence of steps with configuration and metadata.
2. **Step Model** - Each step represents a single operation in the pipeline.
3. **Execution Model** - Records of pipeline executions with inputs, outputs, and metrics.
4. **Pipeline Engine** - Executes the steps and manages the pipeline state.

### Step Types

- **Prompt** - Send prompts to LLMs and process responses
- **Code** - Execute code snippets
- **File** - Read or write files
- **API** - Make HTTP requests to external services
- **Condition** - Evaluate conditions for flow control
- **Transform** - Transform data between formats

## Usage

### Creating a Pipeline

```python
from db.database import get_db
from db.pipeline_crud import create_pipeline, create_pipeline_step
from db.pipeline_models import PipelineStepType

async def create_code_gen_pipeline(user_id):
    # Create the pipeline
    pipeline = await create_pipeline(
        db=next(get_db()),
        user_id=user_id,
        name="TypeScript Code Generator",
        description="Generates TypeScript code from requirements"
    )
    
    # Create steps
    prompt_step = await create_pipeline_step(
        db=next(get_db()),
        pipeline_id=pipeline.id,
        name="Generate Code",
        step_type=PipelineStepType.PROMPT.value,
        order=0,
        config={
            "model_id": "gpt-4-turbo",
            "prompt": "Generate TypeScript code to implement the following:\n\n{{input.requirements}}",
            "system_prompt": "You are an expert TypeScript developer."
        }
    )
    
    file_step = await create_pipeline_step(
        db=next(get_db()),
        pipeline_id=pipeline.id,
        name="Save Code",
        step_type=PipelineStepType.FILE.value,
        order=1,
        config={
            "operation": "write",
            "file_path": "{{input.output_path}}"
        },
        input_mapping={
            "content": {"source": "output", "path": "Generate Code.response"}
        }
    )
    
    return pipeline
```

### Executing a Pipeline

```python
from db.database import get_db
from pipeline.engine import PipelineEngine

async def execute_pipeline(pipeline_id, user_id, requirements, output_path):
    # Create engine
    engine = PipelineEngine(next(get_db()))
    
    # Execute pipeline
    execution = await engine.execute_pipeline(
        pipeline_id=pipeline_id,
        user_id=user_id,
        input_parameters={
            "requirements": requirements,
            "output_path": output_path
        }
    )
    
    return execution
```

### Using Pipeline Templates

```python
from db.database import get_db
from db.pipeline_crud import create_pipeline, create_pipeline_step
from pipeline.templates import create_code_generation_pipeline

async def create_pipeline_from_template(user_id):
    # Get template
    template = create_code_generation_pipeline(
        name="Python Code Generator",
        description="Generates Python code from requirements",
        model_id="mistral:7b-instruct",
        output_file_path="/tmp/generated_code.py",
        language="python"
    )
    
    # Create pipeline
    pipeline = await create_pipeline(
        db=next(get_db()),
        user_id=user_id,
        name=template["name"],
        description=template["description"],
        is_public=template["is_public"],
        tags=template["tags"],
        config=template["config"]
    )
    
    # Create steps
    for i, step_config in enumerate(template["steps"]):
        await create_pipeline_step(
            db=next(get_db()),
            pipeline_id=pipeline.id,
            name=step_config["name"],
            step_type=step_config["type"],
            order=step_config["order"],
            config=step_config["config"],
            description=step_config["description"],
            input_mapping=step_config["input_mapping"],
            output_mapping=step_config["output_mapping"]
        )
    
    return pipeline
```

## Extending the System

### Adding New Step Types

1. Add a new type to the `PipelineStepType` enum in `db/pipeline_models.py`
2. Implement a handler function in the `PipelineEngine` class in `pipeline/engine.py`
3. Register the handler in the `_register_default_handlers` method

### Creating Custom Templates

Create helper functions in `pipeline/templates.py` for your specific pipeline templates.

## API Endpoints

- `GET /api/pipelines` - List pipelines
- `POST /api/pipelines` - Create a pipeline
- `GET /api/pipelines/{id}` - Get a pipeline
- `PUT /api/pipelines/{id}` - Update a pipeline
- `DELETE /api/pipelines/{id}` - Delete a pipeline
- `POST /api/pipelines/{id}/execute` - Execute a pipeline
- `GET /api/pipelines/executions` - List executions
- `GET /api/pipelines/executions/{id}` - Get execution details

See the API documentation for full details.