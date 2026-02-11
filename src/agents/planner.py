"""Planner agent: generate detailed visual description from brief + reference images."""

import logging

from src.config import client, settings
from src.models import PlannerOutput, Reference
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)


def create_description(brief: str, references: list[Reference]) -> PlannerOutput:
    """
    Send brief + reference images to LLM, get structured 5-section visual description.
    """
    # Build reference descriptions block
    ref_descriptions = ""
    for i, ref in enumerate(references, 1):
        ref_descriptions += f"\nReference {i}: {ref.description}"

    prompt_text = get_prompt(
        "planner",
        brief=brief,
        n=str(len(references)),
        reference_descriptions=ref_descriptions,
    )

    # Build multimodal message content array
    content: list[dict] = [{"type": "text", "text": prompt_text}]

    for ref in references:
        if ref.image_base64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{ref.image_base64}",
                        "detail": "low",  # Save tokens on reference images
                    },
                }
            )

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": content}],
        temperature=0.7,
        max_tokens=2000,
    )

    description = response.choices[0].message.content.strip()
    word_count = len(description.split())

    logger.info("Planner produced description: %d words", word_count)

    return PlannerOutput(description=description, word_count=word_count)
