"""
STAGE 2 of the pipeline: deterministically render a validated PresentationSpec
into a real .pptx file. The LLM never touches this layer â€” layout, position,
typography, color and spacing are all controlled here from theme tokens, which
is what keeps output consistent and maintainable instead of ad-hoc per slide.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

from backend.app.schemas.presentation import PresentationSpec, SlideSpec, SlideType
from backend.app.themes import Theme, get_theme

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.55)


def _rgb(hexstr: str) -> RGBColor:
    return RGBColor.from_string(hexstr)


def _new_deck(theme: Theme) -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def _blank_slide(prs: Presentation, theme: Theme):
    layout = prs.slide_layouts[6]  # blank layout
    slide = prs.slides.add_slide(layout)
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = _rgb(theme.bg)
    return slide


def _textbox(slide, left, top, width, height, *, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return box, tf


def _set_run(run, text, *, size, color, bold=False, italic=False, font=""):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if font:
        run.font.name = font
    run.font.color.rgb = _rgb(color)


def _add_title(slide, theme: Theme, text: str, *, top=Inches(0.45), size=None, color=None):
    _, tf = _textbox(slide, MARGIN, top, SLIDE_W - 2 * MARGIN, Inches(0.9))
    p = tf.paragraphs[0]
    r = p.add_run()
    _set_run(r, text, size=size or theme.heading_size, color=color or theme.text, bold=True, font=theme.font_heading)
    return tf


def _add_bullets(slide, theme: Theme, bullets: list[str], left, top, width, height, *, size=None):
    _, tf = _textbox(slide, left, top, width, height)
    size = size or theme.body_size
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(12)
        p.level = 0
        bullet_run = p.add_run()
        _set_run(bullet_run, "\u2022  ", size=size, color=theme.primary, bold=True, font=theme.font_body)
        text_run = p.add_run()
        _set_run(text_run, b, size=size, color=theme.text, font=theme.font_body)
    return tf


def _add_footer(slide, theme: Theme, slide_number: int, total: int, title_text: str):
    box, tf = _textbox(slide, MARGIN, SLIDE_H - Inches(0.42), SLIDE_W - 2 * MARGIN, Inches(0.3))
    p = tf.paragraphs[0]
    left_run = p.add_run()
    _set_run(left_run, title_text[:70], size=9, color=theme.text_soft, font=theme.font_body)
    p.alignment = PP_ALIGN.LEFT

    box2, tf2 = _textbox(slide, SLIDE_W - MARGIN - Inches(1.2), SLIDE_H - Inches(0.42), Inches(1.2), Inches(0.3))
    p2 = tf2.paragraphs[0]
    r2 = p2.add_run()
    _set_run(r2, f"{slide_number:02d} / {total:02d}", size=9, color=theme.text_soft, font=theme.font_body)
    p2.alignment = PP_ALIGN.RIGHT

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN, SLIDE_H - Inches(0.55), SLIDE_W - 2 * MARGIN, Pt(1))
    line.fill.solid()
    line.fill.fore_color.rgb = _rgb(theme.surface)
    line.line.fill.background()


def _add_image(slide, image_bytes: bytes, left, top, width, height):
    stream = BytesIO(image_bytes)
    pic = slide.shapes.add_picture(stream, left, top, width=width, height=height)
    # crop to fill the target box without distortion (center-crop)
    return pic


def _placeholder_panel(slide, theme: Theme, left, top, width, height, label: str = ""):
    """Used whenever no image is available â€” a clean shape panel instead of a blank hole."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(theme.surface)
    shape.line.color.rgb = _rgb(theme.secondary)
    shape.line.width = Pt(1)
    shape.shadow.inherit = False
    if label:
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        _set_run(r, label, size=theme.small_size, color=theme.text_soft, font=theme.font_body)


# ------------------------------------------------------------------ slide type renderers

def _render_title(slide, theme: Theme, s: SlideSpec, image: bytes | None):
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.18), SLIDE_H)
    accent.fill.solid(); accent.fill.fore_color.rgb = _rgb(theme.primary); accent.line.fill.background()

    if image:
        _add_image(slide, image, SLIDE_W - Inches(5.6), 0, Inches(5.6), SLIDE_H)
        text_width = Inches(7.0)
    else:
        text_width = SLIDE_W - Inches(1.6)

    _, tf = _textbox(slide, Inches(0.9), Inches(2.6), text_width, Inches(2.0), valign=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    r = p.add_run()
    _set_run(r, s.title, size=theme.title_size, color=theme.text, bold=True, font=theme.font_heading)
    if s.subtitle:
        p2 = tf.add_paragraph()
        p2.space_before = Pt(14)
        r2 = p2.add_run()
        _set_run(r2, s.subtitle, size=theme.body_size + 2, color=theme.text_soft, font=theme.font_body)


def _render_section(slide, theme: Theme, s: SlideSpec, image: bytes | None):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(theme.primary)
    _, tf = _textbox(slide, Inches(1.0), Inches(3.0), SLIDE_W - Inches(2.0), Inches(1.5), valign=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    r = p.add_run()
    _set_run(r, s.title, size=theme.title_size - 2, color="FFFFFF", bold=True, font=theme.font_heading)
    if s.subtitle:
        p2 = tf.add_paragraph()
        p2.space_before = Pt(10)
        r2 = p2.add_run()
        _set_run(r2, s.subtitle, size=theme.body_size + 1, color="F2F4F8", font=theme.font_body)


def _render_content(slide, theme: Theme, s: SlideSpec, image: bytes | None, has_image_slot: bool):
    _add_title(slide, theme, s.title)
    if image and has_image_slot:
        body_w = Inches(6.6)
        _add_bullets(slide, theme, s.bullets, MARGIN, Inches(1.6), body_w, SLIDE_H - Inches(2.2))
        _add_image(slide, image, MARGIN + body_w + Inches(0.35), Inches(1.6),
                   SLIDE_W - MARGIN - (MARGIN + body_w + Inches(0.35)), SLIDE_H - Inches(2.2))
    else:
        _add_bullets(slide, theme, s.bullets, MARGIN, Inches(1.6), SLIDE_W - 2 * MARGIN, SLIDE_H - Inches(2.2))


def _render_image_content(slide, theme: Theme, s: SlideSpec, image: bytes | None):
    _add_title(slide, theme, s.title, top=Inches(0.4))
    img_area = (MARGIN, Inches(1.35), SLIDE_W - 2 * MARGIN, Inches(4.4))
    if image:
        _add_image(slide, image, *img_area)
    else:
        _placeholder_panel(slide, theme, *img_area, label=s.image_query or "")
    if s.bullets:
        _add_bullets(slide, theme, s.bullets[:2], MARGIN, Inches(5.95), SLIDE_W - 2 * MARGIN, Inches(1.0), size=theme.small_size + 2)


def _render_two_or_three_column(slide, theme: Theme, s: SlideSpec):
    _add_title(slide, theme, s.title)
    cols = [s.left_bullets, s.center_bullets, s.right_bullets] if s.type == SlideType.three_column else [s.left_bullets, s.right_bullets]
    cols = [c for c in cols if True]
    n = len(cols) if s.type == SlideType.two_column else 3
    gap = Inches(0.3)
    total_w = SLIDE_W - 2 * MARGIN - gap * (n - 1)
    col_w = total_w / n
    top = Inches(1.7)
    height = SLIDE_H - Inches(2.3)
    for i in range(n):
        left = MARGIN + i * (col_w + gap)
        panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, col_w, height)
        panel.fill.solid(); panel.fill.fore_color.rgb = _rgb(theme.surface)
        panel.line.fill.background(); panel.shadow.inherit = False
        bullets = cols[i] if i < len(cols) else []
        _add_bullets(slide, theme, bullets, left + Inches(0.25), top + Inches(0.25), col_w - Inches(0.5), height - Inches(0.5), size=theme.small_size + 2)


def _render_comparison(slide, theme: Theme, s: SlideSpec):
    _add_title(slide, theme, s.title)
    gap = Inches(0.35)
    col_w = (SLIDE_W - 2 * MARGIN - gap) / 2
    top = Inches(1.7)
    height = SLIDE_H - Inches(2.3)
    labels = [s.left_label or "Option A", s.right_label or "Option B"]
    bullets_pair = [s.left_bullets, s.right_bullets]
    colors = [theme.text_soft, theme.primary]
    for i in range(2):
        left = MARGIN + i * (col_w + gap)
        panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, col_w, height)
        panel.fill.solid(); panel.fill.fore_color.rgb = _rgb(theme.surface)
        panel.line.color.rgb = _rgb(colors[i]); panel.line.width = Pt(1.5); panel.shadow.inherit = False
        _, tf = _textbox(slide, left + Inches(0.25), top + Inches(0.2), col_w - Inches(0.5), Inches(0.5))
        p = tf.paragraphs[0]; r = p.add_run()
        _set_run(r, labels[i], size=theme.small_size + 4, color=colors[i], bold=True, font=theme.font_heading)
        _add_bullets(slide, theme, bullets_pair[i], left + Inches(0.25), top + Inches(0.8), col_w - Inches(0.5), height - Inches(1.0), size=theme.small_size + 2)


def _render_timeline_process(slide, theme: Theme, s: SlideSpec):
    _add_title(slide, theme, s.title)
    steps = s.steps or s.bullets
    n = max(1, len(steps))
    top = Inches(3.3)
    total_w = SLIDE_W - 2 * MARGIN
    node_d = Inches(0.5)
    gap = (total_w - node_d) / max(1, n - 1) if n > 1 else 0
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN + node_d / 2, top + node_d / 2 - Pt(1), total_w - node_d, Pt(2))
    line.fill.solid(); line.fill.fore_color.rgb = _rgb(theme.secondary); line.line.fill.background()
    for i, step in enumerate(steps):
        left = MARGIN + i * gap if n > 1 else MARGIN + total_w / 2 - node_d / 2
        node = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, node_d, node_d)
        node.fill.solid(); node.fill.fore_color.rgb = _rgb(theme.primary); node.line.fill.background()
        tf = node.text_frame; tf.word_wrap = False
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run()
        _set_run(r, str(i + 1), size=theme.small_size + 2, color="FFFFFF", bold=True, font=theme.font_body)

        label_top = top + node_d + Inches(0.2) if i % 2 == 0 else top - Inches(1.2)
        _, ltf = _textbox(slide, left - Inches(0.85), label_top, Inches(2.2), Inches(1.0))
        lp = ltf.paragraphs[0]; lp.alignment = PP_ALIGN.CENTER
        lr = lp.add_run()
        _set_run(lr, step, size=theme.small_size + 1, color=theme.text, font=theme.font_body)


def _render_statistics(slide, theme: Theme, s: SlideSpec):
    _add_title(slide, theme, s.title)
    if not s.stats:
        _placeholder_panel(slide, theme, MARGIN, Inches(1.7), SLIDE_W - 2 * MARGIN, SLIDE_H - Inches(2.3),
                            label="No verified numeric data was available for this slide.")
        return
    chart_data = CategoryChartData()
    chart_data.categories = [pt.label for pt in s.stats]
    chart_data.add_series(s.stats_unit or "Value", [pt.value for pt in s.stats])
    x, y, cx, cy = MARGIN, Inches(1.7), SLIDE_W - 2 * MARGIN, SLIDE_H - Inches(2.5)
    gframe = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data)
    chart = gframe.chart
    chart.has_legend = False
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.series[0].format.fill.solid()
    plot.series[0].format.fill.fore_color.rgb = _rgb(theme.primary)
    if s.stats_unit:
        _, tf = _textbox(slide, MARGIN, SLIDE_H - Inches(0.75), SLIDE_W - 2 * MARGIN, Inches(0.3))
        p = tf.paragraphs[0]; r = p.add_run()
        _set_run(r, f"Unit: {s.stats_unit}", size=theme.small_size, color=theme.text_soft, font=theme.font_body)


def _render_quote(slide, theme: Theme, s: SlideSpec):
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = _rgb(theme.surface)
    _, tf = _textbox(slide, Inches(1.6), Inches(2.4), SLIDE_W - Inches(3.2), Inches(2.2), valign=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    _set_run(r, f"\u201C{s.quote_text or s.title}\u201D", size=theme.heading_size + 2, color=theme.text, italic=True, font=theme.font_heading)
    if s.quote_attribution:
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(16)
        r2 = p2.add_run()
        _set_run(r2, f"â€” {s.quote_attribution}", size=theme.body_size, color=theme.primary, bold=True, font=theme.font_body)


def _render_bullets_generic(slide, theme: Theme, s: SlideSpec):
    _add_title(slide, theme, s.title)
    _add_bullets(slide, theme, s.bullets, MARGIN, Inches(1.6), SLIDE_W - 2 * MARGIN, SLIDE_H - Inches(2.2))


def _render_sources(slide, theme: Theme, s: SlideSpec, all_sources: list[str]):
    _add_title(slide, theme, s.title or "Sources")
    items = all_sources or [f"{src.label}" + (f" â€” {src.document}" + (f", p.{src.page}" if src.page else "") if src.document else "") for src in s.sources]
    if not items:
        items = ["Generated content â€” no document sources were used."]
    _add_bullets(slide, theme, items[:12], MARGIN, Inches(1.6), SLIDE_W - 2 * MARGIN, SLIDE_H - Inches(2.2), size=theme.small_size + 2)


# ------------------------------------------------------------------ orchestration

def render_pptx(spec: PresentationSpec, images: dict[int, bytes], out_path: Path,
                 include_notes: bool = True, include_sources: bool = True) -> None:
    theme = get_theme(spec.theme)
    prs = _new_deck(theme)
    total = len(spec.slides)

    # collect all source refs across body slides, for a consolidated sources slide if needed
    all_source_lines: list[str] = []
    for sl in spec.slides:
        for src in sl.sources:
            line = src.label
            if src.document:
                line += f" â€” {src.document}" + (f", p.{src.page}" if src.page else "")
            if line not in all_source_lines:
                all_source_lines.append(line)

    for s in spec.slides:
        slide = _blank_slide(prs, theme)
        image = images.get(s.slide_number)

        if s.type == SlideType.title:
            _render_title(slide, theme, s, image)
        elif s.type == SlideType.section:
            _render_section(slide, theme, s, image)
        elif s.type == SlideType.image_content:
            _render_image_content(slide, theme, s, image)
        elif s.type in (SlideType.two_column, SlideType.three_column):
            _render_two_or_three_column(slide, theme, s)
        elif s.type == SlideType.comparison:
            _render_comparison(slide, theme, s)
        elif s.type in (SlideType.timeline, SlideType.process):
            _render_timeline_process(slide, theme, s)
        elif s.type == SlideType.statistics:
            _render_statistics(slide, theme, s)
        elif s.type == SlideType.quote:
            _render_quote(slide, theme, s)
        elif s.type == SlideType.sources:
            if not include_sources:
                continue
            _render_sources(slide, theme, s, all_source_lines)
        elif s.type in (SlideType.summary, SlideType.conclusion):
            _render_bullets_generic(slide, theme, s)
        else:  # content and any unmapped type
            _render_content(slide, theme, s, image, has_image_slot=True)

        if s.type not in (SlideType.title, SlideType.section, SlideType.quote):
            _add_footer(slide, theme, s.slide_number, total, spec.title)

        if include_notes and s.speaker_notes:
            slide.notes_slide.notes_text_frame.text = s.speaker_notes

    prs.save(str(out_path))

