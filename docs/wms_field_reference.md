# Modula WMS Field Reference

## Item Import: `CFG-IMP-ARTICOLI.xml`

Root node: `MODULA_WMS`  
Entity node: `IMP_ARTICOLI`

| WMS Field | Internal Field | Description | Required |
|---|---|---|---|
| ART_ARTICOLO | item_code | Item/SKU code | Yes |
| ART_DES | description | Item description | No |

---

## Order Import: `CFG-IMP-ORDINI.xml`

Root node: `SYSTORE`  
Header node: `IMP_ORDINI`  
Line node: `IMP_ORDINI_RIGHE`

### Header Fields

| WMS Field | Internal Field | Description | Required |
|---|---|---|---|
| ORD_ORDINE | order_number | Order number | Yes |
| ORD_DES | description | Order description | No |
| ORD_TIPOOP | operation_type | Operation type, example: P | Yes |

### Line Fields

| WMS Field | Internal Field | Description | Required |
|---|---|---|---|
| RIG_ORDINE | order_number | Order number reference | Yes |
| RIG_ARTICOLO | item_code | Item/SKU code | Yes |
| RIG_QTAR | quantity | Requested quantity | Yes |
| RIG_SUB1 | sub1 | Optional sub field | No |
| RIG_SUB2 | sub2 | Optional sub field | No |

---

## Order Export: `CFG-EXP-ORDINI.xml`

Root node: `SYSTORE`  
Header node: `EXP_ORDINI`  
Line node: `EXP_ORDINI_RIGHE`

### Header Fields

| WMS Field | Internal Field | Description | Required |
|---|---|---|---|
| ORD_ORDINE | order_number | Order number | Yes |
| ORD_TIPOOP | operation_type | Operation type | Yes |
| ORD_ATTR1 | warehouse_number | Warehouse number or warehouse reference | No |
| ORD_ELEBAIE | bay_number | Bay number | No |

### Line Fields

| WMS Field | Internal Field | Description | Required |
|---|---|---|---|
| RIG_ORDINE | order_number | Order number reference | Yes |
| RIG_ARTICOLO | item_code | Item/SKU code | Yes |
| RIG_SUB1 | sub1 | Batch or sub field | No |
| RIG_ATTR1 | warehouse_task | Warehouse task | No |
| RIG_ATTR2 | source_bin | Source storage bin | No |
| RIG_ATTR3 | destination_bin | Destination storage bin | No |
| RIG_QTAE | quantity | Executed/exported quantity | Yes |