"""End-to-end deterministic graph test, no model or external services needed."""
import asyncio
from travel_agent.graph import run


def test_parallel_graph(monkeypatch):
    monkeypatch.setenv("WEATHER_DEMO_MODE", "1")
    result = asyncio.run(run("Compare Bengaluru Chennai Hyderabad Mumbai for tomorrow"))
    assert not result.get("error")
    workers = [e for e in result["events"] if e["step"] == "weather_worker"]
    assert len(workers) == 4
    assert {e["city"] for e in workers} == {"Bengaluru", "Chennai", "Hyderabad", "Mumbai"}
    analyses = {a["type"] for a in result["analyses"]}
    assert analyses == {"rain", "comfort"}
    assert result["ranking"]
    assert "SIMULATED DEMO" in result["answer"]


def test_invalid_graph_routes_error(monkeypatch):
    monkeypatch.setenv("WEATHER_DEMO_MODE", "1")
    result = asyncio.run(run("Forecast next month"))
    assert result.get("error")
    assert "Unable to complete" in result["answer"]
