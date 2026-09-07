class McpUpstreamError(Exception):
    """A crm-api HTTP call returned a 4xx/5xx response. Carries the upstream
    error code/message verbatim so tool callers see it unchanged (never
    swallowed or rewritten — see the mcp-server charter's Invariants)."""

    def __init__(self, status_code: int, error_code: str | None, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class McpUpstreamUnreachableError(Exception):
    """crm-api could not be reached at all (connection refused, DNS failure,
    timeout) — raised instead of letting a raw httpx exception surface."""
