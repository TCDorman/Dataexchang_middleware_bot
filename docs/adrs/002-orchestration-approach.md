# ADR 002: Orchestration Approach

## Status
Accepted

## Context
The integration agent requires orchestration between:
- parsers
- mapping logic
- validators
- transformers
- formatting scripts
- future UI components

A decision was required between:
- autonomous agent frameworks
- LangChain orchestration
- direct Python module orchestration

## Decision
Use direct Python module orchestration for Phase 1.

## Rationale
- Simpler debugging
- Lower architectural complexity
- Easier testing
- Better deterministic control
- Existing workflows are mostly sequential and rule-based
- Reduces dependency overhead

Current orchestration flow:

```text
Input Source
    ↓
Parser
    ↓
Normalized Pydantic Models
    ↓
LLM Mapping Suggestions
    ↓
Human Confirmation
    ↓
Transformer
    ↓
Formatter
    ↓
Validator
    ↓
WMS XML Output