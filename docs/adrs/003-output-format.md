# ADR 003: Output Format

## Status
Accepted

## Context
The integration agent must generate files compatible with the Modula WMS import/export process.

The Modula WMS environment currently expects:
- XML files
- specific tag structures
- import/export schema formatting
- consistent indentation/readability

## Decision
Use Modula-compatible XML as the primary output format.

Example root structures:
- MODULA_WMS
- SYSTORE

Primary supported outputs:
- IMP_ARTICOLI
- IMP_ORDINI
- EXP_ORDINI

## Rationale
- Matches existing Modula integration workflows
- Compatible with customer WMS imports
- Easier validation against existing examples
- Human-readable and auditable
- Easily generated using Python XML libraries

## Current Output Pipeline

```text
Customer Data
    ↓
Parser
    ↓
Normalized Models
    ↓
Transformer
    ↓
XML Formatter
    ↓
Formatted WMS XML