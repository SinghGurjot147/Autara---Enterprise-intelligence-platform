"""
Generated files get a server-assigned UUID filename and are tracked in a
small JSON manifest (presentation_id -> {path, original filename, created_at}).
Downloads are always served by looking up presentation_id in this manifest â€”
the client never supplies or sees a raw filesystem path, which rules out
path traversal by construction.
"""
from __future__ import annotations

import json
import re
import threading
import time
import uuid
from pathlib import Path

from backend.app.config import settings

_lock = threading.Lock()
_MANIFEST_NAME = "manifest.json"


def _manifest_path() -> Path:
    return settings.presentations_path / _MANIFEST_NAME


def _load_manifest() -> dict:
    p = _manifest_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - corrupt manifest should never crash the API
        return {}


def _save_manifest(data: dict) -> None:
    _manifest_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    text = re.sub(r"[\s-]+", "_", text)
    return (text or "presentation")[:max_len]


def new_presentation_path(topic: str) -> tuple[str, Path, str]:
    """Returns (presentation_id, absolute_path, display_filename)."""
    presentation_id = uuid.uuid4().hex
    display_filename = f"{slugify(topic)}.pptx"
    path = settings.presentations_path / f"{presentation_id}.pptx"
    return presentation_id, path, display_filename


def register_presentation(presentation_id: str, path: Path, display_filename: str, slide_count: int) -> None:
    with _lock:
        manifest = _load_manifest()
        manifest[presentation_id] = {
            "path": str(path.name),  # filename only â€” resolved against presentations_path on read
            "filename": display_filename,
            "slide_count": slide_count,
            "created_at": time.time(),
        }
        _save_manifest(manifest)


def resolve_presentation(presentation_id: str) -> dict | None:
    """Looks up a presentation by id. Returns None if unknown â€” callers must 404."""
    if not re.fullmatch(r"[a-f0-9]{32}", presentation_id):
        return None  # reject anything that isn't exactly the uuid4 hex shape we issue
    with _lock:
        manifest = _load_manifest()
    entry = manifest.get(presentation_id)
    if not entry:
        return None
    resolved_path = (settings.presentations_path / entry["path"]).resolve()
    # Defense in depth: resolved path must still live inside the presentations dir.
    if settings.presentations_path.resolve() not in resolved_path.parents and resolved_path.parent != settings.presentations_path.resolve():
        return None
    if not resolved_path.exists():
        return None
    entry = dict(entry)
    entry["absolute_path"] = resolved_path
    return entry

