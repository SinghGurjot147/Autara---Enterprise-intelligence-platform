"""
Small provider abstraction so the renderer never cares where an image came
from, and a provider can be swapped or added (AI image generation, user
uploads, a different stock API) without touching renderer.py.

    ImageProvider
        â”œâ”€â”€ search_image(query) -> bytes | None
        â””â”€â”€ generate_image(prompt) -> bytes | None   (not implemented yet â€” seam only)

If no image can be obtained for any reason, callers get None and must fall
back to a text/shape-only layout. Image failures NEVER abort presentation
generation.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from io import BytesIO

import requests

from backend.app.config import settings

logger = logging.getLogger("presentations.images")


class ImageProvider(ABC):
    @abstractmethod
    def search_image(self, query: str) -> bytes | None:
        ...

    def generate_image(self, prompt: str) -> bytes | None:  # pragma: no cover - seam for later
        """Plug an AI image-generation provider in here later. Not implemented in v1."""
        return None


class PexelsImageProvider(ImageProvider):
    """Free-tier stock photo search: https://www.pexels.com/api/"""

    BASE_URL = "https://api.pexels.com/v1/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_image(self, query: str) -> bytes | None:
        if not query:
            return None
        try:
            resp = requests.get(
                self.BASE_URL,
                headers={"Authorization": self.api_key},
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            photos = data.get("photos") or []
            if not photos:
                return None
            image_url = photos[0]["src"]["large"]
            img_resp = requests.get(image_url, timeout=15)
            img_resp.raise_for_status()
            return img_resp.content
        except Exception as e:  # noqa: BLE001
            logger.warning("Pexels image search failed for %r: %s", query, e)
            return None


class NullImageProvider(ImageProvider):
    """Used when no image API key is configured. Renderer treats None as 'use text layout'."""

    def search_image(self, query: str) -> bytes | None:
        return None


def get_image_provider() -> ImageProvider:
    if settings.pexels_api_key:
        return PexelsImageProvider(settings.pexels_api_key)
    return NullImageProvider()


def fetch_images_for_spec(spec_slides, enabled: bool) -> dict[int, bytes]:
    """
    Resolves an image (bytes) per slide_number that requested one.
    Returns only entries that actually succeeded â€” missing keys mean
    'render this slide without an image'.
    """
    images: dict[int, bytes] = {}
    if not enabled:
        return images
    provider = get_image_provider()
    for slide in spec_slides:
        if getattr(slide, "image_required", False) and getattr(slide, "image_query", None):
            img = provider.search_image(slide.image_query)
            if img:
                images[slide.slide_number] = img
    return images

