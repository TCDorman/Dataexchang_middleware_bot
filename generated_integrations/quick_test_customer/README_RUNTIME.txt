MODULA MIDDLEWARE RUNTIME

Customer:
Quick Test Customer

Purpose:
This package runs a local always-on middleware runtime.

How to use:

1. Put customer CSV files into:

   runtime\customer_input

2. Start the runtime by double-clicking:

   start_runtime.bat

3. Converted Modula WMS XML files will appear in:

   runtime\modula_output

4. Successfully processed files move to:

   runtime\processed

5. Failed files move to:

   runtime\errors

6. Saved mapping profiles are stored in:

   runtime\profiles

Output Format:
Modula WMS XML using SYSTORE / IMP_ORDINI / IMP_ORDINI_RIGHE.

Mapping:
The first time a new customer file format is processed, the runtime asks the AI
to suggest field mappings and then asks the user to confirm them.

After confirmation, the mapping is saved and reused automatically for future files.

Required CSV fields can vary by customer, but the runtime maps them to:

- order_id
- customer_name
- item
- quantity

Example input CSV:

ORDER_NUMBER,CUSTOMER,PART_NUMBER,ORDER_QTY
ORDER11,ORDER 11,ITEM01,2
ORDER11,ORDER 11,ITEM02,2
ORDER12,ORDER 12,ITEM03,2

Expected XML output will be written to:

runtime\modula_output