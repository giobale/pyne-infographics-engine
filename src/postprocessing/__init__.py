"""Post-processing transforms applied to generated images."""

from .slide_adapter import SLIDE_FORMATS, adapt_for_slides

__all__ = ["SLIDE_FORMATS", "adapt_for_slides"]
