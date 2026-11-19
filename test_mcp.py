"""Actual stdio MCP discovery/invocation; deterministic mock weather (not internet)."""
import asyncio
import os
from travel_agent.mcp_client import fetch_via_mcp
from travel_agent.weather import india_date

async def main():
    os.environ["WEATHER_MCP_TEST_MODE"] = "1"
    value, names = await fetch_via_mcp("Bengaluru", india_date(1))
    assert "get_weather" in names
    assert value["city"] == "Bengaluru"
    assert "SIMULATED" in value["source"]
    print("MCP stdio discovery and tool invocation PASSED:", value)

if __name__ == "__main__":
    asyncio.run(main())
