# Module Interfaces

## Purpose

This document defines the expected inputs and outputs for the main modules in the Modula WMS Integration Agent.

---

## 1. FileIngestionModule

### Responsibility
Accepts customer files or API payloads and routes them to the correct parser.

### Input
```python
file_path: str
source_type: str
```

Supported `source_type` values:
- `csv`
- `xml`
- `json`
- `rest_api`

### Output
```python
ParsedSourceData
```

---

## 2. Parser Layer

### Responsibility
Converts external customer data into normalized internal models.

### Input
```python
file_path: str
```

or for two-file CSV order imports:

```python
header_file_path: str
line_file_path: str
```

### Output
```python
list[WMSItem]
list[WMSOrder]
```

---

## 3. Normalized Models

Current Pydantic models:

```python
WMSItem
WMSOrder
WMSOrderLine
```

These models are the internal standard format used across the application.

---

## 4. SchemaMapper

### Responsibility
Maps customer ERP fields to normalized internal fields and WMS XML fields.

### Input
```python
source_fields: list[str]
target_fields: list[str]
```

### Output
```python
MappingSuggestion
```

Example:

```json
{
  "source_field": "product_sku",
  "internal_field": "item_code",
  "wms_field": "RIG_ARTICOLO",
  "confidence": 0.96
}
```

---

## 5. LLMClient

### Responsibility
Uses OpenAI to suggest mappings for unknown customer field names.

### Input
```python
source_fields: list[str]
known_wms_fields: list[str]
sample_rows: list[dict]
```

### Output
```json
{
  "mappings": [
    {
      "source_field": "ordered_qty",
      "suggested_wms_field": "RIG_QTAR",
      "confidence": 0.94
    }
  ]
}
```

---

## 6. Human Confirmation Module

### Responsibility
Allows a user to approve or override suggested mappings.

### Input
```python
mapping_suggestions: list[MappingSuggestion]
```

### Output
```python
confirmed_mapping: dict[str, str]
```

---

## 7. Transformer / CodeGenerator

### Responsibility
Converts normalized models into Modula WMS XML output.

### Input
```python
orders: list[WMSOrder]
items: list[WMSItem]
```

### Output
```python
output_file_path: str
```

---

## 8. Validator

### Responsibility
Checks that required fields exist and values are valid.

### Input
```python
orders: list[WMSOrder]
items: list[WMSItem]
```

### Output
```python
list[str]
```

Example:

```python
[
    "Order SO1001 line 2: quantity must be greater than 0"
]
```

---

## Current Architecture Rule

All source data must be converted into normalized Pydantic models before transformation.

```text
External Source
    ↓
Parser
    ↓
Pydantic Model
    ↓
Validator
    ↓
Transformer
    ↓
WMS XML
```