from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pygame

from app.theme import THEME, blend


@dataclass
class Fonts:
    title: pygame.font.Font
    heading: pygame.font.Font
    body: pygame.font.Font
    small: pygame.font.Font
    mono: pygame.font.Font


def load_fonts() -> Fonts:
    return Fonts(
        title=pygame.font.SysFont("segoeui", 24, bold=True),
        heading=pygame.font.SysFont("segoeui", 17, bold=True),
        body=pygame.font.SysFont("segoeui", 15),
        small=pygame.font.SysFont("segoeui", 12),
        mono=pygame.font.SysFont("consolas", 13),
    )


def draw_text(surface, font, text: str, pos: tuple[int, int], color=THEME.text, *, max_width: int | None = None) -> None:
    if max_width is None:
        surface.blit(font.render(text, True, color), pos)
        return
    words = text.split()
    line = ""
    y = pos[1]
    for word in words:
        trial = word if not line else f"{line} {word}"
        if font.size(trial)[0] <= max_width:
            line = trial
        else:
            surface.blit(font.render(line, True, color), (pos[0], y))
            y += font.get_height() + 3
            line = word
    if line:
        surface.blit(font.render(line, True, color), (pos[0], y))


def panel(surface, rect: pygame.Rect, *, title: str | None = None, font: pygame.font.Font | None = None) -> None:
    pygame.draw.rect(surface, THEME.panel, rect, border_radius=8)
    pygame.draw.rect(surface, THEME.panel_edge, rect, width=1, border_radius=8)
    if title and font is not None:
        draw_text(surface, font, title, (rect.x + 14, rect.y + 10), THEME.text)


def button(
    surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    mouse_pos: tuple[int, int],
    *,
    active: bool = False,
    danger: bool = False,
) -> bool:
    hovered = rect.collidepoint(mouse_pos)
    base = THEME.danger if danger else (THEME.accent if active else THEME.panel_alt)
    color = blend(base, (255, 255, 255), 0.12 if hovered else 0.0)
    pygame.draw.rect(surface, color, rect, border_radius=6)
    pygame.draw.rect(surface, THEME.panel_edge_hot if hovered or active else THEME.panel_edge, rect, width=1, border_radius=6)
    label = font.render(text, True, THEME.text)
    surface.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
    return hovered


def segmented(
    surface,
    rect: pygame.Rect,
    labels: Sequence[str],
    active_label: str,
    font: pygame.font.Font,
    mouse_pos: tuple[int, int],
) -> list[tuple[str, pygame.Rect, bool]]:
    width = rect.w // max(len(labels), 1)
    result = []
    for index, label in enumerate(labels):
        item = pygame.Rect(rect.x + index * width, rect.y, width, rect.h)
        if index == len(labels) - 1:
            item.w = rect.right - item.x
        result.append((label, item, button(surface, item, label, font, mouse_pos, active=label == active_label)))
    return result


def metric_row(surface, font, label: str, value: str, x: int, y: int, width: int, color=THEME.text) -> None:
    draw_text(surface, font, label, (x, y), THEME.muted)
    value_surface = font.render(value, True, color)
    surface.blit(value_surface, (x + width - value_surface.get_width(), y))


def mini_chart(
    surface,
    rect: pygame.Rect,
    values: Sequence[float],
    font: pygame.font.Font,
    title: str,
    color=THEME.accent,
) -> None:
    pygame.draw.rect(surface, (8, 13, 21), rect, border_radius=6)
    pygame.draw.rect(surface, THEME.chart_grid, rect, width=1, border_radius=6)
    draw_text(surface, font, title, (rect.x + 8, rect.y + 6), THEME.muted)
    if len(values) < 2:
        return
    finite = [float(v) for v in values if abs(float(v)) < 1.0e300]
    if len(finite) < 2:
        return
    v_min = min(finite)
    v_max = max(finite)
    if v_max == v_min:
        v_max = v_min + 1.0
    inner = rect.inflate(-16, -32)
    points = []
    for index, value in enumerate(finite[-180:]):
        x = inner.x + int(index * inner.w / max(len(finite[-180:]) - 1, 1))
        t = (value - v_min) / (v_max - v_min)
        y = inner.bottom - int(t * inner.h)
        points.append((x, y))
    if len(points) >= 2:
        pygame.draw.aalines(surface, color, False, points)


def draw_status_pill(surface, font, rect: pygame.Rect, text: str) -> None:
    color = THEME.accent
    if "Stable" in text:
        color = THEME.stable
    elif "Escape" in text or "Collision" in text:
        color = THEME.danger
    elif "Chaotic" in text or "Sensitive" in text:
        color = THEME.warning
    pygame.draw.rect(surface, (9, 14, 22), rect, border_radius=rect.h // 2)
    pygame.draw.rect(surface, color, rect, width=1, border_radius=rect.h // 2)
    label = font.render(text, True, color)
    surface.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
