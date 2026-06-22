from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np
import pygame

from app.camera import SpaceCamera
from app.theme import THEME, blend
from physics.constants import AU
from physics.engine import accelerations_for_bodies


@dataclass
class Star:
    x: int
    y: int
    radius: int
    brightness: int


@dataclass
class SpaceRenderer:
    width: int
    height: int
    trails: list[deque[np.ndarray]] = field(default_factory=list)
    starfield: list[Star] = field(default_factory=list)

    def __post_init__(self) -> None:
        rng = np.random.default_rng(42)
        for _ in range(700):
            self.starfield.append(
                Star(
                    int(rng.integers(0, self.width)),
                    int(rng.integers(0, self.height)),
                    int(rng.choice([1, 1, 1, 2])),
                    int(rng.integers(70, 235)),
                )
            )

    def ensure_trails(self, body_count: int, limit: int) -> None:
        if len(self.trails) != body_count or any(trail.maxlen != limit for trail in self.trails):
            self.trails = [deque(maxlen=limit) for _ in range(body_count)]

    def record_trails(self, bodies) -> None:
        self.ensure_trails(len(bodies), 1500)
        for index, body in enumerate(bodies):
            self.trails[index].append(body.position.copy())

    def clear_trails(self) -> None:
        for trail in self.trails:
            trail.clear()

    def draw_background(self, surface, viewport: pygame.Rect, camera: SpaceCamera) -> None:
        for y in range(viewport.y, viewport.bottom):
            t = (y - viewport.y) / max(viewport.h, 1)
            pygame.draw.line(surface, blend(THEME.space_top, THEME.space_bottom, t), (viewport.x, y), (viewport.right, y))

        for star in self.starfield:
            x = viewport.x + int((star.x + camera.yaw * 18.0 * star.radius) % max(viewport.w, 1))
            y = viewport.y + int((star.y + camera.pitch * 22.0 * star.radius) % max(viewport.h, 1))
            if viewport.collidepoint(x, y):
                pygame.draw.circle(surface, (star.brightness, star.brightness, star.brightness), (x, y), star.radius)

    def draw_orbit_plane(self, surface, viewport: pygame.Rect, camera: SpaceCamera) -> None:
        for au in range(-12, 13):
            p1 = camera.project(np.array([au * AU, -12 * AU], dtype=float), viewport)
            p2 = camera.project(np.array([au * AU, 12 * AU], dtype=float), viewport)
            p3 = camera.project(np.array([-12 * AU, au * AU], dtype=float), viewport)
            p4 = camera.project(np.array([12 * AU, au * AU], dtype=float), viewport)
            color = (23, 34, 48) if au != 0 else (45, 72, 102)
            pygame.draw.aaline(surface, color, p1[:2], p2[:2])
            pygame.draw.aaline(surface, color, p3[:2], p4[:2])

    def draw_trails(self, surface, viewport: pygame.Rect, camera: SpaceCamera, bodies) -> None:
        trail_surface = pygame.Surface((viewport.w, viewport.h), pygame.SRCALPHA)
        for body, trail in zip(bodies, self.trails):
            if len(trail) < 3:
                continue
            points = []
            for point in trail:
                projected = camera.project(point, viewport)
                points.append((projected[0] - viewport.x, projected[1] - viewport.y))
            color = (*tuple(max(60, min(255, c)) for c in body.color), 150)
            if len(points) > 2:
                pygame.draw.aalines(trail_surface, color, False, points)
        surface.blit(trail_surface, viewport.topleft)

    def draw_vectors(self, surface, viewport: pygame.Rect, camera: SpaceCamera, bodies, state) -> None:
        accelerations = accelerations_for_bodies(bodies, softening=state.simulator.softening)
        for index, body in enumerate(bodies):
            start_projected = camera.project(body.position, viewport)
            start = np.array(start_projected[:2], dtype=float)
            if state.show_velocity_vectors:
                scale = 0.0017 * camera.zoom * AU / 30_000.0
                end = start + body.velocity * scale
                pygame.draw.aaline(surface, THEME.accent_2, tuple(start), tuple(end))
                pygame.draw.circle(surface, THEME.accent_2, (int(end[0]), int(end[1])), 2)
            if state.show_force_vectors:
                acceleration = accelerations[index]
                norm = np.linalg.norm(acceleration)
                if norm > 0:
                    end = start + acceleration / norm * 50.0
                    pygame.draw.aaline(surface, THEME.danger, tuple(start), tuple(end))

    def draw_bodies(self, surface, viewport: pygame.Rect, camera: SpaceCamera, bodies, state, font) -> None:
        projected = [(index, body, camera.project(body.position, viewport)) for index, body in enumerate(bodies)]
        projected.sort(key=lambda item: item[2][2])

        glow_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        for index, body, projection in projected:
            x, y, depth = projection
            if not viewport.collidepoint(x, y):
                continue
            radius = self._screen_radius(body.radius, camera.zoom)
            glow = max(radius * 3, 18)
            alpha = 34 if index != state.selected_index else 68
            for layer in range(3, 0, -1):
                pygame.draw.circle(glow_surface, (*body.color, alpha // layer), (x, y), glow * layer // 2)
        surface.blit(glow_surface, (0, 0))

        for index, body, projection in projected:
            x, y, depth = projection
            if not viewport.collidepoint(x, y):
                continue
            radius = self._screen_radius(body.radius, camera.zoom)
            lit = blend(tuple(max(30, c // 2) for c in body.color), body.color, 0.78)
            pygame.draw.circle(surface, lit, (x, y), radius)
            pygame.draw.circle(surface, blend(lit, (255, 255, 255), 0.3), (x - radius // 3, y - radius // 3), max(1, radius // 3))
            if index == state.selected_index:
                pygame.draw.circle(surface, THEME.accent, (x, y), radius + 7, width=1)
                pygame.draw.circle(surface, THEME.accent_2, (x, y), radius + 12, width=1)
            if state.show_labels and radius > 3:
                label = font.render(body.name, True, THEME.text)
                surface.blit(label, (x + radius + 6, y - label.get_height() // 2))

    @staticmethod
    def _screen_radius(real_radius: float, zoom: float) -> int:
        physical = int(real_radius * zoom)

        radius = int(np.log10(real_radius) * 2.2 + physical * 0.05)

        if real_radius < 3e6:      # moons
            radius += 5
        elif real_radius < 8e6:    # earth-like planets
            radius += 3

        return max(6, min(30, radius))
