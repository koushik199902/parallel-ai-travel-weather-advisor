import argparse
import asyncio
import json
import os
from travel_agent.graph import run

DEFAULT = ("Compare the weather in Bengaluru, Chennai, Hyderabad, and Mumbai for tomorrow. "
           "Analyze temperature, rainfall, and wind conditions, and recommend the best city for outdoor activities.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--question", default=DEFAULT)
    p.add_argument("--demo", action="store_true", help="Simulated data and analysis; NO MCP or Ollama")
    args = p.parse_args()
    if args.demo:
        os.environ["WEATHER_DEMO_MODE"] = "1"
    result = asyncio.run(run(args.question))
    print(result.get("answer", ""))
    print("\nExecution trace:\n" + json.dumps(result.get("events", []), indent=2))
