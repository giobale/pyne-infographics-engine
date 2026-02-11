"""Load and render prompt templates from config/prompts.yaml."""

import logging

import yaml

from src.config import settings

logger = logging.getLogger(__name__)

_prompts_cache: dict | None = None


def _load_prompts() -> dict:
    """Load prompts YAML file (cached after first call)."""
    global _prompts_cache
    if _prompts_cache is None:
        with open(settings.prompts_path, "r") as f:
            _prompts_cache = yaml.safe_load(f)
        logger.debug("Loaded prompts from %s", settings.prompts_path)
    return _prompts_cache


def get_prompt(agent_name: str, **kwargs: str) -> str:
    """
    Load a prompt template by agent name and render placeholders.

    Example:
        get_prompt("retriever_classify", brief="Build a pipeline...")
    """
    prompts = _load_prompts()
    if agent_name not in prompts:
        raise KeyError(f"Prompt '{agent_name}' not found in {settings.prompts_path}")

    template: str = prompts[agent_name]
    try:
        rendered = template.format_map(kwargs)
    except KeyError as e:
        raise KeyError(
            f"Missing placeholder {e} for prompt '{agent_name}'. "
            f"Provided: {list(kwargs.keys())}"
        ) from e

    logger.debug("Rendered prompt '%s' (%d chars)", agent_name, len(rendered))
    return rendered
