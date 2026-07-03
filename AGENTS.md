# AGENTS.md — BizInsight Agent Project Context

## Project Overview
BizInsight Agent is a multi-agent business intelligence system built with CrewAI.
It analyzes business data (CSV files), generates insights, and produces structured reports.

## Stack
- **Agent Framework**: CrewAI (multi-agent orchestration)
- **MCP Servers**: Custom data-access and chart-generation servers (stdio transport)
- **LLM**: Google Gemini (configurable via GOOGLE_API_KEY in .env)
- **Data**: pandas, numpy
- **Visualization**: matplotlib, seaborn
- **Language**: Python 3.10+

## Project Conventions
- Always begin by thinking deeply before coding — explicitly state assumptions, surface tradeoffs, and halt to ask for clarification the moment you encounter ambiguity rather than guessing silently.
- Write only the absolute minimum amount of code required to solve the immediate problem, strictly avoiding speculative features, unrequested abstractions, or predictive configurations.
- When editing existing code, make highly surgical changes by restricting your updates only to the exact lines necessary to fulfill the request, maintaining the existing style perfectly, and leaving adjacent, unbroken code completely untouched unless your changes directly orphaned an import or variable.
- Approach every task through goal-driven execution by breaking it down into a clear, step-by-step plan with strong success criteria.
- All MCP tools must validate inputs before execution.
- All file I/O is scoped to the `data/` and `output/` directories. Never read or write outside these paths.
- Never hardcode API keys. Use environment variables only.
- Use `[[VARIABLE]]` placeholder syntax in all agent-facing templates. Never hardcode PII.

## Spec-Driven Development (Day 5)
- BDD specifications live in `specs/` using Gherkin format (Given / When / Then)
- Specs are the source of truth — if code diverges from specs, the code is wrong
- Use the spec to drive test creation and agent behavior verification

## Zero-Trust Governance (Day 5)
- All tool calls pass through the Policy Server (`policy_server.py`)
- Policies are defined in `policies.yaml` — structural gating via role/environment
- Context hygiene is enforced via `context_resolver.py` — PII masking + placeholder resolution
- No tool has ambient authority; every action is checked before execution

## Available Skills
The following Agent Skills are installed and available for on-demand loading:

| Skill | Trigger | Description |
|---|---|---|
| `data-analysis` | "analyze", "statistics", "trend", "anomaly", "profile" | Business data analysis methodology with statistical scripts |
| `insight-generation` | "insight", "finding", "pattern", "recommendation" | Business insight frameworks and narration patterns |
| `report-writing` | "report", "summary", "document", "executive" | Report structure, templates, and formatting utilities |

## MCP Servers
| Server | Transport | Tools Available |
|---|---|---|
| Data Server | stdio | read_csv, filter_rows, get_columns, compute_aggregate, detect_anomalies |
| Charts Server | stdio | create_bar_chart, create_line_chart, create_pie_chart, create_heatmap |

## Build & Run
```bash
pip install -r requirements.txt
python main.py --data data/sample_business_data.csv --query "Your business question here"
```