"""Critic agent: multimodal evaluation of generated diagrams."""

import logging

from src.config import client, settings
from src.models import CriticOutput
from src.utils.image_utils import bytes_to_base64
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)


def evaluate(
    image_bytes: bytes,
    brief: str,
    description: str,
) -> CriticOutput:
    """
    Evaluate a generated image against the original brief and description.

    Returns CriticOutput with approved=True, or approved=False with a
    complete refined description that fixes identified issues.
    """
    image_b64 = bytes_to_base64(image_bytes)

    prompt_text = get_prompt(
        "critic",
        brief=brief,
        description=description,
    )

    content: list[dict] = [
        {"type": "text", "text": prompt_text},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_b64}",
                "detail": "high",  # High detail for quality evaluation
            },
        },
    ]

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": content}],
        temperature=0.2,  # Low temp for consistent evaluation
        max_tokens=3000,
    )

    result_text = response.choices[0].message.content.strip()

    if result_text.upper().startswith("APPROVED"):
        logger.info("Critic: APPROVED")
        return CriticOutput(approved=True, feedback_summary="All dimensions passed")

    logger.info(
        "Critic: REFINEMENT NEEDED (%d words)", len(result_text.split())
    )
    return CriticOutput(
        approved=False,
        refined_description=result_text,
        feedback_summary=result_text[:200],
    )
