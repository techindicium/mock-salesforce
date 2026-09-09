# mock-salesforce

A standalone mock of a Salesforce-shaped CRM API — accounts, contacts, opportunities — for the
adev course tracks to consume as an external system dependency.

Independent repo: no dependency on `course-shared`, the other `mock-*` repos, or any track repo.
Tracks that need it (see `adev-workspace.yaml` at the workspace root for which ones) pull it in
as a service dependency; this repo never depends on them back.

Not yet scoped. Run `/adev:brainstorm` here to charter what the mock API surface needs to cover
before implementing it.

## Running with Docker

The whole stack (`crm-api` and `mcp-server`) is packaged with Docker Compose. From a clean
checkout, one command brings up a fully working stack:

```bash
docker compose up
```

This builds exactly two images — `crm-api` (which also bundles `crm-ui`'s built static assets,
so it serves the UI itself) and `mcp-server` — and starts them in dependency order: `crm-api`
must report healthy before `mcp-server` starts, since `mcp-server` talks to it over the internal
Docker network.

**Ports:**

- `crm-api` is published at `http://localhost:8020`. Override the host port with `PORT=<port>`.
- `mcp-server` is published at `http://localhost:8021`. Override the host port with
  `MCP_PORT=<port>`.
- Neither port is exposed beyond `localhost` by default.

```bash
PORT=9000 MCP_PORT=9001 docker compose up
```

**Data:** the SQLite database lives in the named volume `mock_salesforce_db` and survives
`docker compose down` (without `-v`) — only `docker compose down -v` wipes it.

**Health and logs:**

```bash
docker compose ps                        # check container health
curl http://localhost:8020/health        # or probe crm-api directly
docker compose logs -f                   # combined, live logs from both services
```

**Teardown:**

```bash
docker compose down       # stop containers, keep data
docker compose down -v    # stop containers and wipe the named volume
```
