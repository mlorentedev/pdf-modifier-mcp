"""Jinja2 prompt template renderer."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def get_template_env() -> Environment:
    """Get a cached Jinja2 environment for prompt templates."""
    return Environment(
        loader=FileSystemLoader(str(PROMPTS_DIR)),
        keep_trailing_newline=True,
    )


def render_prompt(template_name: str, **kwargs: Any) -> str:
    """Render a prompt template with given variables.

    Args:
        template_name: Template file name (e.g., "detect_fields.j2").
        **kwargs: Variables to substitute in the template.

    Returns:
        Rendered prompt string.

    Raises:
        FileNotFoundError: If template doesn't exist.
    """
    env = get_template_env()
    template = env.get_template(template_name)
    rendered: str = template.render(**kwargs)
    return rendered
