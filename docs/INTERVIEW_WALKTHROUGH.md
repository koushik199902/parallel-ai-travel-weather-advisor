# Architecture & Interview Walkthrough

## 60-second introduction

> I built a local, parallel multi-agent travel-weather advisor. LangGraph dynamically fans out city-weather tasks using `Send`; each worker connects to a custom MCP server using stdio and retrieves an Open-Meteo forecast. After gathering the results, two separate Ollama-powered specialists analyze rain and comfort concurrently. A deterministic reviewer ranks the cities with an explicitly subjective demo heuristic, then a response agent explains the winner. The project has a Streamlit interface, trace output, simulated offline rehearsal, and automated tests.

## Trace a request through the code

| Stage | Source | What happens |
| --- | --- | --- |
| User input | `app.py` | User enters a question and clicks Run |
| Input planning | `travel_agent/decision.py` `plan_request` | Deterministically extracts named supported cities and today/tomorrow |
| Graph orchestration | `travel_agent/graph.py` `build_graph` | Registers nodes and edges |
| Worker fan-out | `travel_agent/graph.py` `dispatch` | Creates a `Send` for each city |
| MCP invocation | `travel_agent/mcp_client.py` `fetch_via_mcp` | `initialize`, `list_tools`, `call_tool` |
| MCP server | `travel_agent/mcp_server.py` `get_weather` | Exposes an asynchronous tool |
| Forecast | `travel_agent/weather.py` `get_city_weather` | Fetches Open-Meteo daily forecast using known city coordinates |
| Merge | `travel_agent/graph.py` `TravelState`, `gather` | Accumulates worker outputs with reducers; ranks successful cities |
| Parallel specialists | `travel_agent/graph.py` `rain_agent`, `comfort_agent` | Two separately prompted asynchronous Ollama requests |
| Validation | `travel_agent/graph.py` `reviewer` | Requires both analyses and a ranking |
| Recommendation | `travel_agent/decision.py` `score_weather` | 45/35/20 subjective rain/temp/wind weighting |
| Final response | `travel_agent/graph.py` `response_agent` | Explains deterministic winning city |
| Debugging | `app.py` | Displays trace and complete shared state |

## Technical distinctions worth stating

- **Parallel workers ≠ four autonomous LLM agents.** The four city tasks are concurrent MCP clients. Rain and Comfort are separately prompted LLM specialist nodes.
- **Planner is deterministic**, not an LLM-powered planner. It supports only four named cities and today/tomorrow.
- **MCP** is used for standardized client/server tool communication, not for Ollama inference. The MCP server also exposes a resource and a prompt but the workflow consumes its `get_weather` tool.
- **Two stages of graph parallelism:** four city workers first, then two analysis nodes. Joining the branches ensures review runs after both analyses finish.
- **Simulated mode is fictional**, not proof of MCP or live forecasts. Test MCP separately using `test_mcp.py` and run with simulation unchecked to demonstrate the complete external flow.
- **No measured performance improvements are claimed.** Parallel scheduling does not guarantee a faster response on every local model or machine.
- **No production guarantees.** There is no persistent checkpointer, retry/backoff, activity-specific risk model, official severe weather warning feed, or production authentication.

## 5-minute demonstration

1. Open `assets/workflow.gif` in the GitHub README to explain the workflow.
2. Open `travel_agent/graph.py` and show `TravelState`, `dispatch`, and `build_graph`.
3. Open `travel_agent/mcp_client.py` and show `client.call_tool`.
4. Run `python test_mcp.py` to verify actual MCP protocol communication with simulated tool data.
5. Run `python -m streamlit run app.py`, with simulated mode **off**, and submit the four-city question.
6. Expand execution trace and discuss independent weather-worker events, the two Ollama analyses, and the deterministic scoring.
7. Explain limitations and improvements honestly.

## Interview talking points

**Why LangGraph?** It makes execution order, parallel branching, joins and shared state explicit and testable.

**Why MCP?** Weather tool schemas and execution are exposed by a separate server, decoupling tool access from the graph.

**How is state merged?** `Annotated[list[dict], operator.add]` accumulates concurrent weather, analysis and trace updates.

**How is tool safety handled?** The client checks that `get_weather` is exposed, validates the returned city and date, and the service supports only a known set of cities and dates.

**How do you prevent unsupported claims?** Measured weather comes from Open-Meteo. The score is deterministic and explicitly described as a subjective demo heuristic; the LLM generates narrative only.
