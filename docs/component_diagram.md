# Modula WMS Integration Agent — Component Diagram

```mermaid
flowchart TD

    A[Customer Input<br/>CSV / XML / JSON / REST API]
        --> B[FileIngestionModule]

    B --> C[Parser Layer]

    C --> D[Normalized Pydantic Models<br/>WMSItem / WMSOrder / WMSOrderLine]

    D --> E[SchemaMapper]

    E --> F[LLMClient<br/>OpenAI Mapping Suggestions]

    F --> G[Human Confirmation / Override]

    G --> H[Confirmed Mapping Configuration]

    H --> I[Transformer / CodeGenerator]

    I --> J[Validator]

    J --> K[Modula WMS XML Output]

    J --> L[Validation Errors]

    L --> G
```

## Architecture Notes

### FileIngestionModule
Responsible for:
- accepting uploaded files
- detecting file types
- routing to appropriate parsers

### Parser Layer
Converts external formats into normalized internal models.

Supported formats:
- CSV
- XML
- JSON
- REST API responses

### SchemaMapper
Determines how customer ERP fields map to Modula WMS fields.

### LLMClient
Uses OpenAI API to suggest field mappings and confidence scores.

### Human Confirmation / Override
Allows users to:
- approve mappings
- reject mappings
- manually correct mappings

### Transformer / CodeGenerator
Generates Modula-compatible XML output files.

### Validator
Checks:
- required fields
- data types
- XML structure
- mapping completeness