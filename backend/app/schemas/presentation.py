"""
All presentation-related data shapes.

`PresentationSpec` is the strict, validated contract between Gemini's output
and the deterministic PPTX renderer. Gemini is never trusted to produce
anything past this boundary unvalidated.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------- requests

Audience = Literal["general", "student", "academic", "business", "technical"]
Tone = Literal["professional", "academic", "simple", "executive"]
Style = Literal["modern", "corporate", "minimal", "academic", "dark"]
Mode = Literal["general", "rag"]


class PresentationRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=400)
    mode: Mode = "general"
    slide_count: int = Field(10, ge=3, le=30)
    audience: Audience = "general"
    tone: Tone = "professional"
    style: Style = "modern"
    include_images: bool = True
    include_notes: bool = True
    include_sources: bool = True
    document_ids: list[str] = Field(default_factory=list)

    @field_validator("topic")
    @classmethod
    def strip_topic(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("topic cannot be empty")
        return v

    @field_validator("document_ids")
    @classmethod
    def limit_doc_ids(cls, v: list[str]) -> list[str]:
        if len(v) > 25:
            raise ValueError("too many document_ids (max 25)")
        for d in v:
            if len(d) > 128 or "/" in d or ".." in d:
                raise ValueError("invalid document_id")
        return v


# ---------------------------------------------------------------- spec (LLM output contract)

class SlideType(str, Enum):
    title = "title"
    section = "section"
    content = "content"
    image_content = "image_content"
    two_column = "two_column"
    three_column = "three_column"
    comparison = "comparison"
    timeline = "timeline"
    process = "process"
    statistics = "statistics"
    quote = "quote"
    summary = "summary"
    conclusion = "conclusion"
    sources = "sources"


class SourceRef(BaseModel):
    label: str = Field(..., max_length=200)
    document: Optional[str] = Field(None, max_length=200)
    page: Optional[int] = None


class StatPoint(BaseModel):
    label: str = Field(..., max_length=60)
    value: float


class SlideSpec(BaseModel):
    slide_number: int
    type: SlideType = SlideType.content
    title: str = Field("", max_length=140)
    subtitle: Optional[str] = Field(None, max_length=200)
    bullets: list[str] = Field(default_factory=list)
    left_bullets: list[str] = Field(default_factory=list)   # two/three column, comparison
    right_bullets: list[str] = Field(default_factory=list)
    center_bullets: list[str] = Field(default_factory=list)
    left_label: Optional[str] = Field(None, max_length=60)
    right_label: Optional[str] = Field(None, max_length=60)
    steps: list[str] = Field(default_factory=list)          # timeline / process
    quote_text: Optional[str] = Field(None, max_length=400)
    quote_attribution: Optional[str] = Field(None, max_length=120)
    stats: list[StatPoint] = Field(default_factory=list)
    stats_unit: Optional[str] = Field(None, max_length=40)
    image_required: bool = False
    image_query: Optional[str] = Field(None, max_length=120)
    speaker_notes: Optional[str] = Field(None, max_length=1200)
    sources: list[SourceRef] = Field(default_factory=list)

    @field_validator("bullets", "left_bullets", "right_bullets", "center_bullets")
    @classmethod
    def cap_bullets(cls, v: list[str]) -> list[str]:
        v = [b.strip() for b in v if b and b.strip()]
        return v[:6]

    @field_validator("steps")
    @classmethod
    def cap_steps(cls, v: list[str]) -> list[str]:
        return [s.strip() for s in v if s and s.strip()][:8]


class PresentationSpec(BaseModel):
    title: str = Field(..., max_length=140)
    subtitle: Optional[str] = Field(None, max_length=200)
    theme: Style = "modern"
    aspect_ratio: Literal["16:9", "4:3"] = "16:9"
    slides: list[SlideSpec]

    @field_validator("slides")
    @classmethod
    def non_empty(cls, v: list[SlideSpec]) -> list[SlideSpec]:
        if not v:
            raise ValueError("presentation must contain at least one slide")
        return v


# ---------------------------------------------------------------- response

class OutlineItem(BaseModel):
    slide_number: int
    type: SlideType
    title: str


class GenerateResponse(BaseModel):
    success: bool
    presentation_id: str
    filename: str
    download_url: str
    slide_count: int
    outline: list[OutlineItem]
    warnings: list[str] = Field(default_factory=list)

