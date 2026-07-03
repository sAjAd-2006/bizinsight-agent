"""
Policy Server — Zero-Trust Development Guardrail
Day 5: Implements hybrid policy engine (Structural + Semantic Gating)

Structural Gating: Deterministic YAML-based rules (fast, binary)
Semantic Gating: LLM-based intent inspection (slow, nuanced)

The agent execution flow is intercepted:
1. Structural Check — Is the tool allowed for this role/env? (Check YAML)
2. Execution — If pass, the tool runs. Otherwise, "Policy Violation" is returned.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class PolicyService:
    """
    Lightweight Policy Server that enforces Zero-Trust principles.
    Separates execution logic from governance logic.

    Usage:
        policy = PolicyService(
            config_path="policies.yaml",
            environment="localhost",
            role="analyst"
        )
        if policy.is_tool_allowed("read_csv"):
            # proceed with tool execution
        else:
            # return "Policy Violation" to agent
    """

    def __init__(self, config_path: str, environment: str = "localhost", role: str = "analyst"):
        self.environment = environment
        self.role = role
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and parse the policies.yaml configuration file."""
        path = Path(config_path)
        if not path.exists():
            return {"environments": {}, "roles": {}}
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}

    def is_tool_allowed(self, tool_name: str) -> bool:
        """
        Structural Gating: Check if a tool is allowed for the current role/environment.

        Returns True if the tool is permitted, False otherwise.
        Checks:
        1. Is the tool blocked in the current environment?
        2. Is the tool in the role's allowed list?
        """
        # Check Environment Blocks
        env_config = self.config.get("environments", {}).get(self.environment, {})
        blocked_tools = env_config.get("blocked_tools", [])
        if tool_name in blocked_tools:
            return False

        # Check Role Permissions
        role_config = self.config.get("roles", {}).get(self.role, {})
        allowed_tools = role_config.get("allowed_tools", [])
        if "*" in allowed_tools:
            return True
        return tool_name in allowed_tools

    def get_violation_message(self, tool_name: str) -> str:
        """Generate a human-readable policy violation message."""
        return (
            f"Policy Violation: Tool '{tool_name}' is not allowed "
            f"for role '{self.role}' in environment '{self.environment}'."
        )

    def list_allowed_tools(self) -> list:
        """List all tools currently allowed for this role/environment combination."""
        env_config = self.config.get("environments", {}).get(self.environment, {})
        blocked = set(env_config.get("blocked_tools", []))

        role_config = self.config.get("roles", {}).get(self.role, {})
        allowed = role_config.get("allowed_tools", [])

        if "*" in allowed:
            return ["all tools (admin)"]

        return [t for t in allowed if t not in blocked]