"""Connect a local MCP client, discover tools and read one change; no model."""

import argparse
import asyncio
import json

from enterprise_api import ClientConfig, Scope
from mcp_server.client import connect


async def probe(origin, change_id):
    async with connect(origin + "/mcp") as client:
        tools = await client.list_tools()
        result = await client.call_tool("get_change_request", {"change_id": change_id})
        payload = result.structured_content
        print(json.dumps({"tool_count": len(tools.tools), "tools": [t.name for t in tools.tools],
                          "ok": payload["ok"], "record_id": payload["data"]["id"] if payload["ok"] else None,
                          "error": payload["error"], "trace": result.meta["stratos/trace"]}, indent=2))
        return 0 if payload["ok"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:9000")
    parser.add_argument("--change-id", default="CR-017")
    args = parser.parse_args()
    try:
        origin = ClientConfig(base_url=args.origin, scope=Scope(program_id="PRG-A17", customer_id="CUST-FML01")).base_url
        return asyncio.run(probe(origin, args.change_id))
    except Exception:
        print('{"ok":false,"error":{"code":"LOCAL_MCP_PROBE_FAILED"}}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
