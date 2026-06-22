from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from physics.constants import AU


@dataclass
class SpaceCamera:
    """A smooth 2.5D camera for a 2D orbital plane.

    The physics engine remains 2D. The presentation camera treats the plane as a
    tilted 3D surface with yaw and pitch so the viewport feels like a space
    exploration tool rather than a flat classroom plot.
    """

    zoom: float = 330.0 / AU
    target_zoom: float = 330.0 / AU
    focus: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=float))
    target_focus: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=float))
    yaw: float = 0.0
    target_yaw: float = 0.0
    pitch: float = 0.45
    target_pitch: float = 0.45
    mode: str = "free"
    cinematic_rate: float = 0.08

    def update(self, dt: float, follow_position: np.ndarray | None = None) -> None:
        if self.mode == "follow" and follow_position is not None:
            self.target_focus = follow_position.copy()
        elif self.mode == "cinematic":
            self.target_yaw += self.cinematic_rate * dt
            if follow_position is not None:
                self.target_focus = follow_position.copy()
            self.target_pitch = 0.66

        smooth = 1.0 - pow(0.001, min(dt, 0.2))
        self.focus += (self.target_focus - self.focus) * smooth
        self.zoom += (self.target_zoom - self.zoom) * smooth
        self.yaw += (self.target_yaw - self.yaw) * smooth
        self.pitch += (self.target_pitch - self.pitch) * smooth

    def project(self, position: np.ndarray, viewport) -> tuple[int, int, float]:
        relative = position - self.focus
        cos_yaw = np.cos(self.yaw)
        sin_yaw = np.sin(self.yaw)
        rotated_x = relative[0] * cos_yaw - relative[1] * sin_yaw
        rotated_y = relative[0] * sin_yaw + relative[1] * cos_yaw
        tilted_y = rotated_y * np.cos(self.pitch)

        center_x = viewport.x + viewport.w / 2
        center_y = viewport.y + viewport.h / 2
        screen_x = center_x + rotated_x * self.zoom
        screen_y = center_y + tilted_y * self.zoom
        depth = rotated_y * np.sin(self.pitch)
        return int(screen_x), int(screen_y), float(depth)

    def screen_to_world_delta(self, delta_pixels: tuple[float, float]) -> np.ndarray:
        dx = -delta_pixels[0] / self.zoom
        dy = -delta_pixels[1] / max(self.zoom * np.cos(self.pitch), 1.0e-12)
        cos_yaw = np.cos(-self.yaw)
        sin_yaw = np.sin(-self.yaw)
        return np.array([dx * cos_yaw - dy * sin_yaw, dx * sin_yaw + dy * cos_yaw], dtype=float)

    def pan_pixels(self, delta_pixels: tuple[float, float]) -> None:
        self.target_focus += self.screen_to_world_delta(delta_pixels)

    def zoom_by(self, factor: float) -> None:
        self.target_zoom = float(np.clip(self.target_zoom * factor, 8.0 / AU, 10_000.0 / AU))

    def rotate_by(self, yaw_delta: float, pitch_delta: float = 0.0) -> None:
        self.target_yaw += yaw_delta
        self.target_pitch = float(np.clip(self.target_pitch + pitch_delta, 0.0, 1.25))

    def follow(self, position: np.ndarray) -> None:
        self.mode = "follow"
        self.target_focus = position.copy()

    def free(self) -> None:
        self.mode = "free"

    def cinematic(self) -> None:
        self.mode = "cinematic"
