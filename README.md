# BizInsight Agent: Multi-Agent Business Intelligence System

> A multi-agent system that automates business data analysis, insight generation, and report creation — demonstrating **Multi-Agent Systems**, **MCP (Model Context Protocol)**, and **Agent Skills** from the 5-Day AI Agents: Intensive Vibe Coding Course with Google.

---

## 🏆 Kaggle Capstone Project — Agents for Business Track

### Problem Statement

Small and medium businesses generate large volumes of operational data (sales, expenses, inventory) but lack the resources to hire dedicated data analysts. Manual analysis is slow, inconsistent, and often misses critical patterns. This project builds an **autonomous multi-agent system** that ingests business data, performs structured analysis, generates actionable insights, and produces professional reports — all through natural language interaction.

### Key Concepts Demonstrated

| Course Concept | How It's Demonstrated |
|---|---|
| **Multi-Agent Systems** (Day 1) | 4 specialized CrewAI agents (Orchestrator, Data Analyst, Insight Generator, Report Writer) collaborate via structured delegation |
| **MCP Servers** (Day 2) | 2 custom MCP servers (data access + chart generation) with Discovery → Configuration → Connection pattern |
| **Agent Skills** (Day 3) | 3 SKILL.md files with Progressive Disclosure (metadata → body → scripts/references) |
| **Context Engineering** (Day 1) | AGENTS.md provides project-level context; Skills loaded on-demand to prevent context rot |
| **Security** (Day 4) | Input validation, sandboxed code execution, egress governance on MCP servers |
| **Spec-Driven Dev** (Day 5) | BDD specs (Gherkin), Policy Server (Zero-Trust), Context Hygiene (PII masking) |

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                 User (Natural Language)          │
│          "Analyze Q2 sales data and find..."     │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│           Orchestrator Agent (Router)           │
│    Routes requests, coordinates sub-agents      │
└──┬──────────────┬───────────────┬───────────────┘
   │              │               │
   ▼              ▼               ▼
┌─────────┐      ┌──────────┐ ┌──────────────┐
│  Data   │      │ Insight  │ │   Report     │
│ Analyst │      │ Generator│ │   Writer     │
│  Agent  │      │  Agent   │ │   Agent      │
└────┬────┘      └────┬─────┘ └──────┬───────┘
     │                │              │
     │         ┌──────┴──────┐       │
     │         │  Agent      │       │
     ▼         │  Skills     │       ▼
┌────────────┐ │ (SKILL.md)  │  ┌────────────┐
│  MCP       │ │             │  │  MCP       │
│  Data      │   ◄───────────┘  │  Charts    │
│  Server    │                  │  Server    │
│            │                  │            │
│ • CSV read │                  │ • Bar chart│
│ • Filter   │                  │ • Line plot│
│ • Aggregate│                  │ • Heatmap  │
└────────────┘                  └────────────┘
```

### Agent Roles

1. **Orchestrator Agent**: Receives user requests, breaks them into tasks, delegates to specialist agents, and synthesizes results. Implements the "Orchestrator" pattern from Day 1.

2. **Data Analyst Agent**: Connects to data sources via MCP, performs statistical analysis (aggregation, trend detection, anomaly identification). Uses `data-analysis` Skill.

3. **Insight Generator Agent**: Transforms raw analysis into business-relevant insights using frameworks (SWOT, Pareto, growth patterns). Uses `insight-generation` Skill.

4. **Report Writer Agent**: Produces structured markdown reports with embedded charts (via MCP Charts Server). Uses `report-writing` Skill.

### MCP Servers

1. **Data Server** (`mcp_servers/data_server/`): Provides tools for reading CSV files, filtering rows, computing aggregates, and detecting anomalies. Uses stdio transport.

2. **Charts Server** (`mcp_servers/charts_server/`): Provides tools for generating matplotlib/seaborn charts (bar, line, pie, heatmap) and saving them as files. Uses stdio transport.

### Agent Skills (SKILL.md)

1. **data-analysis** (`skills/data-analysis/`): Defines how to approach business data analysis — column profiling, outlier detection using IQR, trend analysis, correlation checks. Includes Python scripts for statistical computations.

2. **insight-generation** (`skills/insight-generation/`): Defines business insight frameworks — what makes a good insight, Pareto analysis, YoY growth patterns, anomaly narration. Includes reference documents.

3. **report-writing** (`skills/report-writing/`): Defines report structure — executive summary, methodology, findings, recommendations. Includes Jinja2 templates and formatting scripts.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Gemini API key (or OpenAI/Anthropic)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/bizinsight-agent.git
cd bizinsight-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your API key
```

### Running the Demo

```bash
# Run the main pipeline with sample data
python main.py --data data/sample_business_data.csv --query "Analyze sales trends and identify top performing categories"

# Run with custom options
python main.py --data data/sample_business_data.csv --query "Find expense anomalies in Q2" --output output/
```

### Running MCP Servers Manually (for debugging)

```bash
# Start Data MCP Server
python -m mcp_servers.data_server.server

# In another terminal, verify with MCP Inspector
npx @modelcontextprotocol/inspector python -m mcp_servers.data_server.server
```

---

## 📁 Project Structure

```
bizinsight-agent/
├── AGENTS.md                    # Project-level context (Day 1: Context Engineering)
├── README.md                    # This file
├── requirements.txt
├── .env.example
├── main.py                      # Entry point - orchestrates the full pipeline
├── specs/                       # BDD Specifications (Day 5: SDD)
│   └── analysis_pipeline.feature # Gherkin scenarios (Given/When/Then)
├── policy_server.py             # Day 5: Policy Server (Zero-Trust guardrail)
├── context_resolver.py          # Day 5: Context Hygiene (PII masking, prompt sanitization)
├── policies.yaml                # Day 5: Policy configuration (role/environment rules)
│
├── crew/                        # CrewAI multi-agent system
│   ├── config/
│   │   ├── agents.yaml          # Agent definitions (roles, goals, backstories)
│   │   └── tasks.yaml           # Task definitions (what each agent does)
│   ├── agents/                  # Agent implementations
│   │   ├── orchestrator.py
│   │   ├── data_analyst.py
│   │   ├── insight_generator.py
│   │   └── report_writer.py
│   └── tasks/                   # Task implementations
│       ├── analyze_data.py
│       ├── generate_insights.py
│       └── write_report.py
│
├── mcp_servers/                 # MCP Servers (Day 2: Interoperability)
│   ├── data_server/
│   │   ├── server.py            # MCP server for data access
│   │   └── SKILL.md             # Skill documentation for the server
│   └── charts_server/
│       ├── server.py            # MCP server for chart generation
│       └── SKILL.md
│
├── skills/                      # Agent Skills (Day 3: Skills)
│   ├── data-analysis/
│   │   ├── SKILL.md             # Analysis methodology
│   │   ├── scripts/
│   │   │   └── analyze.py       # Statistical analysis functions
│   │   └── references/
│   │       └── methods.md       # Statistical methods reference
│   ├── insight-generation/
│   │   ├── SKILL.md             # Insight frameworks
│   │   └── references/
│   │       └── frameworks.md    # Business analysis frameworks
│   └── report-writing/
│       ├── SKILL.md             # Report structure guide
│       ├── scripts/
│       │   └── format_report.py # Report formatting utilities
│       └── assets/
│           └── report_template.md
│
├── data/
│   └── sample_business_data.csv # Sample dataset for demo
│
├── notebooks/
│   └── demo.ipynb               # Interactive Kaggle notebook
│
├── output/                      # Generated reports and charts
│
└── tests/
    ├── test_mcp_servers.py
    ├── test_skills.py
    ├── test_crew.py
    └── test_day5.py
```

---

## 📖 Concept Mapping to Course Content

### Day 1: The New SDLC with Vibe Coding

| Concept | Implementation |
|---|---|
| **Agentic Engineering** | The project follows the disciplined end of the spectrum — formal specs (AGENTS.md), automated testing, structured agent definitions |
| **Harness Engineering** | MCP servers + Skills form the "harness" around the LLM — tools, memory (context), and orchestration |
| **Context Engineering** | AGENTS.md provides project-level context; Skills use Progressive Disclosure to load knowledge on-demand, preventing context rot |
| **Orchestrator Pattern** | The Orchestrator Agent delegates tasks asynchronously to specialist agents, then synthesizes results |
| **AGENTS.md** | Contains project conventions, coding standards, and skill catalog |

### Day 2: Agent Tools & Interoperability

| Concept | Implementation |
|---|---|
| **MCP Discovery** | Data and Charts servers are registered with proper tool schemas |
| **MCP Configuration** | Environment variables for API keys, file paths scoped to project |
| **MCP Connection** | stdio transport for local execution; tools verified via handshake |
| **NxM Problem Solved** | Both agents connect to same MCP servers — O(N+M) instead of O(N*M) |
| **MCP Best Practices** | No hardcoded credentials, read-only data access, scoped to project directory |

### Day 3: Agent Skills

| Concept | Implementation |
|---|---|
| **SKILL.md Format** | YAML frontmatter (name, description) + markdown instructions |
| **Progressive Disclosure** | 3 levels: metadata always loaded → body on trigger → scripts/references on demand |
| **Skill vs MCP** | Skills provide "know-how" (how to analyze), MCP provides "reach" (access to data) |
| **DAG Orchestration** | Tasks flow in a directed acyclic graph: Analyze → Generate Insights → Write Report |
| **Eval Coverage** | Tests verify skill triggering, output quality, and tool trajectory |

### Day 4: Security & Evaluation

| Concept | Implementation |
|---|---|
| **Sandboxing** | Data server restricts file access to `data/` directory only |
| **Egress Governance** | MCP servers have no outbound network access; data stays local |
| **Input Validation** | All MCP tool inputs are validated before execution |
| **Zero Ambient Authority** | Each tool has minimal required permissions |
| **Observability** | Structured logging of all agent actions and tool calls |

### Day 5: Spec-Driven Production Grade Development

| Concept | Implementation |
|---|---|
| **Spec-Driven Development (SDD)** | BDD specs in `specs/` using Gherkin (Given/When/Then) — specs are the source of truth |
| **Hybrid Markdown + YAML** | SKILL.md uses YAML frontmatter for metadata, Markdown for methodology (per SkCC research) |
| **Policy Server** | `policy_server.py` implements Structural Gating — YAML-based role/environment permissions |
| **Zero-Trust Development** | Every tool call passes through Policy Server before execution; no ambient authority |
| **Context Hygiene** | `context_resolver.py` — PII masking, `[[VARIABLE]]` placeholder resolution, prompt sanitization |
| **AI-Generated Test Coverage** | 48+ tests covering all 5 days' concepts; eval-based quality gates |
| **Where Instructions Live** | 4 layers: Chat → `specs/` → `skills/` (SKILL.md) → `AGENTS.md` (global) |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test MCP servers
pytest tests/test_mcp_servers.py -v

# Test skill loading
pytest tests/test_skills.py -v

# Test crew execution
pytest tests/test_crew.py -v
```

---

## 📊 Sample Output

When you run the demo with the sample dataset, the system produces:

1. **Statistical Analysis** — column profiles, trend detection, anomaly flags
2. **Business Insights** — categorized findings with business impact ratings
3. **Visualization Charts** — trend lines, category breakdowns, heatmaps (saved as PNG)
4. **Final Report** — structured markdown document with executive summary, methodology, findings, and recommendations

---

## 🛠️ Extending the Project

- **Add new MCP servers**: Connect to Google Sheets, BigQuery, or Salesforce
- **Add new Skills**: Create domain-specific skills (financial analysis, inventory optimization)
- **Add new Agents**: Extend with a Forecasting Agent or an Alert Agent
- **Deploy**: Containerize with Docker, deploy on GCP Cloud Run

---

## 📝 License

MIT License — Feel free to use and modify for your own projects.

---

## 🙏 Acknowledgments

Built as a Capstone Project for the **5-Day AI Agents: Intensive Vibe Coding Course with Google** (July 2026).

Course materials referenced:
- Day 1: The New SDLC With Vibe Coding
- Day 2: Agent Tools & Interoperability
- Day 3: Agent Skills
- Day 4: Vibe Coding Agent Security and Evaluation
- Day 5: Spec-Driven Production Grade Development in the Age of Vibe Coding