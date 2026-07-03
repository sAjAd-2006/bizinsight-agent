"""
BizInsight Charts MCP Server

Provides tools for generating business charts and saving them as PNG files.
Uses stdio transport (Day 2: MCP Discovery → Configuration → Connection).

Security (Day 4):
- Output files saved only to OUTPUT_DIR (no write outside designated area)
- No outbound network access
- Input validation on all parameters
"""

import json
import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

# --- Configuration ---
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "output"))
OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)

if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

mcp = FastMCP("bizinsight-charts-server")


def _output_path(filename: str) -> str:
    """Validate output filename and return full path."""
    if not filename.endswith(".png"):
        filename = filename.replace(".jpg", ".png").replace(".jpeg", ".png")
        if not filename.endswith(".png"):
            filename = filename + ".png"
    full_path = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    if not full_path.startswith(os.path.abspath(OUTPUT_DIR)):
        raise ValueError("Output path escapes OUTPUT_DIR")
    return full_path


# Suppress matplotlib GUI backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Font setup for clean rendering
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["figure.facecolor"] = "white"


@mcp.tool()
def create_bar_chart(
    data_json: str,
    labels_key: str,
    values_key: str,
    title: str = "Bar Chart",
    x_label: str = "",
    y_label: str = "",
    filename: str = "bar_chart.png",
    color: str = "#4A90D9",
    horizontal: bool = False
) -> str:
    """Create a bar chart from JSON data and save as PNG.

    Args:
        data_json: JSON string of a list of objects, e.g. '[{"name": "A", "value": 10}, ...]'.
        labels_key: Key in each object to use for bar labels.
        values_key: Key in each object to use for bar values.
        title: Chart title.
        x_label: X-axis label.
        y_label: Y-axis label.
        filename: Output filename (saved to output/ directory).
        color: Bar color (hex code).
        horizontal: If True, create horizontal bar chart.
    """
    try:
        data = json.loads(data_json)
        if not isinstance(data, list):
            return json.dumps({"error": "data_json must be a JSON array"})
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in data_json"})

    labels = [str(item.get(labels_key, "")) for item in data]
    values = [float(item.get(values_key, 0)) for item in data]

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)

    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor="white", linewidth=0.5)
        ax.set_ylabel(x_label or labels_key)
        ax.set_xlabel(y_label or values_key)
    else:
        bars = ax.bar(labels, values, color=color, edgecolor="white", linewidth=0.5)
        ax.set_xlabel(x_label or labels_key)
        ax.set_ylabel(y_label or values_key)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(axis="x", rotation=45)

    # Add value labels on bars
    for bar in bars:
        width = bar.get_width() if horizontal else bar.get_height()
        if horizontal:
            ax.text(width + width * 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{width:,.0f}", va="center", fontsize=9)
        else:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + bar.get_height() * 0.01,
                    f"{width:,.0f}", ha="center", va="bottom", fontsize=9)

    out_path = _output_path(filename)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

    return json.dumps({
        "status": "success",
        "chart_type": "bar",
        "file": os.path.basename(out_path),
        "path": out_path,
        "data_points": len(data)
    })


@mcp.tool()
def create_line_chart(
    data_json: str,
    x_key: str,
    y_key: str,
    title: str = "Line Chart",
    x_label: str = "",
    y_label: str = "",
    filename: str = "line_chart.png",
    color: str = "#2ECC71",
    marker: bool = True
) -> str:
    """Create a line chart from JSON data and save as PNG.

    Args:
        data_json: JSON string of a list of objects.
        x_key: Key for x-axis values.
        y_key: Key for y-axis values.
        title: Chart title.
        x_label: X-axis label.
        y_label: Y-axis label.
        filename: Output filename.
        color: Line color.
        marker: Whether to show data point markers.
    """
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in data_json"})

    x_vals = [str(item.get(x_key, "")) for item in data]
    y_vals = [float(item.get(y_key, 0)) for item in data]

    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    ax.plot(x_vals, y_vals, color=color, linewidth=2, marker="o" if marker else None, markersize=5)
    ax.fill_between(range(len(x_vals)), y_vals, alpha=0.1, color=color)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(x_label or x_key)
    ax.set_ylabel(y_label or y_key)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)

    out_path = _output_path(filename)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

    return json.dumps({
        "status": "success",
        "chart_type": "line",
        "file": os.path.basename(out_path),
        "path": out_path,
        "data_points": len(data)
    })


@mcp.tool()
def create_pie_chart(
    data_json: str,
    labels_key: str,
    values_key: str,
    title: str = "Pie Chart",
    filename: str = "pie_chart.png"
) -> str:
    """Create a pie chart from JSON data and save as PNG.

    Args:
        data_json: JSON string of a list of objects.
        labels_key: Key for slice labels.
        values_key: Key for slice values.
        title: Chart title.
        filename: Output filename.
    """
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in data_json"})

    labels = [str(item.get(labels_key, "")) for item in data]
    values = [float(item.get(values_key, 0)) for item in data]

    fig, ax = plt.subplots(figsize=(8, 8), constrained_layout=True)

    colors = ["#4A90D9", "#2ECC71", "#E74C3C", "#F39C12", "#9B59B6",
              "#1ABC9C", "#E67E22", "#3498DB", "#E91E63", "#00BCD4"]

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct="%1.1f%%", startangle=90,
        colors=colors[:len(values)], pctdistance=0.75
    )
    for text in texts:
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    out_path = _output_path(filename)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

    return json.dumps({
        "status": "success",
        "chart_type": "pie",
        "file": os.path.basename(out_path),
        "path": out_path,
        "data_points": len(data)
    })


@mcp.tool()
def create_heatmap(
    data_json: str,
    row_key: str,
    col_key: str,
    value_key: str,
    title: str = "Heatmap",
    filename: str = "heatmap.png",
    cmap: str = "YlOrRd"
) -> str:
    """Create a heatmap from pivoted JSON data and save as PNG.

    Args:
        data_json: JSON string of a list of objects with row, column, and value keys.
        row_key: Key for row labels.
        col_key: Key for column labels.
        value_key: Key for cell values.
        title: Chart title.
        filename: Output filename.
        cmap: Matplotlib colormap name.
    """
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in data_json"})

    import pandas as pd
    df = pd.DataFrame(data)
    try:
        pivot = df.pivot_table(index=row_key, columns=col_key, values=value_key, aggfunc="sum", fill_value=0)
    except Exception as e:
        return json.dumps({"error": f"Could not create pivot table: {str(e)}"})

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    import seaborn as sns
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap=cmap, ax=ax, linewidths=0.5)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    out_path = _output_path(filename)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

    return json.dumps({
        "status": "success",
        "chart_type": "heatmap",
        "file": os.path.basename(out_path),
        "path": out_path,
        "rows": len(pivot),
        "cols": len(pivot.columns)
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")