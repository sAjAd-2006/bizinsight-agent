---
name: insight-generation
version: 1.0.0
description: >-
  Use when the user asks for insights, key findings, recommendations, or actionable takeaways.
  Trigger on: insights, findings, patterns, recommendations, actionable.
  Do NOT use for raw data analysis, statistical computation, or chart generation.
---

# Insight Generation Skill

## Insight Frameworks

Apply the following frameworks to extract insights from analysis results:

### 1. Pareto Insight (80/20 Analysis)
- Identify the vital few factors driving the majority of outcomes
- Example: "20% of products generate 80% of revenue"
- Quantify the concentration ratio

### 2. Growth Pattern Insight
- Identify segments with highest/lowest growth rates
- Calculate compound growth rates where applicable
- Distinguish between one-time spikes and sustained trends
- Format: "[Segment] grew [X]% over [period], driven by [cause]"

### 3. Gap Analysis Insight
- Compare actual performance against benchmarks or targets
- Identify the largest performance gaps
- Quantify the opportunity cost of gaps
- Format: "[Metric] is [X]% below [benchmark], representing [value] in missed opportunity"

### 4. Anomaly Narration
- Transform statistical anomalies into business narratives
- Propose plausible business explanations for anomalies
- Assess whether anomalies are positive or negative signals
- Format: "Unusual [event] in [period] — [possible cause], [impact assessment]"

### 5. Correlation Insight
- Translate statistical correlations into business relationships
- Distinguish correlation from causation
- Identify leverage points for intervention
- Format: "[Variable A] and [Variable B] show [strength] correlation ([r=X]), suggesting [business implication]"

## Impact Prioritization

Rate each insight on three dimensions:

| Dimension | High | Medium | Low |
|-----------|------|--------|-----|
| Financial Impact | > 20% revenue/cost change | 5-20% change | < 5% change |
| Actionability | Clear next steps exist | Some investigation needed | Informational only |
| Urgency | Time-sensitive window | Important but not urgent | Long-term consideration |

## Output Format

For each insight provide:
1. **Finding**: One-sentence description
2. **Evidence**: Supporting data points
3. **Impact**: High/Medium/Low with rationale
4. **Recommendation**: Specific action to take