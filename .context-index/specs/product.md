# Product Vision: mock-salesforce

## Vision

A standalone, offline mock of a Salesforce-shaped CRM — pipeline kanban UI, CRUD API, and MCP
layer — that other adev-course tracks integrate against as a realistic external dependency.

## Module Map

| Module | Description | Charter |
|--------|-------------|---------|
| crm-api | Provide a Salesforce-shaped CRM domain (accounts, contacts, opportunities) backed by a local SQLite database, exposed over an HTTP CRUD API. | [charter.md](./features/crm-api/charter.md) |
| crm-ui | Gives mock-salesforce a Salesforce-like pipeline kanban board and deal detail page web interface — opportunities as cards in stage columns, full CRUD via forms — as a pure client of crm-api. | [charter.md](./features/crm-ui/charter.md) |
| mcp-server | Exposes crm-api's CRUD operations as MCP tools so an AI agent can create/read/update/delete Accounts, Contacts, and Opportunities through the Model Context Protocol. | [charter.md](./features/mcp-server/charter.md) |
