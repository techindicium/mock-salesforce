import os

from mcp.server.fastmcp import FastMCP

from mcp_server.client import CrmApiClient

mcp = FastMCP("mock-salesforce-crm", port=int(os.environ.get("PORT", "8000")))
client = CrmApiClient()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
