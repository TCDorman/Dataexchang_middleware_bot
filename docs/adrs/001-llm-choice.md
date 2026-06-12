# ADR 001: LLM Choice

## Status
Accepted

## Context
The integration agent needs an LLM to suggest mappings between unknown customer ERP fields and known Modula WMS fields.

Example:

```text
client_order_ref → ORD_ORDINE
material_code → RIG_ARTICOLO
requested_quantity → RIG_QTAR