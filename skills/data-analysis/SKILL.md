---
name: data-analysis
version: 1.0.0
description: >-
  Use when the user asks to analyze data, compute statistics, detect trends, or profile columns.
  Trigger on: analyze, statistics, trend, anomaly, profile, explore data.
  Do NOT use for generating reports, writing documents, or creating visualizations.
---

# Data Analysis Skill

## Methodology

Follow this 5-step analysis pipeline sequentially:

### Step 1: Column Profiling
- Identify all columns and their data types (numeric, categorical, datetime)
- Count missing values per column
- Determine cardinality of categorical columns
- Report basic shape of the dataset (rows × columns)

### Step 2: Descriptive Statistics
- For numeric columns: mean, median, std, min, max, quartiles (Q1, Q3)
- For categorical columns: mode, unique count, frequency distribution (top 5)
- For datetime columns: date range, frequency, gaps

### Step 3: Trend Analysis
- Group data by meaningful time periods (daily, weekly, monthly, quarterly)
- Calculate period-over-period changes (absolute and percentage)
- Identify upward, downward, or stable trends
- Note any seasonal patterns

### Step 4: Anomaly Detection
- Identify outliers using IQR method (values below Q1 - 1.5×IQR or above Q3 + 1.5×IQR)
- Flag statistical anomalies (values beyond 2 standard deviations from mean)
- Check for data quality issues: negative values where unexpected, impossible dates

### Step 5: Correlation Analysis
- Compute pairwise correlations between numeric columns
- Identify strong correlations (|r| > 0.7)
- Note any counter-intuitive correlations
- Suggest causal hypotheses for strong correlations

## Output Format

Present findings as a structured analysis with:
- Executive summary (3-5 bullet points)
- Detailed findings per step
- Key metrics table
- Flags and warnings

## Tools Used
- `read_csv` - Load dataset
- `get_columns` - Inspect column structure
- `filter_rows` - Subset data for segmented analysis
- `compute_aggregate` - Calculate statistics
- `detect_anomalies` - Find outliers