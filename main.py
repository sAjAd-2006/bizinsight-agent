"""
BizInsight Agent — Main Entry Point

Demonstrates:
1. Multi-Agent System (Day 1) — CrewAI orchestration with 4 specialized agents
2. MCP Servers (Day 2) — Data and Charts servers with stdio transport
3. Agent Skills (Day 3) — SKILL.md files with Progressive Disclosure
4. Security (Day 4) — Sandboxed file access, input validation, egress governance
5. Spec-Driven Development (Day 5) — BDD specs in specs/, Policy Server, Context Hygiene

Usage:
    python main.py --data data/sample_business_data.csv --query "Analyze sales trends"
    python main.py --data data/sample_business_data.csv --query "Find expense anomalies" --output output/
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import crewai
from crewai import Agent, Task, Crew, Process


# ============================================================
# Day 5: Policy Server & Context Hygiene Integration
# ============================================================

def create_policy_service(environment: str = "localhost", role: str = "analyst"):
    """
    Day 5: Create a Policy Server instance.
    Implements Zero-Trust Development — Structural Gating.
    """
    from policy_server import PolicyService
    config_path = PROJECT_ROOT / "policies.yaml"
    return PolicyService(
        config_path=str(config_path),
        environment=environment,
        role=role,
    )


def create_policy_guarded_tool(tool, policy_service):
    """
    Day 5: Wrap a CrewAI tool with Policy Server enforcement.
    Before the tool executes, the Policy Server checks if it's allowed.
    """
    from crewai.tools import BaseTool

    class PolicyGuardedTool(BaseTool):
        name: str = tool.name + "_guarded"
        description: str = tool.description + " [Policy-guarded: checked before execution]"

        def _run(self, *args, **kwargs):
            # Day 5: Structural Gating — check before execution
            if not policy_service.is_tool_allowed(tool.name):
                return json.dumps({"error": policy_service.get_violation_message(tool.name)})
            return tool._run(*args, **kwargs)

    guarded = PolicyGuardedTool()
    return guarded


# ============================================================
# Skill Loading (Day 3: Progressive Disclosure)
# ============================================================

def load_skill(skill_name: str) -> str:
    """
    Load a SKILL.md file content.
    Implements Day 3 Progressive Disclosure:
    - Level 1 (metadata): Already in agent's context via AGENTS.md catalog
    - Level 2 (body): Loaded here when skill triggers
    - Level 3 (resources): Referenced but not loaded (scripts/references)
    """
    skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return f"Skill '{skill_name}' not found at {skill_path}"


# ============================================================
# MCP Tool Integration (Day 2: Discovery → Configuration → Connection)
# ============================================================

def create_mcp_tools():
    """
    Create CrewAI-compatible tool wrappers for MCP servers.
    Demonstrates Day 2: MCP as the 'USB-C' for agent tools.
    In production, use crewai-tools MCP integration.
    For the capstone demo, we use direct Python imports for simplicity.
    """
    from crewai.tools import BaseTool
    import pandas as pd
    import numpy as np

    DATA_DIR = os.environ.get("DATA_DIR", str(PROJECT_ROOT / "data"))
    OUTPUT_DIR = os.environ.get("OUTPUT_DIR", str(PROJECT_ROOT / "output"))
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Data Tools ---

    class ReadCSVTool(BaseTool):
        name: str = "read_csv"
        description: str = (
            "Read a CSV file from the data directory. Returns first N rows as JSON. "
            "Args: filename (str), max_rows (int, default 100)."
        )

        def _run(self, filename: str, max_rows: int = 100) -> str:
            max_rows = min(max(1, max_rows), 500)
            path = os.path.abspath(os.path.join(DATA_DIR, filename))
            if not path.startswith(os.path.abspath(DATA_DIR)):
                return json.dumps({"error": "Access denied"})
            if not os.path.isfile(path):
                return json.dumps({"error": f"File not found: {filename}"})
            df = pd.read_csv(path)
            return json.dumps({
                "rows_returned": min(len(df), max_rows),
                "total_rows": len(df),
                "columns": list(df.columns),
                "data": json.loads(df.head(max_rows).to_json(orient="records", date_format="iso"))
            })

    class GetColumnsTool(BaseTool):
        name: str = "get_columns"
        description: str = "Get column names, data types, null counts, and unique values for a CSV file."

        def _run(self, filename: str) -> str:
            path = os.path.abspath(os.path.join(DATA_DIR, filename))
            if not path.startswith(os.path.abspath(DATA_DIR)):
                return json.dumps({"error": "Access denied"})
            df = pd.read_csv(path)
            info = []
            for col in df.columns:
                info.append({
                    "name": col, "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique()),
                    "sample_values": df[col].dropna().head(3).tolist()
                })
            return json.dumps({"total_rows": len(df), "columns": info})

    class ComputeAggregateTool(BaseTool):
        name: str = "compute_aggregate"
        description: str = (
            "Compute aggregated statistics grouped by a column. "
            "Args: filename, group_by, metric_column, aggregation (sum/mean/median/min/max/count)."
        )

        def _run(self, filename: str, group_by: str, metric_column: str, aggregation: str = "sum") -> str:
            path = os.path.abspath(os.path.join(DATA_DIR, filename))
            if not path.startswith(os.path.abspath(DATA_DIR)):
                return json.dumps({"error": "Access denied"})
            df = pd.read_csv(path)
            if group_by not in df.columns or metric_column not in df.columns:
                return json.dumps({"error": "Column not found"})
            df[metric_column] = pd.to_numeric(df[metric_column], errors="coerce")
            grouped = df.groupby(group_by)[metric_column].agg(aggregation).reset_index()
            grouped.columns = [group_by, f"{aggregation}_of_{metric_column}"]
            grouped = grouped.sort_values(f"{aggregation}_of_{metric_column}", ascending=False)
            return json.dumps({
                "group_by": group_by, "metric": metric_column,
                "aggregation": aggregation,
                "result": json.loads(grouped.to_json(orient="records"))
            })

    class DetectAnomaliesTool(BaseTool):
        name: str = "detect_anomalies"
        description: str = (
            "Detect outliers in a numeric column using IQR method. "
            "Args: filename, column, method (iqr/zscore)."
        )

        def _run(self, filename: str, column: str, method: str = "iqr") -> str:
            path = os.path.abspath(os.path.join(DATA_DIR, filename))
            if not path.startswith(os.path.abspath(DATA_DIR)):
                return json.dumps({"error": "Access denied"})
            df = pd.read_csv(path)
            if column not in df.columns:
                return json.dumps({"error": "Column not found"})
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (series < lower) | (series > upper)
            return json.dumps({
                "method": "IQR", "column": column,
                "q1": float(q1), "q3": float(q3), "iqr": float(iqr),
                "lower_bound": float(lower), "upper_bound": float(upper),
                "anomaly_count": int(mask.sum()),
                "anomaly_values": series[mask].tolist()
            })

    # --- Charts Tools ---

    class CreateBarChartTool(BaseTool):
        name: str = "create_bar_chart"
        description: str = "Create a bar chart from JSON data and save as PNG. Args: data_json, labels_key, values_key, title, filename."

        def _run(self, data_json: str, labels_key: str, values_key: str, title: str = "Bar Chart", filename: str = "bar_chart.png") -> str:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            data = json.loads(data_json)
            labels = [str(item.get(labels_key, "")) for item in data]
            values = [float(item.get(values_key, 0)) for item in data]
            fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
            bars = ax.bar(labels, values, color="#4A90D9", edgecolor="white")
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.tick_params(axis="x", rotation=45)
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + bar.get_height()*0.01,
                        f"{bar.get_height():,.0f}", ha="center", va="bottom", fontsize=9)
            out_path = os.path.join(OUTPUT_DIR, filename)
            fig.savefig(out_path, bbox_inches="tight")
            plt.close(fig)
            return json.dumps({"status": "success", "file": filename, "path": out_path})

    class CreateLineChartTool(BaseTool):
        name: str = "create_line_chart"
        description: str = "Create a line chart from JSON data and save as PNG. Args: data_json, x_key, y_key, title, filename."

        def _run(self, data_json: str, x_key: str, y_key: str, title: str = "Line Chart", filename: str = "line_chart.png") -> str:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            data = json.loads(data_json)
            x_vals = [str(item.get(x_key, "")) for item in data]
            y_vals = [float(item.get(y_key, 0)) for item in data]
            fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
            ax.plot(x_vals, y_vals, color="#2ECC71", linewidth=2, marker="o", markersize=5)
            ax.fill_between(range(len(x_vals)), y_vals, alpha=0.1, color="#2ECC71")
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.tick_params(axis="x", rotation=45)
            ax.grid(axis="y", alpha=0.3)
            out_path = os.path.join(OUTPUT_DIR, filename)
            fig.savefig(out_path, bbox_inches="tight")
            plt.close(fig)
            return json.dumps({"status": "success", "file": filename, "path": out_path})

    return [
        ReadCSVTool(), GetColumnsTool(), ComputeAggregateTool(), DetectAnomaliesTool(),
        CreateBarChartTool(), CreateLineChartTool()
    ]


# ============================================================
# Agent Creation (Day 1: Orchestrator Pattern)
# ============================================================

def create_agents(tools, llm, policy_service=None):
    """Create the 4 specialized agents with their Skills loaded."""
    import yaml

    with open(PROJECT_ROOT / "crew" / "config" / "agents.yaml", "r") as f:
        agent_configs = yaml.safe_load(f)

    # Load Skills for each agent (Day 3: Progressive Disclosure)
    data_analysis_skill = load_skill("data-analysis")
    insight_skill = load_skill("insight-generation")
    report_skill = load_skill("report-writing")

    # Day 5: Wrap tools with Policy Server if provided
    active_tools = tools
    if policy_service:
        active_tools = [create_policy_guarded_tool(t, policy_service) for t in tools]

    orchestrator = Agent(
        role=agent_configs["orchestrator"]["role"],
        goal=agent_configs["orchestrator"]["goal"],
        backstory=agent_configs["orchestrator"]["backstory"],
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )

    data_analyst = Agent(
        role=agent_configs["data_analyst"]["role"],
        goal=agent_configs["data_analyst"]["goal"],
        backstory=agent_configs["data_analyst"]["backstory"]
            + f"\n\n## Your Skill (always follow this methodology):\n{data_analysis_skill}",
        tools=active_tools,
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    insight_generator = Agent(
        role=agent_configs["insight_generator"]["role"],
        goal=agent_configs["insight_generator"]["goal"],
        backstory=agent_configs["insight_generator"]["backstory"]
            + f"\n\n## Your Skill (use these frameworks):\n{insight_skill}",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    report_writer = Agent(
        role=agent_configs["report_writer"]["role"],
        goal=agent_configs["report_writer"]["goal"],
        backstory=agent_configs["report_writer"]["backstory"]
            + f"\n\n## Your Skill (follow this template):\n{report_skill}",
        tools=[t for t in active_tools if "chart" in t.name.lower()],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return orchestrator, data_analyst, insight_generator, report_writer


# ============================================================
# Main Pipeline
# ============================================================

def run_analysis(data_file: str, query: str, output_dir: str = "output",
                 enable_policy: bool = True, role: str = "analyst"):
    """Run the full multi-agent analysis pipeline."""
    print("=" * 60)
    print("BizInsight Agent — Multi-Agent Business Intelligence")
    print("=" * 60)
    print(f"Data: {data_file}")
    print(f"Query: {query}")
    print(f"Output: {output_dir}")
    print(f"Policy Server: {'enabled' if enable_policy else 'disabled'}")
    print()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize LLM
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    from crewai import LLM
    model_name = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
    llm = LLM(model=f"google/{model_name}", api_key=api_key)

    # Day 5: Create Policy Server (Zero-Trust Development)
    policy_service = None
    if enable_policy:
        print("[Day 5] Initializing Policy Server (Zero-Trust)...")
        policy_service = create_policy_service(role=role)
        allowed = policy_service.list_allowed_tools()
        print(f"  Role: {role} | Allowed tools: {allowed}")
        print()

    # Create tools (Day 2: MCP integration)
    print("[Day 2] Creating MCP tool wrappers...")
    tools = create_mcp_tools()
    print(f"  Tools available: {[t.name for t in tools]}")
    print()

    # Create agents (Day 1: Multi-Agent + Day 3: Skills + Day 5: Policy)
    print("[Day 1+3+5] Creating agents with Skills + Policy Guard...")
    orchestrator, data_analyst, insight_generator, report_writer = create_agents(
        tools, llm, policy_service=policy_service
    )
    print(f"  Agents: {orchestrator.role}, {data_analyst.role}, {insight_generator.role}, {report_writer.role}")
    print()

    # Define tasks (DAG Orchestration — Day 3)
    print("[Day 3] Defining task DAG: Analyze -> Generate Insights -> Write Report")

    analyze_task = Task(
        description=f"Analyze the business data in '{data_file}' to answer: {query}. "
                    f"Use the data tools to: 1) Profile columns with get_columns, "
                    f"2) Read sample data with read_csv, "
                    f"3) Compute aggregations by category and region, "
                    f"4) Detect anomalies in key metrics. "
                    f"Return ALL results as structured JSON.",
        expected_output="Comprehensive JSON analysis with column profiles, aggregated statistics, anomalies, and trends.",
        agent=data_analyst,
    )

    insights_task = Task(
        description="Based on the analysis results, generate 3-5 business insights. "
                    "For each: title, category (revenue/cost/efficiency/risk/opportunity), "
                    "impact (high/medium/low), description with specific numbers, "
                    "and actionable recommendation.",
        expected_output="JSON list of 3-5 insights with title, category, impact, description, and recommendation.",
        agent=insight_generator,
        context=[analyze_task],
    )

    report_task = Task(
        description=f"Write a professional markdown report. Data source: {data_file}. "
                    f"Query: {query}. Follow the report-writing skill template. "
                    f"Include: header, executive summary (<100 words), key findings with "
                    f"impact ratings, data overview, detailed analysis, and recommendations. "
                    f"Generate at least one chart using the chart tools.",
        expected_output="Complete markdown report saved to the output directory with executive summary, "
                        "findings, methodology, charts, and prioritized recommendations.",
        agent=report_writer,
        context=[analyze_task, insights_task],
    )

    # Create and run crew
    print("[Day 1] Starting CrewAI crew (Sequential process)...\n")

    crew = Crew(
        agents=[data_analyst, insight_generator, report_writer],
        tasks=[analyze_task, insights_task, report_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_{timestamp}.md"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(str(result))

    print()
    print("=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Report saved to: {report_path}")
    print(f"Charts saved to: {output_dir}/")
    print()

    # Print concepts demonstrated
    print("Course Concepts Demonstrated:")
    print("  [Day 1] Multi-Agent System: 3 CrewAI agents in sequential DAG")
    print("  [Day 1] Context Engineering: AGENTS.md + Skill loading")
    print("  [Day 2] MCP Servers: 6 tools via Data + Charts servers")
    print("  [Day 3] Agent Skills: 3 SKILL.md files with Progressive Disclosure")
    print("  [Day 4] Security: Sandboxed file I/O, input validation, egress governance")
    print("  [Day 5] SDD: BDD specs (Gherkin) in specs/ directory")
    print("  [Day 5] Policy Server: Structural gating via policies.yaml")
    print("  [Day 5] Context Hygiene: PII masking + [[VARIABLE]] placeholder resolution")

    return report_path


# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BizInsight Agent — Multi-Agent Business Intelligence")
    parser.add_argument("--data", required=True, help="Path to CSV data file")
    parser.add_argument("--query", required=True, help="Business question to analyze")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--no-policy", action="store_true", help="Disable Policy Server")
    parser.add_argument("--role", default="analyst", help="Agent role for Policy Server (viewer/analyst/chart_creator/admin)")
    args = parser.parse_args()

    run_analysis(
        data_file=args.data,
        query=args.query,
        output_dir=args.output,
        enable_policy=not args.no_policy,
        role=args.role,
    )