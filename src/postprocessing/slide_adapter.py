"""Adapt generated images to common slide deck dimensions."""

import logging
from io import BytesIO

from PIL import Image

logger = logging.getLogger(__name__)

# Registry of available slide formats.
# The UI fetches this to populate a dropdown; the pipeline looks up the
# chosen key to decide target dimensions.  Add new presets here.
SLIDE_FORMATS: dict[str, dict] = {
    "original": {"label": "Original (no resize)", "width": None, "height": None},
    "hd_16_9":  {"label": "HD 16:9 (1920\u00d71080)",  "width": 1920, "height": 1080},
    "hd_4_3":   {"label": "HD 4:3 (1440\u00d71080)",   "width": 1440, "height": 1080},
    "qhd_16_9": {"label": "2K 16:9 (2560\u00d71440)",  "width": 2560, "height": 1440},
}


def adapt_for_slides(
    image_bytes: bytes,
    format_key: str = "hd_16_9",
    bg_color: tuple[int, int, int] = (255, 255, 255),
) -> bytes:
    """Scale and centre-pad *image_bytes* onto a canvas of the requested slide format.

    Args:
        image_bytes: Raw PNG/JPEG bytes from the image generator.
        format_key:  Key into ``SLIDE_FORMATS``.
        bg_color:    RGB background fill for the padding area.

    Returns:
        PNG bytes at the target dimensions (or the original bytes unchanged
        when *format_key* is ``"original"``).
    """
    fmt = SLIDE_FORMATS.get(format_key)
    if fmt is None:
        logger.warning("Unknown slide format '%s', returning original image", format_key)
        return image_bytes

    target_w, target_h = fmt["width"], fmt["height"]
    if target_w is None or target_h is None:
        return image_bytes

    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    src_w, src_h = img.size

    # Scale proportionally so the image fits inside the target canvas.
    ratio = min(target_w / src_w, target_h / src_h)
    new_w = int(src_w * ratio)
    new_h = int(src_h * ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Centre on a new canvas.
    canvas = Image.new("RGB", (target_w, target_h), bg_color)
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y))

    buf = BytesIO()
    canvas.save(buf, format="PNG", dpi=(150, 150))
    result = buf.getvalue()

    logger.info(
        "Adapted image from %dx%d to %dx%d (format=%s, padding=%dpx x %dpx)",
        src_w, src_h, target_w, target_h, format_key, offset_x, offset_y,
    )
    return result
