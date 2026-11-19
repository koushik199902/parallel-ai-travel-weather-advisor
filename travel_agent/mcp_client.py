"""Real MCP subprocess connection: dynamic discovery and tool invocation."""
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def extract_result(result):
    if result.isError:
        raise RuntimeError("MCP tool reported error: " + str(result.content))
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        if isinstance(structured, dict) and "result" in structured and isinstance(structured["result"], dict):
            return structured["result"]
        return structured
    for block in result.content:
        if getattr(block, "type", "") == "text":
            obj = json.loads(block.text)
            if isinstance(obj, dict):
                return obj
    raise RuntimeError("MCP tool returned no usable JSON object")


async def fetch_via_mcp(city: str, date: str):
    env = dict(os.environ)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "travel_agent.mcp_server"],
        env=env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            listing = await client.list_tools()
            names = [t.name for t in listing.tools]
            if "get_weather" not in names:
                raise RuntimeError("get_weather MCP tool was not discovered")
            result = await client.call_tool("get_weather", {"city": city, "date": date})
            data = extract_result(result)
            if not isinstance(data, dict) or data.get("city") != city or data.get("date") != date:
                raise RuntimeError("MCP returned an unexpected city or date")
            return data, names
