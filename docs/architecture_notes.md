# Architecture Notes

## Phase 1 Architecture

The Phase 1 integration agent uses a file-based pipeline for CSV and XML files.

## Current Pipeline

```text
Raw Customer/WMS File
        ↓
Parser
        ↓
Normalized Pydantic Model
        ↓
Validator
        ↓
JSON Export / XML Transformer
        ↓
WMS-Compatible Output