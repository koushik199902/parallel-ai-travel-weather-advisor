"""Two-stage parallel LangGraph workflow: city workers, then analysis agents."""
import json
import os
import operator
import time
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from .decision import plan_request, rank_results
from .weather import simulated_weather
from .mcp_client import fetch_via_mcp
from .llm import complete
from .skills import read_skill


class TravelState(TypedDict, total=False):
    question: str
    plan: dict
    weather_results: Annotated[list[dict], operator.add]
    analyses: Annotated[list[dict], operator.add]
    events: Annotated[list[dict], operator.add]
    ranking: list[dict]
    answer: str
    warning: str
    error: str


class WorkerInput(TypedDict):
    city: str
    date: str


async def planner(state: TravelState):
    started = time.perf_counter()
    try:
        plan = plan_request(state["question"])
        return {"plan": plan, "events": [{"step": "planner", "plan": plan, "ms": round((time.perf_counter()-started)*1000)}]}
    except Exception as exc:
        return {"error": str(exc), "events": [{"step": "planner_failed", "error": str(exc)}]}


def dispatch(state: TravelState):
    if state.get("error"):
        return "error_handler"
    return [Send("weather_worker", {"city": city, "date": state["plan"]["date"]})
            for city in state["plan"]["cities"]]


async def weather_worker(state: WorkerInput):
    city, date = state["city"], state["date"]
    started = time.perf_counter()
    try:
        if os.getenv("WEATHER_DEMO_MODE") == "1":
            data, discovered = simulated_weather(city, date), ["get_weather"]
            transport = "SIMULATED — NO MCP CONNECTION"
        else:
            data, discovered = await fetch_via_mcp(city, date)
            transport = "MCP stdio"
        result = {"city": city, "status": "ok", "data": data}
        detail = {"step": "weather_worker", "city": city, "status": "ok",
                  "transport": transport, "mcp_tools": discovered,
                  "tool": "get_weather", "ms": round((time.perf_counter()-started)*1000)}
    except Exception as exc:
        result = {"city": city, "status": "error", "error": str(exc)}
        detail = {"step": "weather_worker", "city": city, "status": "error",
                  "error": str(exc), "ms": round((time.perf_counter()-started)*1000)}
    return {"weather_results": [result], "events": [detail]}


def gather(state: TravelState):
    successes = [x for x in state.get("weather_results", []) if x.get("status") == "ok"]
    failures = [x["city"] for x in state.get("weather_results", []) if x.get("status") != "ok"]
    if not successes:
        return {"error": "No city weather results were available",
                "events": [{"step": "gather", "ok": 0, "failed": failures}]}
    return {"ranking": rank_results(successes),
            "warning": ("Unavailable cities excluded: " + ", ".join(failures)) if failures else "",
            "events": [{"step": "gather", "ok": len(successes), "failed": failures}]}


def after_gather(state: TravelState):
    return "error_handler" if state.get("error") else "fanout_analysis"


def fanout_analysis(state: TravelState):
    return {"events": [{"step": "fanout_analysis", "agents": ["rain_agent", "comfort_agent"]}]}


async def rain_agent(state: TravelState):
    measured = [x["data"] for x in state["weather_results"] if x["status"] == "ok"]
    started = time.perf_counter()
    try:
        output = await complete(
            "You are a rainfall analysis specialist. " + read_skill(),
            "Explain the reported daily maximum precipitation probabilities and total precipitation. "
            "Do not invent numbers. DATA: " + json.dumps(measured))
        return {"analyses": [{"type": "rain", "text": output}],
                "events": [{"step": "rain_agent", "status": "ok", "ms": round((time.perf_counter()-started)*1000)}]}
    except Exception as exc:
        return {"analyses": [{"type": "rain", "error": str(exc)}],
                "events": [{"step": "rain_agent", "status": "error", "error": str(exc)}]}


async def comfort_agent(state: TravelState):
    measured = [x["data"] for x in state["weather_results"] if x["status"] == "ok"]
    started = time.perf_counter()
    try:
        output = await complete(
            "You are a temperature and wind comfort analyst. " + read_skill(),
            "Explain maximum temperature and maximum wind speed. "
            "Do not invent numbers. DATA: " + json.dumps(measured))
        return {"analyses": [{"type": "comfort", "text": output}],
                "events": [{"step": "comfort_agent", "status": "ok", "ms": round((time.perf_counter()-started)*1000)}]}
    except Exception as exc:
        return {"analyses": [{"type": "comfort", "error": str(exc)}],
                "events": [{"step": "comfort_agent", "status": "error", "error": str(exc)}]}


def reviewer(state: TravelState):
    analyses = state.get("analyses", [])
    kinds = {x.get("type") for x in analyses if x.get("text")}
    if not {"rain", "comfort"}.issubset(kinds):
        return {"error": "One or more analysis agents failed; recommendation withheld",
                "events": [{"step": "reviewer", "status": "error", "analyses": analyses}]}
    if not state.get("ranking"):
        return {"error": "No valid ranked weather results", "events": [{"step": "reviewer", "status": "error"}]}
    return {"events": [{"step": "reviewer", "status": "passed", "top": state["ranking"][0]["city"]}]}


def after_review(state: TravelState):
    return "error_handler" if state.get("error") else "response_agent"


async def response_agent(state: TravelState):
    # Recommendation winner is deterministic; the LLM only explains it.
    top = state["ranking"][0]
    data = [x["data"] for x in state["weather_results"] if x["status"] == "ok"]
    prompt = ("User question: " + state["question"] + "\nDate: " + state["plan"]["date"] +
              "\nVerified weather data: " + json.dumps(data) +
              "\nRanking from transparent DEMO heuristic: " + json.dumps(state["ranking"]) +
              "\nSpecialist analyses: " + json.dumps(state["analyses"]) +
              "\nWarning: " + state.get("warning", "") +
              "\nRecommend EXACTLY " + top["city"] +
              " as highest under this heuristic. State clearly that the weights are a subjective "
              "outdoor suitability demo heuristic, not an official weather safety index. "
              "State any failed cities. Do not invent measurements.")
    try:
        text = await complete("You are a cautious travel weather advisor. " + read_skill(), prompt)
        prefix = ("SIMULATED DEMO — NO LIVE WEATHER / NO OLLAMA\n\n"
                  if os.getenv("WEATHER_DEMO_MODE") == "1" else "")
        # Deterministic header avoids relying solely on the model's prose for the ranking.
        answer = (prefix + f"Top city by demo suitability score: {top['city']} "
                  f"({top['score']}/100) for {state['plan']['date']}.\n\n" + text)
        if state.get("warning"):
            answer += "\n\n" + state["warning"]
        return {"answer": answer, "events": [{"step": "response_agent", "status": "ok"}]}
    except Exception as exc:
        return {"error": "Response generation failed: " + str(exc),
                "events": [{"step": "response_agent", "status": "error", "error": str(exc)}]}


def error_handler(state: TravelState):
    return {"answer": "Unable to complete this request: " + state.get("error", "unknown error"),
            "events": [{"step": "error_handler", "status": "handled"}]}


def build_graph():
    graph = StateGraph(TravelState)
    for name, fn in [("planner", planner), ("weather_worker", weather_worker),
                     ("gather", gather), ("fanout_analysis", fanout_analysis),
                     ("rain_agent", rain_agent), ("comfort_agent", comfort_agent),
                     ("reviewer", reviewer), ("response_agent", response_agent),
                     ("error_handler", error_handler)]:
        graph.add_node(name, fn)
    graph.add_edge(START, "planner")
    graph.add_conditional_edges("planner", dispatch)
    graph.add_edge("weather_worker", "gather")
    graph.add_conditional_edges("gather", after_gather)
    graph.add_edge("fanout_analysis", "rain_agent")
    graph.add_edge("fanout_analysis", "comfort_agent")
    graph.add_edge(["rain_agent", "comfort_agent"], "reviewer")
    graph.add_conditional_edges("reviewer", after_review)
    graph.add_edge("response_agent", END)
    graph.add_edge("error_handler", END)
    return graph.compile()


GRAPH = build_graph()


async def run(question: str):
    return await GRAPH.ainvoke({"question": question, "weather_results": [], "analyses": [], "events": []})
