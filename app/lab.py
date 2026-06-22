from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pygame

from app.camera import SpaceCamera
from app.metrics import LiveMetrics, format_si
from app.renderer import SpaceRenderer
from app.research import ResearchAnalyzer
from app.state import AppState
from app.theme import THEME
from app.widgets import (
    button,
    draw_status_pill,
    draw_text,
    load_fonts,
    metric_row,
    mini_chart,
    panel,
    segmented,
)
from experiments.scenarios import all_scenarios, get_scenario
from physics.constants import AU, DAY


class AstroLabApp:
    def __init__(self, scenario_key: str = "stable", *, width: int = 1600, height: int = 960) -> None:
        pygame.init()
        pygame.display.set_caption("Orbital Dynamics Laboratory")
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.fonts = load_fonts()
        self.scenarios = all_scenarios()
        self.state = AppState(get_scenario(scenario_key))
        self.camera = SpaceCamera()
        self.renderer = SpaceRenderer(width, height)
        self.metrics = LiveMetrics()
        self.research = ResearchAnalyzer()
        self.running = True
        self.dragging_view = False
        self.last_mouse = (0, 0)
        self.message = "Ready"
        self._layout()

    def _layout(self) -> None:
        width, height = self.screen.get_size()
        self.top_bar = pygame.Rect(0, 0, width, 64)
        self.left_panel = pygame.Rect(12, 76, 285, height - 340)
        self.right_panel = pygame.Rect(width - 360, 76, 348, height - 340)
        self.bottom_panel = pygame.Rect(12, height - 252, width - 24, 240)
        self.viewport = pygame.Rect(self.left_panel.right + 12, 76, self.right_panel.x - self.left_panel.right - 24, height - 340)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self.renderer.width, self.renderer.height = event.size
                self._layout()
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event, mouse_pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (2, 3):
                    self.dragging_view = False
            elif event.type == pygame.MOUSEMOTION and self.dragging_view:
                self.camera.pan_pixels(event.rel)

    def _handle_key(self, event) -> None:
        key = event.key
        if key == pygame.K_SPACE:
            self.state.paused = not self.state.paused
        elif key == pygame.K_r:
            self._reset()
        elif key in (pygame.K_EQUALS, pygame.K_PLUS):
            self.camera.zoom_by(1.18)
        elif key == pygame.K_MINUS:
            self.camera.zoom_by(1 / 1.18)
        elif key == pygame.K_LEFTBRACKET:
            self.camera.rotate_by(-0.12)
        elif key == pygame.K_RIGHTBRACKET:
            self.camera.rotate_by(0.12)
        elif key == pygame.K_UP:
            self.camera.rotate_by(0.0, 0.08)
        elif key == pygame.K_DOWN:
            self.camera.rotate_by(0.0, -0.08)
        elif key == pygame.K_TAB:
            self.state.selected_index = (self.state.selected_index + 1) % len(self.state.simulator.bodies)
            self.camera.follow(self.state.selected_body().position)
        elif key == pygame.K_BACKSPACE:
            self.state.search_text = self.state.search_text[:-1]
        elif event.unicode and len(event.unicode) == 1 and event.unicode.isprintable():
            if self.left_panel.collidepoint(pygame.mouse.get_pos()):
                self.state.search_text += event.unicode

    def _handle_mouse_down(self, event, mouse_pos: tuple[int, int]) -> None:
        if event.button == 4:
            self.camera.zoom_by(1.12)
        elif event.button == 5:
            self.camera.zoom_by(1 / 1.12)
        elif event.button in (2, 3) and self.viewport.collidepoint(mouse_pos):
            self.dragging_view = True
        elif event.button == 1:
            self._click(mouse_pos)

    def _click(self, mouse_pos: tuple[int, int]) -> None:
        self._click_top_bar(mouse_pos)
        self._click_left_panel(mouse_pos)
        self._click_right_panel(mouse_pos)
        self._click_bottom_panel(mouse_pos)
        if self.viewport.collidepoint(mouse_pos):
            self._select_body_at(mouse_pos)

    def _click_top_bar(self, mouse_pos: tuple[int, int]) -> None:
        y = 16
        x = 238
        actions = [
            ("Play", pygame.Rect(x, y, 72, 34), lambda: setattr(self.state, "paused", False)),
            ("Pause", pygame.Rect(x + 80, y, 78, 34), lambda: setattr(self.state, "paused", True)),
            ("Reset", pygame.Rect(x + 166, y, 78, 34), self._reset),
            ("Analyze", pygame.Rect(x + 252, y, 96, 34), self._analyze),
        ]
        for _, rect, callback in actions:
            if rect.collidepoint(mouse_pos):
                callback()
        speed_minus = pygame.Rect(460, y, 34, 34)
        speed_plus = pygame.Rect(606, y, 34, 34)
        if speed_minus.collidepoint(mouse_pos):
            self.state.steps_per_frame = max(1, self.state.steps_per_frame - 1)
        if speed_plus.collidepoint(mouse_pos):
            self.state.steps_per_frame = min(240, self.state.steps_per_frame + 1)

        for label, rect, hovered in self._camera_mode_rects(mouse_pos):
            if rect.collidepoint(mouse_pos):
                if label == "Free":
                    self.camera.free()
                elif label == "Follow":
                    self.camera.follow(self.state.selected_body().position)
                elif label == "Cinema":
                    self.camera.cinematic()

    def _click_left_panel(self, mouse_pos: tuple[int, int]) -> None:
        x = self.left_panel.x + 14
        y = self.left_panel.y + 96
        for key, scenario in self.scenarios.items():
            rect = pygame.Rect(x, y, self.left_panel.w - 28, 32)
            if rect.collidepoint(mouse_pos):
                self.state.load_scenario(scenario)
                self.metrics.reset()
                self.renderer.clear_trails()
                self.camera.target_focus = np.zeros(2, dtype=float)
                self.message = f"Loaded {scenario.title}"
            y += 38

        y = self.left_panel.y + 326
        for index, body in enumerate(self.state.simulator.bodies):
            if not self.state.body_matches_search(body):
                continue
            rect = pygame.Rect(x, y, self.left_panel.w - 28, 30)
            if rect.collidepoint(mouse_pos):
                self.state.selected_index = index
                self.camera.follow(body.position)
                self.message = f"Selected {body.name}"
            y += 34

    def _click_right_panel(self, mouse_pos: tuple[int, int]) -> None:
        x = self.right_panel.x + 18
        y = self.right_panel.y + self.right_panel.h - 142
        actions = [
            ("Mass +", pygame.Rect(x, y, 96, 30), lambda: self.state.scale_selected_mass(1.05)),
            ("Mass -", pygame.Rect(x + 104, y, 96, 30), lambda: self.state.scale_selected_mass(1 / 1.05)),
            ("Vel +", pygame.Rect(x, y + 38, 96, 30), lambda: self.state.scale_selected_velocity(1.03)),
            ("Vel -", pygame.Rect(x + 104, y + 38, 96, 30), lambda: self.state.scale_selected_velocity(1 / 1.03)),
            ("Nudge", pygame.Rect(x, y + 76, 96, 30), lambda: self.state.nudge_selected_position(np.array([1.0, 0.0]), 0.02 * AU)),
            ("Rerun", pygame.Rect(x + 104, y + 76, 96, 30), self._reset),
        ]
        for _, rect, callback in actions:
            if rect.collidepoint(mouse_pos):
                callback()
                self.message = "Experiment parameters updated"

    def _click_bottom_panel(self, mouse_pos: tuple[int, int]) -> None:
        labels = ["Metrics", "Graphs", "Research"]
        tab_rect = pygame.Rect(self.bottom_panel.x + 18, self.bottom_panel.y + 14, 330, 32)
        width = tab_rect.w // len(labels)
        for index, label in enumerate(labels):
            rect = pygame.Rect(tab_rect.x + index * width, tab_rect.y, width, tab_rect.h)
            if rect.collidepoint(mouse_pos):
                self.state.active_bottom_tab = label

    def _select_body_at(self, mouse_pos: tuple[int, int]) -> None:
        best_index = None
        best_distance = 1.0e9
        for index, body in enumerate(self.state.simulator.bodies):
            x, y, _ = self.camera.project(body.position, self.viewport)
            distance = ((x - mouse_pos[0]) ** 2 + (y - mouse_pos[1]) ** 2) ** 0.5
            if distance < best_distance:
                best_distance = distance
                best_index = index
        if best_index is not None and best_distance < 34:
            self.state.selected_index = best_index
            self.message = f"Selected {self.state.selected_body().name}"

    def _update(self, dt: float) -> None:
        if not self.state.paused:
            for _ in range(self.state.steps_per_frame):
                self.state.simulator.step()
        self.renderer.ensure_trails(len(self.state.simulator.bodies), self.state.trail_limit)
        self.renderer.record_trails(self.state.simulator.bodies)
        follow = self.state.selected_body().position if self.camera.mode in {"follow", "cinematic"} else None
        self.camera.update(dt, follow)

        snapshot = self.metrics.snapshot(self.state)
        if len(self.state.series.time_days) == 0 or self.state.elapsed_days() - self.state.series.time_days[-1] > 0.08:
            self.metrics.record(self.state, snapshot)
        self.current_snapshot = snapshot

    def _draw(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(THEME.background)
        self._draw_viewport()
        self._draw_top_bar(mouse_pos)
        self._draw_left_panel(mouse_pos)
        self._draw_right_panel(mouse_pos)
        self._draw_bottom_panel(mouse_pos)
        pygame.display.flip()

    def _draw_viewport(self) -> None:
        self.renderer.draw_background(self.screen, self.viewport, self.camera)
        if self.state.show_orbit_plane:
            self.renderer.draw_orbit_plane(self.screen, self.viewport, self.camera)
        if self.state.show_trails:
            self.renderer.draw_trails(self.screen, self.viewport, self.camera, self.state.simulator.bodies)
        self.renderer.draw_vectors(self.screen, self.viewport, self.camera, self.state.simulator.bodies, self.state)
        self.renderer.draw_bodies(self.screen, self.viewport, self.camera, self.state.simulator.bodies, self.state, self.fonts.small)
        pygame.draw.rect(self.screen, THEME.panel_edge, self.viewport, width=1, border_radius=8)

    def _draw_top_bar(self, mouse_pos: tuple[int, int]) -> None:
        pygame.draw.rect(self.screen, (9, 14, 23), self.top_bar)
        pygame.draw.line(self.screen, THEME.panel_edge, (0, self.top_bar.bottom - 1), (self.top_bar.w, self.top_bar.bottom - 1))
        draw_text(self.screen, self.fonts.title, "Orbital Dynamics Laboratory", (18, 18), THEME.text)
        y = 16
        x = 238
        button(self.screen, pygame.Rect(x, y, 72, 34), "Play", self.fonts.body, mouse_pos, active=not self.state.paused)
        button(self.screen, pygame.Rect(x + 80, y, 78, 34), "Pause", self.fonts.body, mouse_pos, active=self.state.paused)
        button(self.screen, pygame.Rect(x + 166, y, 78, 34), "Reset", self.fonts.body, mouse_pos)
        button(self.screen, pygame.Rect(x + 252, y, 96, 34), "Analyze", self.fonts.body, mouse_pos, active=self.state.analysis_result is not None)
        draw_text(self.screen, self.fonts.small, "Simulation Speed", (460, 7), THEME.muted)
        button(self.screen, pygame.Rect(460, y, 34, 34), "-", self.fonts.heading, mouse_pos)
        speed_rect = pygame.Rect(500, y, 100, 34)
        pygame.draw.rect(self.screen, THEME.panel_alt, speed_rect, border_radius=6)
        draw_text(self.screen, self.fonts.body, f"{self.state.steps_per_frame}x", (speed_rect.centerx - 16, speed_rect.y + 8), THEME.text)
        button(self.screen, pygame.Rect(606, y, 34, 34), "+", self.fonts.heading, mouse_pos)
        draw_text(self.screen, self.fonts.small, "Camera", (690, 7), THEME.muted)
        self._camera_mode_rects(mouse_pos, draw=True)
        draw_text(self.screen, self.fonts.mono, self.message, (self.top_bar.w - 350, 23), THEME.muted)

    def _camera_mode_rects(self, mouse_pos: tuple[int, int], *, draw: bool = False):
        rect = pygame.Rect(690, 16, 250, 34)
        labels = ["Free", "Follow", "Cinema"]
        active = {"free": "Free", "follow": "Follow", "cinematic": "Cinema"}.get(self.camera.mode, "Free")
        if draw:
            return segmented(self.screen, rect, labels, active, self.fonts.small, mouse_pos)
        width = rect.w // len(labels)
        return [(label, pygame.Rect(rect.x + i * width, rect.y, width, rect.h), False) for i, label in enumerate(labels)]

    def _draw_left_panel(self, mouse_pos: tuple[int, int]) -> None:
        panel(self.screen, self.left_panel, title="Object Explorer", font=self.fonts.heading)
        x = self.left_panel.x + 14
        search = pygame.Rect(x, self.left_panel.y + 46, self.left_panel.w - 28, 34)
        pygame.draw.rect(self.screen, (8, 13, 22), search, border_radius=6)
        pygame.draw.rect(self.screen, THEME.panel_edge, search, width=1, border_radius=6)
        query = self.state.search_text if self.state.search_text else "Search object"
        draw_text(self.screen, self.fonts.body, query, (search.x + 10, search.y + 8), THEME.text if self.state.search_text else THEME.dim)

        draw_text(self.screen, self.fonts.small, "Experiment Scenarios", (x, self.left_panel.y + 86), THEME.muted)
        y = self.left_panel.y + 106
        for key, scenario in self.scenarios.items():
            rect = pygame.Rect(x, y, self.left_panel.w - 28, 32)
            button(self.screen, rect, scenario.title.split()[0] + " " + scenario.title.split()[1], self.fonts.small, mouse_pos, active=key == self.state.scenario.key)
            y += 38

        draw_text(self.screen, self.fonts.small, "Body Hierarchy", (x, self.left_panel.y + 304), THEME.muted)
        y = self.left_panel.y + 326
        for index, body in enumerate(self.state.simulator.bodies):
            if not self.state.body_matches_search(body):
                continue
            rect = pygame.Rect(x, y, self.left_panel.w - 28, 30)
            hovered = rect.collidepoint(mouse_pos)
            color = THEME.panel_alt if index == self.state.selected_index or hovered else (13, 19, 30)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.circle(self.screen, body.color, (rect.x + 12, rect.centery), 5)
            draw_text(self.screen, self.fonts.body, body.name, (rect.x + 26, rect.y + 6), THEME.text)
            y += 34

    def _draw_right_panel(self, mouse_pos: tuple[int, int]) -> None:
        panel(self.screen, self.right_panel, title="Selected Object", font=self.fonts.heading)
        body = self.state.selected_body()
        central = self.state.central_body()
        snapshot = self.current_snapshot
        x = self.right_panel.x + 18
        y = self.right_panel.y + 48
        pygame.draw.circle(self.screen, body.color, (x + 18, y + 18), 16)
        draw_text(self.screen, self.fonts.heading, body.name, (x + 44, y + 4), THEME.text)
        draw_status_pill(self.screen, self.fonts.small, pygame.Rect(x + 44, y + 30, 150, 24), snapshot.status)
        y += 72
        metric_row(self.screen, self.fonts.mono, "Mass", format_si(body.mass, "kg"), x, y, self.right_panel.w - 36)
        metric_row(self.screen, self.fonts.mono, "Radius", format_si(body.radius / 1000.0, "km"), x, y + 24, self.right_panel.w - 36)
        metric_row(self.screen, self.fonts.mono, "Velocity", format_si(snapshot.orbital_velocity / 1000.0, "km/s"), x, y + 48, self.right_panel.w - 36)
        metric_row(self.screen, self.fonts.mono, f"Distance from {central.name}", format_si(snapshot.orbital_radius / AU, "AU"), x, y + 72, self.right_panel.w - 36)
        period = "pending" if snapshot.orbital_period is None else f"{snapshot.orbital_period / DAY:.2f} days"
        metric_row(self.screen, self.fonts.mono, "Orbital Period", period, x, y + 96, self.right_panel.w - 36)
        metric_row(self.screen, self.fonts.mono, "Total Energy", format_si(snapshot.total_energy, "J"), x, y + 120, self.right_panel.w - 36)
        metric_row(self.screen, self.fonts.mono, "Angular Momentum", format_si(snapshot.angular_momentum), x, y + 144, self.right_panel.w - 36)

        draw_text(self.screen, self.fonts.small, "Experiment Lab", (x, self.right_panel.y + self.right_panel.h - 170), THEME.muted)
        y2 = self.right_panel.y + self.right_panel.h - 142
        for label, rect in [
            ("Mass +", pygame.Rect(x, y2, 96, 30)),
            ("Mass -", pygame.Rect(x + 104, y2, 96, 30)),
            ("Vel +", pygame.Rect(x, y2 + 38, 96, 30)),
            ("Vel -", pygame.Rect(x + 104, y2 + 38, 96, 30)),
            ("Nudge", pygame.Rect(x, y2 + 76, 96, 30)),
            ("Rerun", pygame.Rect(x + 104, y2 + 76, 96, 30)),
        ]:
            button(self.screen, rect, label, self.fonts.small, mouse_pos)

    def _draw_bottom_panel(self, mouse_pos: tuple[int, int]) -> None:
        panel(self.screen, self.bottom_panel)
        segmented(
            self.screen,
            pygame.Rect(self.bottom_panel.x + 18, self.bottom_panel.y + 14, 330, 32),
            ["Metrics", "Graphs", "Research"],
            self.state.active_bottom_tab,
            self.fonts.small,
            mouse_pos,
        )
        if self.state.active_bottom_tab == "Metrics":
            self._draw_metrics_tab()
        elif self.state.active_bottom_tab == "Graphs":
            self._draw_graphs_tab()
        else:
            self._draw_research_tab()

    def _draw_metrics_tab(self) -> None:
        snapshot = self.current_snapshot
        x = self.bottom_panel.x + 24
        y = self.bottom_panel.y + 62
        columns = [
            ("Total Energy", format_si(snapshot.total_energy, "J")),
            ("Potential", format_si(snapshot.potential_energy, "J")),
            ("Kinetic", format_si(snapshot.kinetic_energy, "J")),
            ("Angular Momentum", format_si(snapshot.angular_momentum)),
            ("Orbital Velocity", format_si(snapshot.orbital_velocity / 1000.0, "km/s")),
            ("Orbital Radius", format_si(snapshot.orbital_radius / AU, "AU")),
            ("Energy Drift", f"{snapshot.energy_drift:.3e}"),
            ("Elapsed Time", f"{self.state.elapsed_days():.2f} days"),
        ]
        width = (self.bottom_panel.w - 64) // 4
        for index, (label, value) in enumerate(columns):
            cx = x + (index % 4) * width
            cy = y + (index // 4) * 64
            draw_text(self.screen, self.fonts.small, label, (cx, cy), THEME.muted)
            draw_text(self.screen, self.fonts.heading, value, (cx, cy + 20), THEME.text)

    def _draw_graphs_tab(self) -> None:
        x = self.bottom_panel.x + 24
        y = self.bottom_panel.y + 58
        chart_w = (self.bottom_panel.w - 72) // 3
        chart_h = 156
        mini_chart(self.screen, pygame.Rect(x, y, chart_w, chart_h), self.state.series.total, self.fonts.small, "Energy vs Time", THEME.accent)
        mini_chart(self.screen, pygame.Rect(x + chart_w + 12, y, chart_w, chart_h), self.state.series.selected_radius, self.fonts.small, "Distance vs Time", THEME.accent_2)
        mini_chart(self.screen, pygame.Rect(x + 2 * (chart_w + 12), y, chart_w, chart_h), self.state.series.selected_speed, self.fonts.small, "Velocity vs Time", THEME.warning)

    def _draw_research_tab(self) -> None:
        x = self.bottom_panel.x + 24
        y = self.bottom_panel.y + 62
        if not self.state.research_summary:
            draw_text(self.screen, self.fonts.heading, "Press Analyze System to generate a scientific summary.", (x, y), THEME.text)
            draw_text(self.screen, self.fonts.body, "The analysis runs the same physics engine headlessly and reports stability, period, energy drift, collision margin, escape evidence, and chaos indicators.", (x, y + 34), THEME.muted, max_width=self.bottom_panel.w - 70)
            return
        for index, line in enumerate(self.state.research_summary):
            draw_text(self.screen, self.fonts.body, line, (x, y + index * 24), THEME.text if index < 2 else THEME.muted)

    def _reset(self) -> None:
        self.state.reset_simulator()
        self.metrics.reset()
        self.renderer.clear_trails()
        self.message = "Simulation reset"

    def _analyze(self) -> None:
        self.state.paused = True
        self.message = "Analyzing system..."
        pygame.display.flip()
        report = self.research.analyze(self.state)
        self.state.analysis_result = report.result
        self.state.research_summary = report.summary_lines
        self.state.chaos_divergence = report.divergence_m
        self.state.active_bottom_tab = "Research"
        self.message = f"Analysis complete: {report.result.label}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Professional Orbital Dynamics Laboratory")
    parser.add_argument("--scenario", choices=sorted(all_scenarios()), default="stable")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=960)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    AstroLabApp(args.scenario, width=args.width, height=args.height).run()


if __name__ == "__main__":
    main()
