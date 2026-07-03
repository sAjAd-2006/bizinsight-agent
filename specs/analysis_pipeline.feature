# Business Analysis Pipeline — BDD Specification
# Day 5: Spec-Driven Development (SDD)
# Format: Gherkin (Given / When / Then) — forces State > Action > Outcome reasoning

Feature: Business Data Analysis Pipeline
  As a business owner
  I want to upload a CSV file and ask a natural language question
  So that I receive a structured report with insights and charts

  # --- Scenario 1: Happy Path — Full Pipeline ---

  Scenario: Analyze sales data and receive a complete report
    Given a CSV file with columns: date, category, product, region, sales, quantity, cost, profit, customer_rating
    And the CSV file is placed in the data/ directory
    And the user provides the query "Analyze sales trends by category"
    When the user runs the BizInsight Agent pipeline
    Then the Data Analyst agent should profile all columns (dtype, null count, unique count)
    And the Data Analyst agent should compute aggregated statistics grouped by category
    And the Data Analyst agent should detect anomalies using the IQR method
    And the Insight Generator agent should produce 3-5 categorized insights
    And each insight should have a title, category, impact rating (high/medium/low), and recommendation
    And the Report Writer agent should produce a markdown report with 7 sections
    And at least one chart should be saved to the output/ directory

  # --- Scenario 2: Anomaly Detection ---

  Scenario: Detect outliers in sales data
    Given a CSV file with numeric sales column containing values [100, 150, 200, 180, 5000]
    When the Data Analyst agent runs anomaly detection on the "sales" column
    Then the IQR bounds should be calculated (Q1=150, Q3=200, IQR=50)
    And the value 5000 should be flagged as an outlier (above Q3 + 1.5*IQR = 275)
    And the anomaly result should include the anomaly count and values

  # --- Scenario 3: Security — Path Traversal Prevention ---

  Scenario: Block access to files outside the data directory
    Given the DATA_DIR is set to the project's data/ directory
    When a tool call requests a file path like "../../etc/passwd"
    Then the path traversal check should reject the request
    And the tool should return "Access denied" without reading the file
    And no file outside DATA_DIR should be accessed

  # --- Scenario 4: Policy Server — Tool Gating ---

  Scenario: Enforce role-based tool access via Policy Server
    Given a policies.yaml configuration with:
      | environment | blocked_tools |
      | localhost  | send_email    |
    And a viewer role that can only use list_files and read_file
    When a viewer agent attempts to use "create_bar_chart"
    Then the Policy Server structural check should deny the request
    And the agent should receive a "Policy Violation" message

  # --- Scenario 5: Context Hygiene — PII Masking ---

  Scenario: Sanitize agent output to prevent PII leakage
    Given an agent template containing "[[CUSTOMER_EMAIL]]"
    And the CUSTOMER_EMAIL environment variable is set to "john@company.com"
    When the ContextResolver processes the template
    Then the placeholder "[[CUSTOMER_EMAIL]]" should be replaced with the env value
    And if the env variable is NOT set, the placeholder should remain unresolved
    And no hardcoded PII should appear in the final agent output

  # --- Scenario 6: Skill Progressive Disclosure ---

  Scenario: Load skill content on demand, not at startup
    Given 3 Agent Skills in skills/ directory: data-analysis, insight-generation, report-writing
    And AGENTS.md contains a skill catalog with trigger keywords (Level 1: metadata)
    When the Data Analyst agent is created
    Then the data-analysis SKILL.md body should be loaded into the agent's backstory (Level 2)
    And the scripts/ and references/ subdirectories should NOT be loaded (Level 3: on-demand)
    And the metadata size should be under 500 characters for context efficiency

  # --- Scenario 7: Evaluation — Behavioral Quality Gate ---

  Scenario: Evaluate agent output quality using scored judgments
    Given the agent pipeline has completed an analysis run
    When the evaluation runner checks the output
    Then the report should contain an executive summary section
    And the report should contain at least 3 findings with data-backed evidence
    And each finding should reference specific metrics (numbers, percentages)
    And the quality score should be at least 3 out of 5