"""
BizInsight Data MCP Server

Provides tools for reading, filtering, and analyzing CSV business data.
Uses stdio transport (Day 2: MCP Discovery → Configuration → Connection).

Security (Day 4):
- File access scoped to DATA_DIR environment variable (default: ./data)
- Read-only access — no file modification tools
- Input validation on all tool parameters
- No outbound network access (Pillar 1: Egress Governance)
"""

import json
import os
import sys
from typing import Any

import pandas as pd
import numpy as np
from mcp.server.fastmcp import FastMCP

# --- Configuration ---
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DATA_DIR = os.path.abspath(DATA_DIR)

# Security: Ensure DATA_DIR exists and is a directory
if not os.path.isdir(DATA_DIR):
    print(f"Warning: DATA_DIR '{DATA_DIR}' does not exist. Creating it.", file=sys.stderr)
    os.makedirs(DATA_DIR, exist_ok=True)

# Create MCP server
mcp = FastMCP("bizinsight-data-server")


def _safe_path(filename: str) -> str:
    """Validate and resolve file path to prevent directory traversal (Day 4: Zero Ambient Authority)."""
    if not filename.endswith(".csv"):
        raise ValueError(f"Only .csv files are allowed. Got: {filename}")
    full_path = os.path.abspath(os.path.join(DATA_DIR, filename))
    if not full_path.startswith(os.path.abspath(DATA_DIR)):
        raise ValueError(f"Access denied: path escapes DATA_DIR")
    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"File not found: {filename}")
    return full_path


# ============================================================
# MCP Tools
# ============================================================

@mcp.tool()
def read_csv(filename: str, max_rows: int = 100) -> str:
    """Read a CSV file from the data directory and return its contents as JSON.

    Args:
        filename: Name of the CSV file (must be in the data/ directory).
        max_rows: Maximum number of rows to return (default: 100, max: 500).
    """
    max_rows = min(max(1, max_rows), 500)
    path = _safe_path(filename)
    df = pd.read_csv(path)
    result = df.head(max_rows).to_json(orient="records", date_format="iso")
    return json.dumps({
        "rows_returned": min(len(df), max_rows),
        "total_rows": len(df),
        "columns": list(df.columns),
        "data": json.loads(result)
    }, indent=2)


@mcp.tool()
def get_columns(filename: str) -> str:
    """Get column names, data types, and basic statistics for a CSV file.

    Args:
        filename: Name of the CSV file.
    """
    path = _safe_path(filename)
    df = pd.read_csv(path)
    info = []
    for col in df.columns:
        info.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "unique_count": int(df[col].nunique()),
            "sample_values": df[col].dropna().head(3).tolist()
        })
    return json.dumps({
        "total_columns": len(df.columns),
        "total_rows": len(df),
        "columns": info
    }, indent=2)


@mcp.tool()
def filter_rows(
    filename: str,
    column: str,
    operator: str,
    value: str
) -> str:
    """Filter rows in a CSV file based on a column condition.

    Args:
        filename: Name of the CSV file.
        column: Column name to filter on.
        operator: Comparison operator - one of: 'eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'contains'.
        value: Value to compare against (as string, will be converted to numeric if possible).
    """
    path = _safe_path(filename)
    df = pd.read_csv(path)

    if column not in df.columns:
        return json.dumps({"error": f"Column '{column}' not found. Available: {list(df.columns)}"})

    valid_ops = {"eq", "ne", "gt", "gte", "lt", "lte", "contains"}
    if operator not in valid_ops:
        return json.dumps({"error": f"Invalid operator '{operator}'. Must be one of: {valid_ops}"})

    # Try numeric conversion
    try:
        numeric_val = float(value)
        col_series = pd.to_numeric(df[column], errors="coerce")
    except (ValueError, TypeError):
        numeric_val = None
        col_series = df[column]

    if operator == "eq":
        mask = (col_series == numeric_val) if numeric_val is not None else (df[column].astype(str) == value)
    elif operator == "ne":
        mask = (col_series != numeric_val) if numeric_val is not None else (df[column].astype(str) != value)
    elif operator == "gt":
        mask = col_series > numeric_val
    elif operator == "gte":
        mask = col_series >= numeric_val
    elif operator == "lt":
        mask = col_series < numeric_val
    elif operator == "lte":
        mask = col_series <= numeric_val
    elif operator == "contains":
        mask = df[column].astype(str).str.contains(value, case=False, na=False)

    filtered = df[mask]
    return json.dumps({
        "filter": f"{column} {operator} {value}",
        "matching_rows": len(filtered),
        "total_rows": len(df),
        "data": filtered.head(100).to_json(orient="records", date_format="iso")
    }, indent=2)


@mcp.tool()
def compute_aggregate(
    filename: str,
    group_by: str,
    metric_column: str,
    aggregation: str = "sum"
) -> str:
    """Compute aggregated statistics grouped by a column.

    Args:
        filename: Name of the CSV file.
        group_by: Column to group by.
        metric_column: Numeric column to aggregate.
        aggregation: Aggregation type - 'sum', 'mean', 'median', 'min', 'max', 'count'.
    """
    path = _safe_path(filename)
    df = pd.read_csv(path)

    valid_aggs = {"sum", "mean", "median", "min", "max", "count"}
    if aggregation not in valid_aggs:
        return json.dumps({"error": f"Invalid aggregation '{aggregation}'. Must be one of: {valid_aggs}"})

    if group_by not in df.columns:
        return json.dumps({"error": f"Column '{group_by}' not found."})
    if metric_column not in df.columns:
        return json.dumps({"error": f"Column '{metric_column}' not found."})

    df[metric_column] = pd.to_numeric(df[metric_column], errors="coerce")
    grouped = df.groupby(group_by)[metric_column].agg(aggregation).reset_index()
    grouped.columns = [group_by, f"{aggregation}_of_{metric_column}"]
    grouped = grouped.sort_values(f"{aggregation}_of_{metric_column}", ascending=False)

    return json.dumps({
        "group_by": group_by,
        "metric": metric_column,
        "aggregation": aggregation,
        "groups": len(grouped),
        "result": grouped.to_json(orient="records")
    }, indent=2)


@mcp.tool()
def detect_anomalies(filename: str, column: str, method: str = "iqr") -> str:
    """Detect anomalies (outliers) in a numeric column.

    Args:
        filename: Name of the CSV file.
        column: Numeric column to analyze.
        method: Detection method - 'iqr' (Interquartile Range) or 'zscore' (Z-Score).
    """
    path = _safe_path(filename)
    df = pd.read_csv(path)

    if column not in df.columns:
        return json.dumps({"error": f"Column '{column}' not found."})

    series = pd.to_numeric(df[column], errors="coerce").dropna()

    if method == "iqr":
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (series < lower) | (series > upper)
        anomalies = series[mask]
        return json.dumps({
            "method": "IQR",
            "column": column,
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(iqr),
            "lower_bound": float(lower),
            "upper_bound": float(upper),
            "anomaly_count": int(mask.sum()),
            "anomaly_values": anomalies.tolist(),
            "anomaly_indices": mask[mask].index.tolist()
        }, indent=2)

    elif method == "zscore":
        mean = series.mean()
        std = series.std()
        if std == 0:
            return json.dumps({"method": "zscore", "anomaly_count": 0, "note": "Standard deviation is zero"})
        z_scores = ((series - mean) / std).abs()
        mask = z_scores > 2.0
        anomalies = series[mask]
        return json.dumps({
            "method": "Z-Score",
            "column": column,
            "mean": float(mean),
            "std": float(std),
            "threshold": 2.0,
            "anomaly_count": int(mask.sum()),
            "anomaly_values": anomalies.tolist(),
            "anomaly_indices": mask[mask].index.tolist()
        }, indent=2)

    else:
        return json.dumps({"error": "Method must be 'iqr' or 'zscore'"})


if __name__ == "__main__":
    mcp.run(transport="stdio")