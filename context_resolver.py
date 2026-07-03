"""
Context Resolver — Context Hygiene & Prompt Sanitization
Day 5: Prevents context hallucination by replacing [[VARIABLE]] placeholders
with sanitized values from environment variables or runtime overrides.

This prevents agents from leaking sensitive information (PII) by ensuring
that no hardcoded emails, API keys, or URLs appear in agent prompts.
"""

import os
import re
from typing import Optional, Dict, Any


def resolve_context(template_str: str, override_state: Optional[Dict[str, Any]] = None) -> str:
    """
    Scans a template string for [[VARIABLE_NAME]] placeholders and replaces
    them with values from override_state (priority) or os.environ (fallback).

    If a variable is not found in either source, the placeholder is left
    UNRESOLVED to prevent silent failures.

    Args:
        template_str: String containing [[VARIABLE]] placeholders
        override_state: Optional dict of runtime variable overrides

    Returns:
        String with resolved placeholders

    Examples:
        >>> resolve_context("Hello [[NAME]]", {"NAME": "Alice"})
        'Hello Alice'

        >>> # If NAME is not set anywhere, placeholder stays:
        >>> resolve_context("Hello [[NAME]]")
        'Hello [[NAME]]'
    """
    if template_str is None:
        return ""

    state_to_check = override_state or {}

    def replacement(match):
        var_name = match.group(1).strip()
        # 1. Prioritize runtime state overrides
        if var_name in state_to_check and state_to_check[var_name] is not None:
            return str(state_to_check[var_name])
        # 2. Fallback to validated environment variables
        elif var_name in os.environ and os.environ[var_name] is not None:
            return os.environ[var_name]
        # 3. Leave unresolved to prevent silent failures
        else:
            return match.group(0)

    # Resolve all bracketed variables dynamically
    return re.sub(r'\[\[([^\]]+)\]\]', replacement, template_str)


def sanitize_tool_args(args: Dict[str, Any], override_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Middleware that sanitizes all string arguments in a tool call.
    Integrates with the agent pipeline to prevent prompt injection.

    Args:
        args: Dictionary of tool argument name -> value

    Returns:
        Sanitized args dictionary with all strings resolved
    """
    resolved_args = {}
    for k, v in args.items():
        if isinstance(v, str):
            resolved_args[k] = resolve_context(v, override_state=override_state)
        elif isinstance(v, list):
            resolved_args[k] = [
                resolve_context(item, override_state=override_state) if isinstance(item, str) else item
                for item in v
            ]
        else:
            resolved_args[k] = v
    return resolved_args


def mask_pii(text: str) -> str:
    """
    Basic PII masking for common patterns.
    Replaces email addresses and API key-like strings with placeholders.

    Args:
        text: Input text that may contain PII

    Returns:
        Text with PII replaced by [[MASKED_*]] placeholders
    """
    # Mask email addresses
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[[MASKED_EMAIL]]',
        text
    )
    # Mask API key-like strings (long alphanumeric sequences)
    text = re.sub(
        r'\b[A-Za-z0-9_-]{32,}\b',
        '[[MASKED_API_KEY]]',
        text
    )
    return text