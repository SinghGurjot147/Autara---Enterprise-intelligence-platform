"""Lightweight sanity checks run after rendering, before the file is exposed to clients."""
from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile

from pptx import Presentation


class PptxValidationError(Exception):
    pass


def validate_pptx(path: Path, expected_slide_count: int) -> None:
    if not path.exists():
        raise PptxValidationError("generated file does not exist")
    if path.stat().st_size == 0:
        raise PptxValidationError("generated file is empty")
    try:
        prs = Presentation(str(path))
    except BadZipFile as e:
        raise PptxValidationError(f"generated file is not a valid .pptx package: {e}") from e
    except Exception as e:  # noqa: BLE001
        raise PptxValidationError(f"generated file could not be reopened: {e}") from e

    actual = len(prs.slides)
    if actual == 0:
        raise PptxValidationError("presentation has zero slides")
    if actual < max(1, expected_slide_count - 1):
        # allow a slide of slack (e.g. sources slide intentionally skipped)
        raise PptxValidationError(f"expected ~{expected_slide_count} slides, found {actual}")

