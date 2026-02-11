"""Visualizer agent: generate an image from the styled description."""

import base64
import logging

from src.config import client, settings

logger = logging.getLogger(__name__)


def generate_image(styled_description: str) -> bytes:
    """
    Generate an image using the configured image generation model.

    The styled_description IS the prompt — no additional wrapping.
    Returns raw image bytes (PNG/WEBP/JPEG depending on config).
    """
    logger.info(
        "Generating image with model=%s, size=%s, quality=%s",
        settings.image_model,
        settings.image_size.value,
        settings.image_quality.value,
    )

    response = client.images.generate(
        model=settings.image_model,
        prompt=styled_description,
        size=settings.image_size.value,
        quality=settings.image_quality.value,
        n=1,
        response_format="b64_json",
    )

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    logger.info("Generated image: %d bytes", len(image_bytes))
    return image_bytes
