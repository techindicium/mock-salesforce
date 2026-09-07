import os

import httpx

from mcp_server.errors import McpUpstreamError, McpUpstreamUnreachableError


class CrmApiClient:
    """Thin synchronous wrapper around crm-api's HTTP surface. Every MCP tool
    goes through this so BEH-9 and the verbatim-passthrough rule are
    satisfied in exactly one place, never reimplemented per tool."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        # A default (rather than a bare os.environ["API_BASE_URL"] subscript)
        # is deliberate: mcp_server/app.py builds a module-level `client =
        # CrmApiClient()` at import time, and every test in this plan imports
        # mcp_server.app. A missing env var must not raise KeyError during
        # pytest collection and take down the whole `python3 -m pytest -q`
        # gate — mirrors src/mock_salesforce/db.py's
        # os.environ.get("DB_PATH", "mock_salesforce.db") default pattern.
        self.base_url = (
            base_url or os.environ.get("API_BASE_URL", "http://localhost:8000")
        ).rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, transport=transport)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict | list | None:
        try:
            resp = self._client.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            raise McpUpstreamUnreachableError(
                f"Cannot reach crm-api at {self.base_url}: {exc}"
            ) from exc
        if resp.status_code >= 400:
            body = resp.json() if resp.content else {}
            raise McpUpstreamError(
                resp.status_code, body.get("error"), body.get("message", resp.text)
            )
        return resp.json() if resp.content else None

    def close(self) -> None:
        self._client.close()
