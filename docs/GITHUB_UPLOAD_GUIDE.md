# Upload without Git commands — GitHub browser UI

1. Sign in at https://github.com and click **+ → New repository**.
2. Repository name: `parallel-ai-travel-weather-advisor`.
3. Description: `Parallel LangGraph weather agents with Ollama, MCP tool calling, live Open-Meteo forecasts, scoring and Streamlit UI.`
4. Choose **Public** if publishing the code is authorized. Keep it private otherwise. Do **not** initialize with an extra README because one is included here.
5. Click **Create repository**. The empty repository may show **uploading an existing file**. Select that, or **Add file → Upload files**.
6. Extract the ZIP locally. **Open its inner folder**, select all its contents (files and folders) and **drag them from Windows File Explorer onto the GitHub upload screen**. Do not upload the ZIP as one file if you want GitHub to display the source tree and README.
7. Confirm the browser shows paths like `travel_agent/graph.py`, `assets/workflow.gif`, `.github/workflows/tests.yml`, and `README.md` before committing.
8. Enter commit message: `Add parallel AI Travel Weather Advisor with MCP and LangGraph` and click **Commit changes**.
9. Go to the repository home page. Confirm the README displays its animation below the title and the **Actions** tab reports the test workflow result.
10. Add repository **About** topics: `langgraph`, `ollama`, `mcp`, `multi-agent`, `python`, `streamlit`, `open-meteo`, `weather-agent`, `agentic-ai`.
11. Copy the repository URL into your resume/portfolio only after verifying the page loads and tests pass.

## Windows upload gotchas

- File picker **Choose your files** can limit folder selection. Use drag-and-drop of the selected contents from File Explorer.
- Ensure hidden `.github` and `.gitignore` are visible in Explorer (View → Show → Hidden items). If hidden content is missed, upload those separately with **Add file → Upload files** or GitHub's **Create new file** (enter nested paths using `/`).
- A repository browser upload is limited to 25 MiB per file. This project uses smaller assets.
- Never upload `.venv`, `.env`, credentials, company documents or sensitive data.
- If folder drag-and-drop does not preserve paths in your browser, use GitHub Desktop for folder-aware upload without terminal commands.
