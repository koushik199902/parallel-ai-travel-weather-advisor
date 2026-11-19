"""Independent local MCP weather server, stdio transport."""
from mcp.server.fastmcp import FastMCP
from travel_agent.weather import get_city_weather

mcp = FastMCP("Travel Weather MCP")

@mcp.tool()
async def get_weather(city: str, date: str) -> dict:
    """Retrieve live Open-Meteo daily forecast for an approved Indian city and ISO date."""
    return await get_city_weather(city, date)

@mcp.resource("weather://about")
def about() -> str:
    return "Travel Weather MCP exposes get_weather(city, date) for four Indian cities."

@mcp.prompt()
def travel_brief(city: str) -> str:
    return f"Summarize travel conditions for {city} using measured weather data only."

if __name__ == "__main__":
    mcp.run(transport="stdio")
