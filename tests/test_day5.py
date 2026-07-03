"""
Tests for Day 5: Spec-Driven Development, Policy Server, and Context Hygiene.
"""

import os
import sys
import pytest
import tempfile
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestSpecDrivenDevelopment:
    """Day 5: Verify Spec-Driven Development (SDD) practices."""

    def test_specs_directory_exists(self):
        """SDD: A specs/ directory should exist for BDD specifications."""
        path = os.path.join(PROJECT_ROOT, "specs")
        assert os.path.isdir(path)

    def test_bdd_spec_exists(self):
        """SDD: At least one BDD spec file should exist."""
        specs = [
            f for f in os.listdir(os.path.join(PROJECT_ROOT, "specs"))
            if f.endswith((".feature", ".spec", ".md"))
        ]
        assert len(specs) >= 1, "No BDD spec files found in specs/"

    def test_bdd_spec_uses_gherkin(self):
        """SDD: Spec should use Gherkin syntax (Given/When/Then)."""
        spec_path = os.path.join(PROJECT_ROOT, "specs", "analysis_pipeline.feature")
        with open(spec_path) as f:
            content = f.read()
        assert "Feature:" in content
        assert "Scenario:" in content
        assert "Given" in content
        assert "When" in content
        assert "Then" in content

    def test_bdd_spec_has_multiple_scenarios(self):
        """SDD: Spec should cover multiple scenarios (happy path + edge cases)."""
        spec_path = os.path.join(PROJECT_ROOT, "specs", "analysis_pipeline.feature")
        with open(spec_path) as f:
            content = f.read()
        scenario_count = content.count("Scenario:")
        assert scenario_count >= 3, f"Expected 3+ scenarios, found {scenario_count}"

    def test_bdd_spec_includes_security_scenario(self):
        """SDD: Spec should include a security/path traversal scenario."""
        spec_path = os.path.join(PROJECT_ROOT, "specs", "analysis_pipeline.feature")
        with open(spec_path) as f:
            content = f.read()
        assert "path traversal" in content.lower() or "security" in content.lower()

    def test_bdd_spec_includes_policy_scenario(self):
        """SDD: Spec should include a Policy Server scenario."""
        spec_path = os.path.join(PROJECT_ROOT, "specs", "analysis_pipeline.feature")
        with open(spec_path) as f:
            content = f.read()
        assert "policy" in content.lower()


class TestPolicyServer:
    """Day 5: Verify Policy Server (Zero-Trust Development)."""

    def test_policy_server_module_exists(self):
        """Policy server module should exist at project root."""
        path = os.path.join(PROJECT_ROOT, "policy_server.py")
        assert os.path.isfile(path)

    def test_policies_yaml_exists(self):
        """policies.yaml configuration should exist."""
        path = os.path.join(PROJECT_ROOT, "policies.yaml")
        assert os.path.isfile(path)

    def test_policies_yaml_has_environments(self):
        """policies.yaml should define environments with blocked tools."""
        import yaml
        path = os.path.join(PROJECT_ROOT, "policies.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert "environments" in config
        assert "localhost" in config["environments"]

    def test_policies_yaml_has_roles(self):
        """policies.yaml should define roles with allowed tools."""
        import yaml
        path = os.path.join(PROJECT_ROOT, "policies.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert "roles" in config
        assert "analyst" in config["roles"]
        assert "admin" in config["roles"]

    def test_policy_blocks_environment_tool(self):
        """Policy Server should block tools in environment blocklist."""
        from policy_server import PolicyService
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "environments": {"test": {"blocked_tools": ["danger_tool"]}},
                "roles": {"tester": {"allowed_tools": ["*"]}}
            }, f)
            tmp_path = f.name
        try:
            policy = PolicyService(config_path=tmp_path, environment="test", role="tester")
            assert not policy.is_tool_allowed("danger_tool")
        finally:
            os.unlink(tmp_path)

    def test_policy_allows_role_tool(self):
        """Policy Server should allow tools in role allowlist."""
        from policy_server import PolicyService
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "environments": {"test": {"blocked_tools": []}},
                "roles": {"tester": {"allowed_tools": ["safe_tool"]}}
            }, f)
            tmp_path = f.name
        try:
            policy = PolicyService(config_path=tmp_path, environment="test", role="tester")
            assert policy.is_tool_allowed("safe_tool")
        finally:
            os.unlink(tmp_path)

    def test_policy_denies_unknown_tool(self):
        """Policy Server should deny tools not in role allowlist."""
        from policy_server import PolicyService
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "environments": {"test": {"blocked_tools": []}},
                "roles": {"viewer": {"allowed_tools": ["read_only"]}}
            }, f)
            tmp_path = f.name
        try:
            policy = PolicyService(config_path=tmp_path, environment="test", role="viewer")
            assert not policy.is_tool_allowed("write_tool")
        finally:
            os.unlink(tmp_path)

    def test_admin_has_wildcard_access(self):
        """Admin role with '*' should have access to all tools."""
        from policy_server import PolicyService
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "environments": {"test": {"blocked_tools": []}},
                "roles": {"admin": {"allowed_tools": ["*"]}}
            }, f)
            tmp_path = f.name
        try:
            policy = PolicyService(config_path=tmp_path, environment="test", role="admin")
            assert policy.is_tool_allowed("any_tool")
        finally:
            os.unlink(tmp_path)

    def test_violation_message_is_informative(self):
        """Violation message should include tool name, role, and environment."""
        from policy_server import PolicyService
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "environments": {"prod": {"blocked_tools": []}},
                "roles": {"viewer": {"allowed_tools": ["read"]}}
            }, f)
            tmp_path = f.name
        try:
            policy = PolicyService(config_path=tmp_path, environment="prod", role="viewer")
            msg = policy.get_violation_message("delete_all")
            assert "delete_all" in msg
            assert "viewer" in msg
            assert "prod" in msg
        finally:
            os.unlink(tmp_path)

    def test_list_allowed_tools(self):
        """list_allowed_tools should return only non-blocked tools for the role."""
        from policy_server import PolicyService
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "environments": {"test": {"blocked_tools": ["tool_b"]}},
                "roles": {"tester": {"allowed_tools": ["tool_a", "tool_b", "tool_c"]}}
            }, f)
            tmp_path = f.name
        try:
            policy = PolicyService(config_path=tmp_path, environment="test", role="tester")
            allowed = policy.list_allowed_tools()
            assert "tool_a" in allowed
            assert "tool_c" in allowed
            assert "tool_b" not in allowed  # blocked by environment
        finally:
            os.unlink(tmp_path)


class TestContextHygiene:
    """Day 5: Verify Context Hygiene and Prompt Sanitization."""

    def test_context_resolver_module_exists(self):
        """context_resolver.py should exist at project root."""
        path = os.path.join(PROJECT_ROOT, "context_resolver.py")
        assert os.path.isfile(path)

    def test_resolve_context_with_override(self):
        """Override state should take priority over env vars."""
        from context_resolver import resolve_context
        result = resolve_context("Hello [[NAME]]", {"NAME": "Alice"})
        assert result == "Hello Alice"

    def test_resolve_context_with_env_var(self):
        """Should fall back to environment variables."""
        from context_resolver import resolve_context
        os.environ["TEST_RESOLVER_VAR"] = "World"
        try:
            result = resolve_context("Hello [[TEST_RESOLVER_VAR]]")
            assert result == "Hello World"
        finally:
            del os.environ["TEST_RESOLVER_VAR"]

    def test_resolve_context_leaves_unresolved(self):
        """Unresolved variables should remain as-is (no silent failure)."""
        from context_resolver import resolve_context
        result = resolve_context("Contact [[UNKNOWN_VAR]] for help")
        assert "[[UNKNOWN_VAR]]" in result

    def test_resolve_context_none_input(self):
        """None input should return empty string."""
        from context_resolver import resolve_context
        assert resolve_context(None) == ""

    def test_sanitize_tool_args_strings(self):
        """sanitize_tool_args should resolve placeholders in string values."""
        from context_resolver import sanitize_tool_args
        args = {"query": "Analyze [[METRIC]]", "limit": 10}
        result = sanitize_tool_args(args, {"METRIC": "sales"})
        assert result["query"] == "Analyze sales"
        assert result["limit"] == 10  # non-string unchanged

    def test_sanitize_tool_args_lists(self):
        """sanitize_tool_args should resolve placeholders in list items."""
        from context_resolver import sanitize_tool_args
        args = {"items": ["Check [[ITEM_A]]", "Check [[ITEM_B]]"], "count": 2}
        result = sanitize_tool_args(args, {"ITEM_A": "X", "ITEM_B": "Y"})
        assert result["items"] == ["Check X", "Check Y"]

    def test_mask_pii_emails(self):
        """mask_pii should replace email addresses with placeholders."""
        from context_resolver import mask_pii
        result = mask_pii("Contact john@company.com for details")
        assert "john@company.com" not in result
        assert "[[MASKED_EMAIL]]" in result

    def test_mask_pii_api_keys(self):
        """mask_pii should replace long alphanumeric strings (API keys)."""
        from context_resolver import mask_pii
        result = mask_pii("Key: abcdef1234567890abcdef1234567890ab")
        assert "abcdef1234567890abcdef1234567890ab" not in result
        assert "[[MASKED_API_KEY]]" in result

    def test_main_integrates_policy_server(self):
        """main.py should import and use PolicyService."""
        main_path = os.path.join(PROJECT_ROOT, "main.py")
        with open(main_path) as f:
            content = f.read()
        assert "PolicyService" in content
        assert "policy_server" in content

    def test_main_integrates_context_resolver(self):
        """main.py should reference context hygiene."""
        main_path = os.path.join(PROJECT_ROOT, "main.py")
        with open(main_path) as f:
            content = f.read()
        assert "context_resolver" in content or "Context Hygiene" in content

    def test_agents_md_references_day5(self):
        """AGENTS.md should reference Day 5 concepts."""
        path = os.path.join(PROJECT_ROOT, "AGENTS.md")
        with open(path) as f:
            content = f.read()
        assert "Policy Server" in content or "policy" in content.lower()
        assert "Context Hygiene" in content or "PII" in content