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
from typing import Optional, Any
from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import crewai
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool


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
    class PolicyGuardedTool(BaseTool):
        name: str = tool.name + "_guarded"
        description: str = tool.description + " [Policy-guarded: checked before execution]"
        args_schema: type[BaseModel] = tool.args_schema  # حفظ schema اصلی

        def _run(self, **kwargs) -> str:
            # Day 5: Structural Gating — check before execution
            if not policy_service.is_tool_allowed(tool.name):
                return json.dumps({"error": policy_service.get_violation_message(tool.name)})
            return tool._run(**kwargs)

    return PolicyGuardedTool()


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

# ---------- Pydantic Schemas for Tools ----------

class ReadCSVInput(BaseModel):
    filename: str = Field(..., description="Name of the CSV file in the data directory")
    max_rows: int = Field(100, description="Maximum number of rows to return (1-500)")

class GetColumnsInput(BaseModel):
    filename: str = Field(..., description="Name of the CSV file in the data directory")

class ComputeAggregateInput(BaseModel):
    filename: str = Field(..., description="Name of the CSV file")
    group_by: str = Field(..., description="Column to group by")
    metric_column: str = Field(..., description="Numeric column to aggregate")
    aggregation: str = Field("sum", description="Aggregation function: sum/mean/median/min/max/count")

class DetectAnomaliesInput(BaseModel):
    filename: str = Field(..., description="Name of the CSV file")
    column: str = Field(..., description="Numeric column to check for anomalies")
    method: str = Field("iqr", description="Method: iqr or zscore")
    filter_column: Optional[str] = Field(None, description="Optional column to filter rows")
    filter_value: Optional[str] = Field(None, description="Optional value to filter on")

class ComputeKeyMetricsInput(BaseModel):
    filename: str = Field(..., description="Name of the CSV file")
    sales_col: str = Field("sales", description="Name of the sales/numeric column")
    category_col: str = Field("category", description="Name of the category column")
    region_col: str = Field("region", description="Name of the region column")
    product_col: str = Field("product", description="Name of the product column")

class CreateBarChartInput(BaseModel):
    data_json: str = Field(..., description="JSON array of objects with labels and values")
    labels_key: str = Field(..., description="Key in each object for the label")
    values_key: str = Field(..., description="Key in each object for the value")
    title: str = Field("Bar Chart", description="Chart title")
    filename: str = Field("bar_chart.png", description="Output filename")

class CreateLineChartInput(BaseModel):
    data_json: str = Field(..., description="JSON array of objects with x and y values")
    x_key: str = Field(..., description="Key for x-axis values")
    y_key: str = Field(..., description="Key for y-axis values")
    title: str = Field("Line Chart", description="Chart title")
    filename: str = Field("line_chart.png", description="Output filename")

class PrepareChartDataInput(BaseModel):
    metrics_json: str = Field(..., description="Full JSON output from compute_key_metrics")
    group_by: str = Field("category", description="Group by: category, region, or product")


# ---------- Tool Implementations ----------

def create_mcp_tools():
    """
    Create CrewAI-compatible tool wrappers for MCP servers.
    Demonstrates Day 2: MCP as the 'USB-C' for agent tools.
    """
    import pandas as pd
    import numpy as np

    DATA_DIR = os.environ.get("DATA_DIR", str(PROJECT_ROOT / "data"))
    OUTPUT_DIR = os.environ.get("OUTPUT_DIR", str(PROJECT_ROOT / "output"))
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Data Tools ---

    class ReadCSVTool(BaseTool):
        name: str = "read_csv"
        description: str = "Read a CSV file and return first N rows as JSON."
        args_schema: type[BaseModel] = ReadCSVInput

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
        description: str = "Get column names, data types, null counts, and unique values."
        args_schema: type[BaseModel] = GetColumnsInput

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
        description: str = "Compute aggregated statistics grouped by a column."
        args_schema: type[BaseModel] = ComputeAggregateInput

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
        description: str = "Detect outliers in a numeric column using IQR method."
        args_schema: type[BaseModel] = DetectAnomaliesInput

        def _run(self, filename: str, column: str, method: str = "iqr",
                  filter_column: Optional[str] = None, filter_value: Optional[str] = None) -> str:
            path = os.path.abspath(os.path.join(DATA_DIR, filename))
            if not path.startswith(os.path.abspath(DATA_DIR)):
                return json.dumps({"error": "Access denied"})
            df = pd.read_csv(path)
            if column not in df.columns:
                return json.dumps({"error": "Column not found"})
            if filter_column and filter_value:
                if filter_column not in df.columns:
                    return json.dumps({"error": f"Filter column '{filter_column}' not found"})
                mask = df[filter_column].astype(str).str.lower() == filter_value.lower()
                df = df[mask]
                if len(df) == 0:
                    return json.dumps({"error": f"No rows match {filter_column}={filter_value}", "anomaly_count": 0, "anomaly_values": []})
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if len(series) < 4:
                return json.dumps({"error": "Too few data points for IQR (need >= 4)", "anomaly_count": 0, "anomaly_values": []})
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (series < lower) | (series > upper)
            return json.dumps({
                "method": "IQR", "column": column,
                "filter_column": filter_column or None,
                "filter_value": filter_value or None,
                "rows_analyzed": int(len(series)),
                "q1": float(q1), "q3": float(q3), "iqr": float(iqr),
                "lower_bound": float(lower), "upper_bound": float(upper),
                "anomaly_count": int(mask.sum()),
                "anomaly_values": series[mask].tolist()
            })

    class ComputeKeyMetricsTool(BaseTool):
        name: str = "compute_key_metrics"
        description: str = "Pre-compute all key business metrics from a CSV file."
        args_schema: type[BaseModel] = ComputeKeyMetricsInput

        def _run(self, filename: str, sales_col: str = "sales", category_col: str = "category",
                 region_col: str = "region", product_col: str = "product") -> str:
            path = os.path.abspath(os.path.join(DATA_DIR, filename))
            if not path.startswith(os.path.abspath(DATA_DIR)):
                return json.dumps({"error": "Access denied"})
            df = pd.read_csv(path)
            # Validate columns exist
            for col in [sales_col, category_col, region_col, product_col]:
                if col not in df.columns:
                    return json.dumps({"error": f"Column '{col}' not found in data"})
            df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
            total_sales = float(df[sales_col].sum())
            total_rows = len(df)

            cat_group = df.groupby(category_col)[sales_col].sum()
            categories = []
            for cat, val in cat_group.sort_values(ascending=False).items():
                categories.append({
                    "category": cat,
                    "total_sales": float(val),
                    "share_pct": round(float(val) / total_sales * 100, 1),
                    "num_records": int(len(df[df[category_col] == cat]))
                })

            reg_group = df.groupby(region_col)[sales_col].sum()
            regions = []
            for reg, val in reg_group.sort_values(ascending=False).items():
                regions.append({
                    "region": reg,
                    "total_sales": float(val),
                    "share_pct": round(float(val) / total_sales * 100, 1),
                    "num_records": int(len(df[df[region_col] == reg]))
                })

            prod_group = df.groupby(df[product_col].str.lower())[sales_col].agg(["mean", "median", "sum", "count"])
            products = []
            for prod, row in prod_group.sort_values("sum", ascending=False).iterrows():
                products.append({
                    "product": prod,
                    "mean_sales": round(float(row["mean"]), 1),
                    "median_sales": round(float(row["median"]), 1),
                    "total_sales": round(float(row["sum"]), 1),
                    "num_records": int(row["count"])
                })

            return json.dumps({
                "total_sales": total_sales,
                "total_rows": total_rows,
                "categories": categories,
                "regions": regions,
                "products": products
            }, indent=2)

    # --- Charts Tools (still defined but not given to report_writer) ---

    class CreateBarChartTool(BaseTool):
        name: str = "create_bar_chart"
        description: str = "Create a bar chart from JSON data and save as PNG."
        args_schema: type[BaseModel] = CreateBarChartInput

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
        description: str = "Create a line chart from JSON data and save as PNG."
        args_schema: type[BaseModel] = CreateLineChartInput

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

    class PrepareChartDataTool(BaseTool):
        name: str = "prepare_chart_data"
        description: str = "Extract chart-ready data from compute_key_metrics JSON output."
        args_schema: type[BaseModel] = PrepareChartDataInput

        def _run(self, metrics_json: str, group_by: str = "category") -> str:
            try:
                data = json.loads(metrics_json)
            except:
                return json.dumps({"error": "Invalid JSON input"})
            if group_by == "category":
                items = data.get("categories", [])
                label_key = "category"
                value_key = "total_sales"
            elif group_by == "region":
                items = data.get("regions", [])
                label_key = "region"
                value_key = "total_sales"
            elif group_by == "product":
                items = data.get("products", [])
                label_key = "product"
                value_key = "total_sales"
            else:
                return json.dumps({"error": f"Unknown group_by: {group_by}"})
            result = [{"label": item[label_key], "value": item[value_key]} for item in items]
            return json.dumps(result)

    # Return all tools including chart tools, but report_writer will not be given chart tools.
    return [
        ReadCSVTool(), GetColumnsTool(), ComputeAggregateTool(),
        DetectAnomaliesTool(), ComputeKeyMetricsTool(), PrepareChartDataTool(),
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

    # Load Skills
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
        tools=active_tools,  # data analyst gets all tools
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

    # Report Writer has NO chart tools (as per user's previous request)
    report_writer = Agent(
        role=agent_configs["report_writer"]["role"],
        goal=agent_configs["report_writer"]["goal"],
        backstory=agent_configs["report_writer"]["backstory"]
            + f"\n\n## Your Skill (follow this template):\n{report_skill}",
        tools=[],   # No tools at all, so it cannot generate charts
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
    
    print(f"🤖 BizInsight Agent: I'll analyze your data to answer your query: '{query}'")
    
    os.makedirs(output_dir, exist_ok=True)

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    from crewai import LLM
    import pandas as pd

    model_name = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")
    base_url = os.environ.get("OPTIONAL_BASE_URL", "https://openrouter.ai/api/v1")

    llm = LLM(
        model=f"{model_name}", 
        api_key=api_key,
        base_url=base_url
    )

    policy_service = None
    if enable_policy:
        print("\n🔒 Initializing Policy Server (Zero-Trust Security)...")
        policy_service = create_policy_service(role=role)
        allowed = policy_service.list_allowed_tools()
        print(f"   Role: {role} | Allowed tools: {allowed}")

    print("\n📊 Step 1: Data Analyst Agent loading data via MCP Data Server...")
    
    # ---------- DYNAMIC COLUMN DETECTION ----------
    try:
        df_temp = pd.read_csv(data_file)
        # Detect numeric column (likely sales)
        numeric_cols = df_temp.select_dtypes(include=['number']).columns.tolist()
        # Try to find a column with 'sales' or 'revenue' in name, else use first numeric
        sales_col_candidates = [c for c in numeric_cols if any(k in c.lower() for k in ['sales', 'revenue', 'amount'])]
        sales_col = sales_col_candidates[0] if sales_col_candidates else numeric_cols[0] if numeric_cols else None
        
        # Detect categorical columns for category, region, product
        cat_cols = df_temp.select_dtypes(include=['object']).columns.tolist()
        # Map based on common names
        category_col = next((c for c in cat_cols if 'category' in c.lower()), cat_cols[0] if cat_cols else None)
        region_col = next((c for c in cat_cols if 'region' in c.lower()), cat_cols[1] if len(cat_cols) > 1 else None)
        product_col = next((c for c in cat_cols if 'product' in c.lower()), cat_cols[-1] if cat_cols else None)
        
        # Fallbacks if detection fails
        if sales_col is None:
            raise ValueError("No numeric column found in data")
        if category_col is None:
            category_col = cat_cols[0] if cat_cols else None
        if region_col is None:
            region_col = cat_cols[1] if len(cat_cols) > 1 else None
        if product_col is None:
            product_col = cat_cols[-1] if cat_cols else None

        # Choose a target product for anomaly detection (top selling product)
        # Group by product_col and sum sales_col to find the top product
        if product_col and sales_col:
            product_sales = df_temp.groupby(product_col)[sales_col].sum()
            if not product_sales.empty:
                target_product = product_sales.idxmax()
            else:
                target_product = "unknown"
        else:
            target_product = "unknown"

        print(f"✅ Detected columns: sales='{sales_col}', category='{category_col}', region='{region_col}', product='{product_col}'")
        print(f"   Target product for anomaly detection: '{target_product}'")
        
    except Exception as e:
        print(f"⚠️ Error detecting columns: {e}")
        # Fallback to defaults
        sales_col = "sales"
        category_col = "category"
        region_col = "region"
        product_col = "product"
        target_product = "Smart Watch"
        print(f"   Using default column names: sales='{sales_col}', category='{category_col}', region='{region_col}', product='{product_col}'")
        print(f"   Target product: '{target_product}'")

    # ---------- END DYNAMIC COLUMN DETECTION ----------

    tools = create_mcp_tools()

    orchestrator, data_analyst, insight_generator, report_writer = create_agents(
        tools, llm, policy_service=policy_service
    )

    filename_only = os.path.basename(data_file)

    # ---------- DYNAMIC TASK DESCRIPTIONS ----------
    analyze_task_description = (
        f"Analyze the business data in '{filename_only}' to answer: {query}. "
        f"Follow this exact sequence — do NOT skip steps or compute numbers in your head:\n"
        f"Step 1: Use get_columns with filename='{filename_only}'.\n"
        f"Step 2: Use compute_key_metrics with filename='{filename_only}', "
        f"sales_col='{sales_col}', category_col='{category_col}', region_col='{region_col}', product_col='{product_col}' "
        f"to get pre-computed totals, category shares, regional shares, and product averages. "
        f"USE THESE EXACT NUMBERS — do not recalculate.\n"
        f"Step 3: Use compute_aggregate with filename='{filename_only}' for any additional groupings needed.\n"
        f"Step 4: Use detect_anomalies with filename='{filename_only}', column='{sales_col}', "
        f"filter_column='{product_col}', filter_value='{target_product}' to check anomalies FOR THAT PRODUCT ONLY (not the whole dataset).\n"
        f"Step 5: Compile ALL tool outputs into a single structured JSON.\n"
        f"CRITICAL: All percentages, means, and totals must come directly from tool output. "
        f"Never compute share_pct = category_sales / total_sales yourself — the tool already provides it."
    )

    analyze_task = Task(
        description=analyze_task_description,
        expected_output="Structured JSON containing: key_metrics (from compute_key_metrics tool), "
                    "column profiles (from get_columns), anomaly results (from detect_anomalies with filter). "
                    "All numbers must be verbatim from tool output — no self-computed arithmetic.",
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

    report_task_description = (
        f"Write a professional markdown report. Data source: {data_file}. Query: {query}. "
        f"Today's date: {datetime.now().strftime('%B %d, %Y')}. Follow the report-writing skill template.\n\n"
        f"STRUCTURE:\n"
        f"1. Header: 'Date of Generation: {datetime.now().strftime('%B %d, %Y')}' (use THIS exact date, not any other date)\n"
        f"2. Executive Summary: 5 bullets, each with an EXACT number from the analysis results\n"
        f"3. Data Overview: row count (use the exact 'total_rows' from compute_key_metrics output, do NOT hardcode it), "
        f"date range, categories, regions\n"
        f"4. Key Findings: for each finding, quote the EXACT metric from the tool output — do NOT recalculate\n"
        f"5. Detailed Analysis\n"
        f"6. Recommendations\n"
        f"7. Appendix\n\n"
        f"CRITICAL RULES:\n"
        f"- Use the EXACT date provided above. NEVER fabricate a date.\n"
        f"- Every percentage must come verbatim from compute_key_metrics output (share_pct field).\n"
        f"- Every average must come verbatim from compute_key_metrics output (mean_sales field).\n"
        f"- Every anomaly count must come verbatim from detect_anomalies output (anomaly_count field).\n"
        f"- If the anomaly_count is 0 for a product, say 'No anomalies detected' — do NOT claim anomalies exist.\n"
        f"- You have access to the outputs of previous tasks via context. Use them to extract numbers.\n"
    )

    report_task = Task(
        description=report_task_description,
        expected_output="Complete markdown report with executive summary, data overview, key findings, detailed analysis, and recommendations.",
        agent=report_writer,
        context=[analyze_task, insights_task],
    )

    # ---------- END DYNAMIC TASK DESCRIPTIONS ----------

    print("\n🔍 Step 2: Performing statistical analysis (IQR anomaly detection)...")
    print("💡 Step 3: Insight Generator Agent transforming raw data into business insights...")
    print("📝 Step 4: Report Writer Agent generating final report...")

    crew = Crew(
        agents=[data_analyst, insight_generator, report_writer],
        tasks=[analyze_task, insights_task, report_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    import re
    slug = re.sub(r'[^a-z0-9]+', '_', query.lower()).strip('_')[:50]
    if not slug:
        slug = "analysis_report"
    report_filename = f"{slug}.md"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(str(result))

    # No charts generated, just a notice
    print("ℹ️ No chart files generated (as per configuration).")
    print("\n✅ Report successfully saved to: {report_path}")

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