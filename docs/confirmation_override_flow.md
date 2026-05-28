# Confirmation / Override Flow

## Purpose

The Modula WMS Integration Agent uses AI to suggest field mappings between customer ERP systems and Modula WMS XML fields.

Because AI suggestions may not always be correct, all mappings must be reviewed and confirmed by a human user before deployment.

---

# Workflow

```text
Customer File/API
        ↓
Parser Layer
        ↓
Detected Source Fields
        ↓
LLM Mapping Suggestions
        ↓
Human Review Screen
        ↓
Approved / Corrected Mapping
        ↓
Saved Mapping Configuration
        ↓
Transformation + XML Generation
```

---

# Example Mapping Suggestion

## AI Suggested Mapping

| Source Field | Suggested WMS Field | Confidence |
|---|---|---|
| client_order_ref | ORD_ORDINE | 0.98 |
| material_code | RIG_ARTICOLO | 0.96 |
| requested_quantity | RIG_QTAR | 0.94 |

---

# Human Override Example

User changes:

```text
material_code
```

from:

```text
RIG_ARTICOLO
```

to:

```text
ART_ARTICOLO
```

The confirmed mapping is then saved as the final configuration.

---

# Benefits

- Prevents incorrect automated mappings
- Allows customer-specific customizations
- Supports auditability
- Improves trust in AI-generated integrations
- Enables reusable mapping configurations

---

# Future Enhancement

Confirmed mappings may later be stored in:

```text
configs/mappings/
```

Example:

```json
{
    "client_order_ref": "ORD_ORDINE",
    "material_code": "RIG_ARTICOLO",
    "requested_quantity": "RIG_QTAR"
}
```

This allows the agent to reuse mappings for future imports from the same ERP source.