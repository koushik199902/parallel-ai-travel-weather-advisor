from travel_agent.decision import plan_request, score_weather, rank_results
from travel_agent.weather import india_date, simulated_weather
import pytest

def test_plan_four_cities():
    p = plan_request("Compare Bengaluru, Chennai, Hyderabad, and Mumbai for tomorrow")
    assert len(p["cities"]) == 4
    assert p["date"] == india_date(1)

def test_invalid_question():
    with pytest.raises(ValueError):
        plan_request("weather next month")

def test_score_bounded():
    for city in ("Bengaluru", "Mumbai"):
        score = score_weather(simulated_weather(city, india_date(1)))
        assert 0 <= score["score"] <= 100

def test_rank_orders_score():
    data = [{"status":"ok", "data":simulated_weather(city, india_date(1))}
            for city in ("Mumbai", "Bengaluru")]
    ranking = rank_results(data)
    assert ranking[0]["score"] >= ranking[-1]["score"]
