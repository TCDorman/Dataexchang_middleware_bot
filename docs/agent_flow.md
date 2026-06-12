# Modula Integration Agent Flow

## High-Level Workflow

Customer File/API
↓
Parser Layer
↓
Normalized Internal Models
↓
LLM Mapping Agent
↓
User Mapping Confirmation
↓
Transformer Layer
↓
WMS XML Output
↓
Validation Layer
↓
Deployment Package

## Supported Input Types
- CSV
- XML
- JSON
- REST API

## Internal Models
- WMSItem
- WMSOrder
- WMSOrderLine

## Output Formats
- Modula WMS XML