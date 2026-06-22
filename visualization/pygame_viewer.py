from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from physics.constants import AU, DAY
from physics.engine import accelerations_for_bodies
from physics.quantities import angular_momentum_z, kinetic_energy, potential_energy, total_energy
from simulation.simulator import NBodySimulator


def _load_pygame():
    try:
        import pygame
    except ImportError as exc:
        raise RuntimeError("pygame is required for visualization. Install with: pip install pygame") from exc
    return pygame


@dataclass
class Camera:
    width: int
    height: int
    zoom: float = 260.0 / AU
    offset: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=float))

    def world_to_screen(self, point: np.ndarray) -> tuple[int, int]:
        centered = (point - self.offset) * self.zoom
        return int(self.width / 2 + centered[0]), int(self.height / 2 + centered[1])

    def screen_to_world(self, point: tuple[int, int]) -> np.ndarray:
        screen = np.array([point[0] - self.width / 2, point[1] - self.height / 2], dtype=float)
        return screen / self.zoom + self.offset


class PygameViewer:
    def __init__(self, simulator: NBodySimulator, *, width: int = 1280, height: int = 820) -> None:
        self.pygame = _load_pygame()
        self.simulator = simulator
        self.camera = Camera(width, height)
        self.paused = False
        self.steps_per_frame = 3
        self.show_velocity = True
        self.show_force = False
        self.show_trails = True
        self.selected_index = 1 if len(simulator.bodies) > 1 else 0
        self.trails = [deque(maxlen=1300) for _ in simulator.bodies]

    def run(self) -> None:
        pygame = self.pygame
        pygame.init()
        screen = pygame.display.set_mode((self.camera.width, self.camera.height))
        pygame.display.set_caption("Orbital Dynamics and Stability Simulation")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("consolas", 16)
        small_font = pygame.font.SysFont("consolas", 13)
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse(event.button, event.pos)

            keys = pygame.key.get_pressed()
            self._handle_camera_keys(keys)

            if not self.paused:
                for _ in range(self.steps_per_frame):
                    self.simulator.step()

            for index, body in enumerate(self.simulator.bodies):
                self.trails[index].append(body.position.copy())

            screen.fill((8, 10, 14))
            self._draw_grid(screen)
            if self.show_trails:
                self._draw_trails(screen)
            self._draw_vectors(screen)
            self._draw_bodies(screen, font)
            self._draw_panel(screen, font, small_font)
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _handle_key(self, key: int) -> None:
        pygame = self.pygame
        if key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key in (pygame.K_EQUALS, pygame.K_PLUS):
            self.camera.zoom *= 1.2
        elif key == pygame.K_MINUS:
            self.camera.zoom /= 1.2
        elif key == pygame.K_PERIOD:
            self.steps_per_frame = min(self.steps_per_frame + 1, 200)
        elif key == pygame.K_COMMA:
            self.steps_per_frame = max(self.steps_per_frame - 1, 1)
        elif key == pygame.K_v:
            self.show_velocity = not self.show_velocity
        elif key == pygame.K_f:
            self.show_force = not self.show_force
        elif key == pygame.K_t:
            self.show_trails = not self.show_trails
        elif key == pygame.K_TAB:
            self.selected_index = (self.selected_index + 1) % len(self.simulator.bodies)
        elif key == pygame.K_c:
            self.camera.offset = self.simulator.bodies[self.selected_index].position.copy()

    def _handle_mouse(self, button: int, pos: tuple[int, int]) -> None:
        if button == 1:
            mouse = np.array(pos, dtype=float)
            best_index = self.selected_index
            best_distance = np.inf
            for index, body in enumerate(self.simulator.bodies):
                screen_pos = np.array(self.camera.world_to_screen(body.position), dtype=float)
                distance = float(np.linalg.norm(screen_pos - mouse))
                if distance < best_distance:
                    best_index = index
                    best_distance = distance
            if best_distance < 35.0:
                self.selected_index = best_index
        elif button == 4:
            self.camera.zoom *= 1.1
        elif button == 5:
            self.camera.zoom /= 1.1

    def _handle_camera_keys(self, keys) -> None:
        pygame = self.pygame
        step = 18.0 / self.camera.zoom
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.camera.offset[0] -= step
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.camera.offset[0] += step
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.camera.offset[1] -= step
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.camera.offset[1] += step

    def _draw_grid(self, screen) -> None:
        pygame = self.pygame
        color = (25, 30, 38)
        for au in range(-10, 11):
            x1 = self.camera.world_to_screen(np.array([au * AU, -10 * AU], dtype=float))
            x2 = self.camera.world_to_screen(np.array([au * AU, 10 * AU], dtype=float))
            y1 = self.camera.world_to_screen(np.array([-10 * AU, au * AU], dtype=float))
            y2 = self.camera.world_to_screen(np.array([10 * AU, au * AU], dtype=float))
            pygame.draw.line(screen, color, x1, x2, 1)
            pygame.draw.line(screen, color, y1, y2, 1)

    def _draw_trails(self, screen) -> None:
        pygame = self.pygame
        for body, trail in zip(self.simulator.bodies, self.trails):
            if len(trail) < 2:
                continue
            points = [self.camera.world_to_screen(point) for point in trail]
            pygame.draw.lines(screen, tuple(max(20, c // 2) for c in body.color), False, points, 1)

    def _draw_vectors(self, screen) -> None:
        pygame = self.pygame
        accelerations = accelerations_for_bodies(self.simulator.bodies, softening=self.simulator.softening)
        for index, body in enumerate(self.simulator.bodies):
            start = np.array(self.camera.world_to_screen(body.position), dtype=float)
            if self.show_velocity:
                velocity_end = start + body.velocity * (0.0015 * self.camera.zoom * AU / 30_000.0)
                pygame.draw.line(screen, (80, 220, 160), start, velocity_end, 2)
            if self.show_force:
                acceleration = accelerations[index]
                norm = np.linalg.norm(acceleration)
                if norm > 0:
                    force_end = start + acceleration / norm * 48.0
                    pygame.draw.line(screen, (255, 130, 90), start, force_end, 2)

    def _draw_bodies(self, screen, font) -> None:
        pygame = self.pygame
        for index, body in enumerate(self.simulator.bodies):
            screen_pos = self.camera.world_to_screen(body.position)
            draw_radius = max(4, min(18, int(np.log10(body.radius) * 1.6)))
            if index == self.selected_index:
                pygame.draw.circle(screen, (255, 255, 255), screen_pos, draw_radius + 5, 1)
            pygame.draw.circle(screen, body.color, screen_pos, draw_radius)
            label = font.render(body.name, True, (220, 225, 235))
            screen.blit(label, (screen_pos[0] + draw_radius + 4, screen_pos[1] - 8))

    def _draw_panel(self, screen, font, small_font) -> None:
        pygame = self.pygame
        panel = pygame.Rect(14, 14, 405, 238)
        pygame.draw.rect(screen, (14, 18, 25), panel)
        pygame.draw.rect(screen, (55, 65, 78), panel, 1)
        selected = self.simulator.bodies[self.selected_index]
        energy = total_energy(self.simulator.bodies, softening=self.simulator.softening)
        lines = [
            f"time: {self.simulator.time / DAY:9.2f} days",
            f"dt: {self.simulator.dt:9.1f} s   steps/frame: {self.steps_per_frame}",
            f"selected: {selected.name}",
            f"speed: {selected.speed / 1000.0:9.3f} km/s",
            f"radius from origin: {np.linalg.norm(selected.position) / AU:9.3f} AU",
            f"kinetic: {kinetic_energy(self.simulator.bodies): .4e} J",
            f"potential: {potential_energy(self.simulator.bodies, softening=self.simulator.softening): .4e} J",
            f"total energy: {energy: .4e} J",
            f"angular momentum z: {angular_momentum_z(self.simulator.bodies): .4e}",
            f"toggles: space pause, v velocity, f force, t trails, tab select",
        ]
        for row, text in enumerate(lines):
            surface = (font if row < 9 else small_font).render(text, True, (225, 230, 238))
            screen.blit(surface, (26, 26 + row * 21))
