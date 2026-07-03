"""
Tests for CrewAI multi-agent system (Day 1).
Verifies agent creation, task definitions, and pipeline structure.
"""

import os
import sys
import pytest
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestAgentConfig:
    """Day 1: Verify agent configurations are well-defined."""

    def test_agents_yaml_exists(self):
        """Agent config file exists."""
        path = os.path.join(PROJECT_ROOT, "crew", "config", "agents.yaml")
        assert os.path.isfile(path)

    def test_all_agents_defined(self):
        """All 4 agents are present in config."""
        path = os.path.join(PROJECT_ROOT, "crew", "config", "agents.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        expected = ["orchestrator", "data_analyst", "insight_generator", "report_writer"]
        for agent in expected:
            assert agent in config, f"Missing agent: {agent}"

    def test_each_agent_has_required_fields(self):
        """Each agent must have role, goal, and backstory."""
        path = os.path.join(PROJECT_ROOT, "crew", "config", "agents.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        for name, agent in config.items():
            assert "role" in agent, f"Agent '{name}' missing 'role'"
            assert "goal" in agent, f"Agent '{name}' missing 'goal'"
            assert "backstory" in agent, f"Agent '{name}' missing 'backstory'"
            assert len(agent["backstory"]) > 50, f"Agent '{name}' backstory too short"

    def test_tasks_yaml_exists(self):
        """Task config file exists."""
        path = os.path.join(PROJECT_ROOT, "crew", "config", "tasks.yaml")
        assert os.path.isfile(path)

    def test_tasks_have_placeholders(self):
        """Tasks use {placeholder} for dynamic values."""
        path = os.path.join(PROJECT_ROOT, "crew", "config", "tasks.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert "{data_file}" in config["analyze_data_task"]["description"]
        assert "{query}" in config["analyze_data_task"]["description"]


class TestPipelineStructure:
    """Verify the multi-agent pipeline follows a DAG (Day 3)."""

    def test_task_dependencies_form_dag(self):
        """Tasks should form a directed acyclic graph.
        analyze_data → generate_insights → write_report
        """
        # This is verified by the context parameter in main.py
        # analyze_task has no context (root)
        # insights_task has context=[analyze_task]
        # report_task has context=[analyze_task, insights_task]
        main_path = os.path.join(PROJECT_ROOT, "main.py")
        with open(main_path) as f:
            code = f.read()
        # Verify DAG structure in task definitions
        assert "context=[analyze_task]" in code
        assert "context=[analyze_task, insights_task]" in code


class TestAGENTSmd:
    """Day 1: Verify AGENTS.md provides proper context engineering."""

    def test_agents_md_exists(self):
        """AGENTS.md must exist at project root."""
        path = os.path.join(PROJECT_ROOT, "AGENTS.md")
        assert os.path.isfile(path)

    def test_agents_md_has_skill_catalog(self):
        """AGENTS.md should list available skills for routing."""
        path = os.path.join(PROJECT_ROOT, "AGENTS.md")
        with open(path) as f:
            content = f.read()
        assert "Available Skills" in content or "skills" in content.lower()
        assert "data-analysis" in content
        assert "insight-generation" in content
        assert "report-writing" in content

    def test_agents_md_has_mcp_servers(self):
        """AGENTS.md should list MCP servers."""
        path = os.path.join(PROJECT_ROOT, "AGENTS.md")
        with open(path) as f:
            content = f.read()
        assert "MCP" in content
        assert "Data Server" in content
        assert "Charts Server" in content


class TestProjectStructure:
    """Verify the overall project structure is complete."""

    def test_readme_exists(self):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "README.md"))

    def test_requirements_exists(self):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "requirements.txt"))

    def test_main_exists(self):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "main.py"))

    def test_sample_data_exists(self):
        path = os.path.join(PROJECT_ROOT, "data", "sample_business_data.csv")
        assert os.path.isfile(path)

    def test_mcp_servers_exist(self):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "mcp_servers", "data_server", "server.py"))
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "mcp_servers", "charts_server", "server.py"))

    def test_concept_documentation(self):
        """README should map to course concepts."""
        path = os.path.join(PROJECT_ROOT, "README.md")
        with open(path) as f:
            content = f.read()
        # Should reference all 5 days
        assert "Day 1" in content
        assert "Day 2" in content
        assert "Day 3" in content
        assert "Day 4" in content
        assert "Day 5" in content

    def test_specs_directory_exists(self):
        """Day 5: SDD requires a specs/ directory."""
        assert os.path.isdir(os.path.join(PROJECT_ROOT, "specs"))

    def test_policy_server_exists(self):
        """Day 5: Policy Server file should exist."""
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "policy_server.py"))

    def test_context_resolver_exists(self):
        """Day 5: Context Resolver file should exist."""
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "context_resolver.py"))