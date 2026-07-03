# Statistical Methods Reference
# Day 3: Skill Level 3 — References (loaded on-demand)

## IQR Method (Interquartile Range)
- Robust to outliers, does not assume normal distribution
- Q1 = 25th percentile, Q3 = 75th percentile
- IQR = Q3 - Q1
- Outlier bounds: below Q1 - 1.5*IQR or above Q3 + 1.5*IQR

## Z-Score Method
- Assumes approximately normal distribution
- Z = (x - mean) / std
- Outlier threshold: |Z| > 2 (common) or |Z| > 3 (strict)

## When to Use Which
- **IQR**: Use when data is skewed or has extreme outliers (business data often is)
- **Z-Score**: Use when data is approximately normally distributed

## Correlation Interpretation
- |r| > 0.7: Strong correlation
- 0.4 < |r| < 0.7: Moderate correlation
- |r| < 0.4: Weak correlation
- Note: Correlation does not imply causation