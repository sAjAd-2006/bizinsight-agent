# Statistical Analysis Functions
# Day 3: Skill Level 3 — Scripts (loaded on-demand)

import pandas as pd
import numpy as np


def compute_iqr_bounds(series: pd.Series):
    """Compute IQR-based outlier bounds for a numeric series."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return {"q1": q1, "q3": q3, "iqr": iqr, "lower": lower, "upper": upper}


def compute_zscore_bounds(series: pd.Series, threshold: float = 2.0):
    """Compute Z-score-based outlier bounds."""
    mean = series.mean()
    std = series.std()
    lower = mean - threshold * std
    upper = mean + threshold * std
    return {"mean": mean, "std": std, "lower": lower, "upper": upper}


def period_over_period_change(series: pd.Series, periods: int = 1):
    """Calculate period-over-period absolute and percentage change."""
    abs_change = series.diff(periods=periods)
    pct_change = series.pct_change(periods=periods) * 100
    return pd.DataFrame({"value": series, "abs_change": abs_change, "pct_change": pct_change})


def compute_correlation_matrix(df: pd.DataFrame, numeric_only: bool = True):
    """Compute pairwise correlation matrix for numeric columns."""
    return df.corr(numeric_only=numeric_only)