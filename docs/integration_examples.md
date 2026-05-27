# Integration Examples

## Example 1 — Item Import

File: `CFG-IMP-ARTICOLI.xml`

Purpose:
Imports inventory/item master data into Modula WMS.

Key Fields:
- ART_ARTICOLO
- ART_DES

Structure Type:
Flat XML structure.

---

## Example 2 — Order Import

File: `CFG-IMP-ORDINI.xml`

Purpose:
Imports customer picking orders into Modula WMS.

Key Fields:
- ORD_ORDINE
- RIG_ARTICOLO
- RIG_QTAR

Structure Type:
Hierarchical XML structure.

---

## Example 3 — Order Export

File: `CFG-EXP-ORDINI.xml`

Purpose:
Exports executed warehouse operations from Modula WMS.

Key Fields:
- ORD_ATTR1
- RIG_ATTR1
- RIG_QTAE

Structure Type:
Hierarchical XML export structure.