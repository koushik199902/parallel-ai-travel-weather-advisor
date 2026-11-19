"""Streamlit user interface for the parallel LangGraph weather project."""
import asyncio
import os
import streamlit as st
from travel_agent.graph import run

st.set_page_config(page_title="Parallel AI Travel Weather Advisor", page_icon="🌦️", layout="wide")
st.title("🌦️ Parallel Multi-Agent Travel Weather Advisor")
st.caption("LangGraph • Ollama • Local MCP • Open-Meteo • Four parallel city workers + two analysis agents")

with st.sidebar:
    st.subheader("Demo options")
    demo = st.checkbox("Simulated offline demo (clearly labeled)", value=False)
    st.info("Unchecked: actual MCP + live forecast + Ollama. Checked: fictional weather and AI analysis for workflow rehearsal only.")
    st.caption("Model is configurable with OLLAMA_MODEL environment variable; default llama3.2.")

question = st.text_area("Ask a question", value=(
    "Compare the weather in Bengaluru, Chennai, Hyderabad, and Mumbai for tomorrow. "
    "Analyze temperature, rainfall, and wind conditions, and recommend the best city for outdoor activities."), height=105)

if st.button("Run multi-agent workflow", type="primary"):
    if demo:
        os.environ["WEATHER_DEMO_MODE"] = "1"
    else:
        os.environ.pop("WEATHER_DEMO_MODE", None)
    with st.spinner("Running LangGraph weather workers and analysis agents..."):
        try:
            result = asyncio.run(run(question))
            st.subheader("Recommendation")
            st.write(result.get("answer", "No answer returned"))
            if result.get("warning"):
                st.warning(result["warning"])
            ranked = result.get("ranking", [])
            if ranked:
                st.subheader("Transparent outdoor suitability ranking")
                st.caption("Illustrative heuristic: rain 45%, temperature 35%, wind 20%. Not a safety index.")
                st.dataframe(ranked, use_container_width=True)
            st.subheader("Per-city results")
            st.dataframe(result.get("weather_results", []), use_container_width=True)
            with st.expander("Parallel execution trace", expanded=True):
                st.json(result.get("events", []))
            with st.expander("Shared LangGraph state"):
                st.json(result)
        except Exception as exc:
            st.error(f"Workflow failed: {type(exc).__name__}: {exc}")
