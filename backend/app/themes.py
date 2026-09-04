"""
Small internal design-token system. The renderer reads colors/fonts/spacing
from here instead of hardcoding values throughout services/renderer.py.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    font_heading: str
    font_body: str
    bg: str          # hex, no '#'
    surface: str
    text: str
    text_soft: str
    primary: str
    secondary: str
    accent: str
    title_size: int
    heading_size: int
    body_size: int
    small_size: int


THEMES: dict[str, Theme] = {
    "modern": Theme(
        font_heading="Calibri", font_body="Calibri",
        bg="FFFFFF", surface="F5F7FB", text="171B21", text_soft="5B6472",
        primary="2551D9", secondary="6E56CF", accent="177A45",
        title_size=40, heading_size=28, body_size=16, small_size=12,
    ),
    "corporate": Theme(
        font_heading="Georgia", font_body="Calibri",
        bg="FFFFFF", surface="EDEFF3", text="14202E", text_soft="52606D",
        primary="1B3B6F", secondary="2E5A8C", accent="B2842A",
        title_size=38, heading_size=26, body_size=16, small_size=12,
    ),
    "academic": Theme(
        font_heading="Georgia", font_body="Georgia",
        bg="FFFDF8", surface="F1EDE2", text="26221A", text_soft="6B6355",
        primary="7A3E1D", secondary="46654A", accent="A8471E",
        title_size=36, heading_size=25, body_size=15, small_size=12,
    ),
    "minimal": Theme(
        font_heading="Calibri Light", font_body="Calibri",
        bg="FFFFFF", surface="FAFAFA", text="1A1A1A", text_soft="6E6E6E",
        primary="1A1A1A", secondary="8A8A8A", accent="1A1A1A",
        title_size=40, heading_size=27, body_size=16, small_size=12,
    ),
    "dark": Theme(
        font_heading="Calibri", font_body="Calibri",
        bg="14171C", surface="1E222A", text="F2F4F8", text_soft="A9B1C4",
        primary="6E9BFF", secondary="B79CF2", accent="4FD897",
        title_size=40, heading_size=28, body_size=16, small_size=12,
    ),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["modern"])

