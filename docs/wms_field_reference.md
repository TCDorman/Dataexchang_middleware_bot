# Modula WMS Field Reference

---

# Item Import Format

## Root Node
```xml
<MODULA_WMS>
```

## Entity
```xml
<IMP_ARTICOLI>
```

## Fields

| Field | Description | Example | Required |
|---|---|---|---|
| ART_ARTICOLO | Item code / SKU | ITEM001 | Yes |
| ART_DES | Item description | ITEM001 Description | Yes |

## Example

```xml
<MODULA_WMS>
    <IMP_ARTICOLI>
        <ART_ARTICOLO>ITEM001</ART_ARTICOLO>
        <ART_DES>ITEM001 Description</ART_DES>
    </IMP_ARTICOLI>
</MODULA_WMS>
```

---

# Order Import Format

## Root Node
```xml
<SYSTORE>
```

## Order Header Entity
```xml
<IMP_ORDINI>
```

## Order Line Entity
```xml
<IMP_ORDINI_RIGHE>
```

---

# Order Header Fields

| Field | Description | Example | Required |
|---|---|---|---|
| ORD_ORDINE | Order number | ORDER11 | Yes |
| ORD_DES | Order description | ORDER 11 | Yes |
| ORD_TIPOOP | Operation type | P | Yes |

---

# Order Line Fields

| Field | Description | Example | Required |
|---|---|---|---|
| RIG_ORDINE | Order number reference | ORDER11 | Yes |
| RIG_ARTICOLO | Item code | ITEM01 | Yes |
| RIG_QTAR | Requested quantity | 2 | Yes |
| RIG_SUB1 | Sub field 1 | NULL | No |
| RIG_SUB2 | Sub field 2 | NULL | No |
| RIG_STAMATE | Unknown/optional | NULL | No |
| RIG_TIPOCONF | Configuration type | NULL | No |
| RIG_HOSTINF | Host info | NULL | No |
| RIG_REQ_NOTE | Request notes | NULL | No |
| RIG_NOTE_STAMPA | Print notes | NULL | No |
| RIG_HOSTCAUS | Host cause | NULL | No |
| RIG_HOSTRIF | Host reference | NULL | No |

---

# Notes

- Orders contain multiple line items
- `IMP_ORDINI` acts as the order header
- `IMP_ORDINI_RIGHE` contains order details
- Empty XML tags represent optional fields
- `ORD_TIPOOP = P` likely indicates Picking operation

# Parsing Considerations

## Items
- Flat structure
- One XML node per item
- Minimal nesting

## Orders
- Nested structure
- Header/detail relationship
- Multiple order lines per order
- Requires hierarchical parsing