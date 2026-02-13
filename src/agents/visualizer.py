"""Visualizer agent: generate an image from the styled description."""

import base64
import logging

from src.config import IMAGE_MODELS, client, get_google_client, settings
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)

_system_prompt: str | None = None


def _get_system_prompt() -> str:
    """Load and cache the visualizer system prompt."""
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = get_prompt("visualizer_system")
    return _system_prompt


def _generate_openai(model: str, prompt: str) -> bytes:
    """Generate an image via the OpenAI Images API."""
    kwargs = dict(
        model=model,
        prompt=prompt,
        size=settings.image_size.value,
        quality=settings.image_quality.value,
        n=1,
    )
    if model.startswith("dall-e"):
        kwargs["response_format"] = "b64_json"

    response = client.images.generate(**kwargs)
    image_base64 = response.data[0].b64_json
    return base64.b64decode(image_base64)


def _generate_google(model: str, prompt: str) -> bytes:
    """Generate an image via the Google GenAI API."""
    from google.genai import types

    google_client = get_google_client()
    response = google_client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return part.inline_data.data
    raise RuntimeError(f"Gemini model {model} returned no image data")


def generate_image(styled_description: str, image_model: str | None = None) -> bytes:
    """
    Generate an image using the specified (or default) image generation model.

    Routes to the correct provider (OpenAI or Google) based on the IMAGE_MODELS
    registry. Returns raw image bytes (PNG/WEBP/JPEG depending on provider).
    """
    model = image_model or settings.image_model
    provider = IMAGE_MODELS[model]["provider"]

    logger.info(
        "Generating image with model=%s, provider=%s, size=%s, quality=%s",
        model,
        provider,
        settings.image_size.value,
        settings.image_quality.value,
    )

    full_prompt = f"{_get_system_prompt()}\n\n{styled_description}"

    if provider == "openai":
        image_bytes = _generate_openai(model, full_prompt)
    elif provider == "google":
        image_bytes = _generate_google(model, full_prompt)
    else:
        raise ValueError(f"Unknown provider '{provider}' for model '{model}'")

    logger.info("Generated image: %d bytes", len(image_bytes))
    return image_bytes
