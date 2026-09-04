"""
STAGE 1 of the pipeline: turn a topic (+ optional RAG context) into a
validated PresentationSpec. Gemini is asked for structured JSON only;
nothing it returns reaches the renderer without passing Pydantic validation.

Reuses the SAME Gemini API key / model your existing chat backend uses
(app.config.settings) â€” no second credential mechanism.
"""
from __future__ import annotations

import json
import os
import logging
import re
from typing import Optional

from pydantic import ValidationError

from backend.app.config import settings
from backend.app.schemas.presentation import PresentationRequest, PresentationSpec
from backend.app.services.rag_context import RetrievedChunk

logger = logging.getLogger("presentations.planner")

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class PlannerError(Exception):
    pass


def _extract_json(raw: str) -> str:
    """Gemini sometimes wraps JSON in markdown fences or adds stray prose. Pull the JSON out."""
    raw = raw.strip()
    fence = _JSON_FENCE_RE.search(raw)
    if fence:
        return fence.group(1).strip()
    # fallback: take the substring between the first '{' and the last '}'
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def _build_prompt(req: PresentationRequest, context_chunks: list[RetrievedChunk]) -> str:
    grounding_block = ""
    if context_chunks:
        joined = "\n\n".join(
            f"[{i+1}] ({c.document} â€” page {c.page or 'n/a'})\n{c.text}"
            for i, c in enumerate(context_chunks)
        )
        grounding_block = f"""
SOURCE MATERIAL (retrieved from the organization's indexed documents):
{joined}

Use the source material above as the primary factual basis for this presentation.
Do not invent statistics, dates, names, percentages, or claims that are not
supported by the material above. If information needed for a strong slide is
not available in the source material, omit that claim rather than fabricating it.
When a slide's content depends on the source material, populate its "sources"
array with the matching bracket reference(s) as {{"label": "[1]", "document": "...", "page": ...}}.
"""

    schema_hint = """
Return ONLY a single JSON object (no markdown fences, no commentary) matching exactly this shape:

{
  "title": string,
  "subtitle": string | null,
  "theme": "modern" | "corporate" | "academic" | "minimal" | "dark",
  "aspect_ratio": "16:9",
  "slides": [
    {
      "slide_number": integer,
      "type": "title" | "section" | "content" | "image_content" | "two_column" | "three_column"
             | "comparison" | "timeline" | "process" | "statistics" | "quote" | "summary"
             | "conclusion" | "sources",
      "title": string,
      "subtitle": string | null,
      "bullets": string[] (max 6, one short sentence each, omit for non-bullet slide types),
      "left_bullets": string[] (two_column / three_column / comparison only),
      "right_bullets": string[] (two_column / comparison only),
      "center_bullets": string[] (three_column only),
      "left_label": string | null (comparison only, e.g. "Before"),
      "right_label": string | null (comparison only, e.g. "After"),
      "steps": string[] (timeline / process only, ordered),
      "quote_text": string | null (quote slides only),
      "quote_attribution": string | null,
      "stats": [{"label": string, "value": number}] (statistics slides only â€” ONLY use numbers
                that genuinely exist in the provided source material; omit this slide type entirely
                if no real numeric data is available),
      "stats_unit": string | null,
      "image_required": boolean,
      "image_query": string | null (a short, concrete visual search phrase, e.g. "solar panel installation rooftop"),
      "speaker_notes": string | null,
      "sources": [{"label": string, "document": string | null, "page": integer | null}]
    }
  ]
}
"""

    return f"""You are a presentation content strategist creating a {req.slide_count}-slide
professional slide deck.

Topic / instructions: "{req.topic}"
Audience: {req.audience}
Tone: {req.tone}
Visual style: {req.style}
Include images: {req.include_images}
Include speaker notes: {req.include_notes}
Include a sources slide: {req.include_sources}
{grounding_block}
CONTENT RULES:
- Exactly {req.slide_count} slides, slide_number 1..{req.slide_count} in order.
- Slide 1 must be type "title". If include_sources is true, the LAST slide must be type "sources".
- Vary slide types deliberately (do not make every slide type "content"). Use "section" dividers
  for major topic shifts, "statistics" only when real numeric data is available, "comparison" for
  before/after or option-vs-option content, "timeline" or "process" for sequences, "quote" sparingly.
- Bullets: concise, 3-5 per slide typically, max 6, each a single short sentence â€” never a paragraph.
- Do not repeat the same information across multiple slides.
- Build a logical narrative arc appropriate to the topic (e.g. context -> current situation ->
  challenges -> impact -> solutions -> implementation -> outlook -> conclusion), adapted to fit
  exactly {req.slide_count} slides.
- image_query should be concrete and photographic (not abstract), only set when image_required is true.
- Keep titles short (under ~8 words).
{schema_hint}
"""


def _deterministic_fallback(req: PresentationRequest) -> PresentationSpec:
    """
    Last-resort local fallback if Gemini is unreachable / returns unusable output
    after retries. Guarantees generation never hard-fails outright.
    """
    n = req.slide_count
    slides = [
        {
            "slide_number": 1,
            "type": "title",
            "title": req.topic[:120],
            "subtitle": f"An overview for a {req.audience} audience",
            "image_required": req.include_images,
            "image_query": req.topic[:80],
        }
    ]
    section_labels = ["Background", "Current Situation", "Key Considerations", "Challenges",
                       "Opportunities", "Recommendations", "Next Steps"]
    body_count = max(0, n - 2 - (1 if req.include_sources else 0))
    for i in range(body_count):
        label = section_labels[i % len(section_labels)]
        slides.append({
            "slide_number": len(slides) + 1,
            "type": "content",
            "title": f"{label}",
            "bullets": [
                f"Key point {i * 3 + 1} regarding {req.topic[:60]}",
                f"Key point {i * 3 + 2} regarding {req.topic[:60]}",
                f"Key point {i * 3 + 3} regarding {req.topic[:60]}",
            ],
            "image_required": req.include_images and i % 2 == 0,
            "image_query": req.topic[:80],
        })
    slides.append({
        "slide_number": len(slides) + 1,
        "type": "conclusion",
        "title": "Conclusion",
        "bullets": [f"Summary takeaway for {req.topic[:60]}", "Recommended next step"],
    })
    if req.include_sources:
        slides.append({
            "slide_number": len(slides) + 1,
            "type": "sources",
            "title": "Sources",
            "sources": [{"label": "Generated without document grounding", "document": None, "page": None}],
        })
    # trim/pad slide_number sequence to exactly n if arithmetic drifted
    slides = slides[:n]
    for idx, s in enumerate(slides, start=1):
        s["slide_number"] = idx

    return PresentationSpec(
        title=req.topic[:140],
        subtitle=None,
        theme=req.style,
        aspect_ratio="16:9",
        slides=slides,  # type: ignore[arg-type]
    )


def _validate_llm_output(raw: str, req: PresentationRequest) -> PresentationSpec:
    """
    Parse and validate raw LLM output into a PresentationSpec.
    Raises on malformed JSON or schema-invalid output.
    """
    raw = (raw or "").strip()

    if not raw:
        raise ValueError("empty response from provider")

    payload = json.loads(_extract_json(raw))
    spec = PresentationSpec.model_validate(payload)

    # Normalize slide numbering and defensively clamp slide count.
    spec.slides = (
        spec.slides[: req.slide_count]
        if len(spec.slides) > req.slide_count
        else spec.slides
    )

    for i, slide in enumerate(spec.slides, start=1):
        slide.slide_number = i

    if not spec.slides:
        raise ValueError("provider returned zero slides")

    return spec


def _generate_with_gemini(prompt: str, req: PresentationRequest) -> PresentationSpec:
    """Primary provider: Gemini 2.5 Flash."""
    from google import genai
    from google.genai import types

    api_key = settings.effective_gemini_api_key
    if not api_key:
        raise RuntimeError("Gemini API key not configured")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.6,
            max_output_tokens=8192,
        ),
    )

    return _validate_llm_output(response.text or "", req)


def _generate_with_groq(prompt: str, req: PresentationRequest) -> PresentationSpec:
    """First fallback: existing Groq Llama 3.3 70B."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured")

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional presentation content strategist. "
                    "Return ONLY valid JSON matching the schema requested by the user. "
                    "Do not include markdown fences or commentary."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.6,
        max_tokens=8192,
    )

    raw = response.choices[0].message.content or ""
    return _validate_llm_output(raw, req)


def _generate_with_openrouter(
    prompt: str, req: PresentationRequest
) -> PresentationSpec:
    """Second fallback: existing OpenRouter free router."""
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not configured")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional presentation content strategist. "
                    "Return ONLY valid JSON matching the schema requested by the user. "
                    "Do not include markdown fences or commentary."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.6,
        max_tokens=8192,
    )

    raw = response.choices[0].message.content or ""
    return _validate_llm_output(raw, req)


def generate_presentation_spec(
    req: PresentationRequest,
    context_chunks: Optional[list[RetrievedChunk]] = None,
) -> tuple[PresentationSpec, list[str]]:
    """
    Generate a validated PresentationSpec using provider failover:

        Gemini 2.5 Flash
            -> Groq Llama 3.3 70B
            -> OpenRouter openrouter/free
            -> deterministic local fallback

    A provider is considered successful only when its output passes
    JSON parsing AND PresentationSpec validation.
    """

    warnings: list[str] = []
    context_chunks = context_chunks or []

    prompt = _build_prompt(req, context_chunks)

    providers = [
        (
            "Gemini 2.5 Flash",
            _generate_with_gemini,
        ),
        (
            "Groq Llama 3.3 70B",
            _generate_with_groq,
        ),
        (
            "OpenRouter free",
            _generate_with_openrouter,
        ),
    ]

    for provider_name, provider_fn in providers:
        try:
            logger.info("Trying PPT planning provider: %s", provider_name)

            spec = provider_fn(prompt, req)

            logger.info("PPT planning succeeded with provider: %s", provider_name)

            if provider_name != "Gemini 2.5 Flash":
                warnings.append(
                    f"Presentation content was generated using fallback provider: "
                    f"{provider_name}."
                )

            return spec, warnings

        except ImportError as e:
            logger.warning(
                "PPT provider %s unavailable because its package is missing: %s",
                provider_name,
                e,
            )
            warnings.append(
                f"{provider_name} unavailable because its Python package is missing."
            )

        except Exception as e:  # noqa: BLE001
            logger.warning(
                "PPT planning provider %s failed: %s",
                provider_name,
                e,
            )
            warnings.append(
                f"{provider_name} failed: {str(e)[:250]}"
            )

    # All AI providers failed.
    warnings.append(
        "All configured AI presentation providers failed; "
        "used the deterministic local fallback outline."
    )

    return _deterministic_fallback(req), warnings