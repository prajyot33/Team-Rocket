from __future__ import annotations

from dataclasses import dataclass


Color = tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    background: Color = (4, 7, 13)
    space_top: Color = (7, 12, 22)
    space_bottom: Color = (1, 4, 10)
    panel: Color = (13, 19, 30)
    panel_alt: Color = (18, 27, 42)
    panel_edge: Color = (47, 63, 86)
    panel_edge_hot: Color = (94, 140, 190)
    text: Color = (226, 233, 244)
    muted: Color = (137, 153, 176)
    dim: Color = (78, 92, 116)
    accent: Color = (98, 184, 255)
    accent_2: Color = (112, 228, 178)
    warning: Color = (255, 196, 92)
    danger: Color = (255, 108, 102)
    stable: Color = (108, 225, 157)
    chart_grid: Color = (33, 45, 62)


THEME = Theme()


def blend(a: Color, b: Color, t: float) -> Color:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )
