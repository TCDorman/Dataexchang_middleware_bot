# Modula WMS / ERP Integration Agent

This project generates file-based integrations between customer ERP exports and Modula WMS import formats.

## Phase 1 Goal

Given a sample CSV, XML, or JSON file, the agent will:

1. Parse the file structure
2. Suggest Modula WMS field mappings
3. Accept user confirmation
4. Generate a transformation script
5. Validate the transformed output