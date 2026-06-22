from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from analysis.stability import StabilityResult
from experiments.scenarios import Scenario
from physics.body import Body
from physics.constants import DAY, HOUR
from physics.integrators import make_integrator
from simulation.simulator import NBodySimulator


@dataclass
class TimeSeries:
    capacity: int = 900
    time_days: deque[float] = field(default_factory=lambda: deque(maxlen=900))
    kinetic: deque[float] = field(default_factory=lambda: deque(maxlen=900))
    potential: deque[float] = field(default_factory=lambda: deque(maxlen=900))
    total: deque[float] = field(default_factory=lambda: deque(maxlen=900))
    angular_momentum: deque[float] = field(default_factory=lambda: deque(maxlen=900))
    selected_speed: deque[float] = field(default_factory=lambda: deque(maxlen=900))
    selected_radius: deque[float] = field(default_factory=lambda: deque(maxlen=900))
    lyapunov: deque[float] = field(default_factory=lambda: deque(maxlen=900))

    def __post_init__(self) -> None:
        self.time_days = deque(maxlen=self.capacity)
        self.kinetic = deque(maxlen=self.capacity)
        self.potential = deque(maxlen=self.capacity)
        self.total = deque(maxlen=self.capacity)
        self.angular_momentum = deque(maxlen=self.capacity)
        self.selected_speed = deque(maxlen=self.capacity)
        self.selected_radius = deque(maxlen=self.capacity)
        self.lyapunov = deque(maxlen=self.capacity)

    def clear(self) -> None:
        for series in (
            self.time_days,
            self.kinetic,
            self.potential,
            self.total,
            self.angular_momentum,
            self.selected_speed,
            self.selected_radius,
            self.lyapunov,
        ):
            series.clear()


@dataclass
class AppState:
    scenario: Scenario
    integrator_name: str = "verlet"
    paused: bool = False
    steps_per_frame: int = 4
    time_scale_label: str = "Realtime Lab"
    selected_index: int = 1
    search_text: str = ""
    active_bottom_tab: str = "Metrics"
    show_trails: bool = True
    show_labels: bool = True
    show_velocity_vectors: bool = True
    show_force_vectors: bool = False
    show_orbit_plane: bool = True
    trail_limit: int = 1500
    analysis_result: StabilityResult | None = None
    research_summary: list[str] = field(default_factory=list)
    chaos_divergence: list[float] = field(default_factory=list)
    series: TimeSeries = field(default_factory=TimeSeries)
    simulator: NBodySimulator = field(init=False)
    original_bodies: list[Body] = field(init=False)

    def __post_init__(self) -> None:
        self.original_bodies = self.scenario.clone_bodies()
        self.reset_simulator()

    @property
    def dt_seconds(self) -> float:
        return self.scenario.default_dt_hours * HOUR

    def reset_simulator(self) -> None:
        self.simulator = NBodySimulator(
            bodies=[body.copy() for body in self.original_bodies],
            dt=self.dt_seconds,
            integrator=make_integrator(self.integrator_name),
            softening=self.scenario.softening,
        )
        self.selected_index = min(self.selected_index, len(self.simulator.bodies) - 1)
        self.analysis_result = None
        self.research_summary = []
        self.chaos_divergence = []
        self.series.clear()

    def load_scenario(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.original_bodies = scenario.clone_bodies()
        self.selected_index = min(1, len(self.original_bodies) - 1)
        self.reset_simulator()

    def selected_body(self) -> Body:
        return self.simulator.bodies[self.selected_index]

    def central_body(self) -> Body:
        return self.simulator.bodies[self.scenario.central_index]

    def elapsed_days(self) -> float:
        return self.simulator.time / DAY

    def body_matches_search(self, body: Body) -> bool:
        query = self.search_text.strip().lower()
        return not query or query in body.name.lower()

    def scale_selected_mass(self, factor: float) -> None:
        body = self.selected_body()
        body.mass *= factor
        self.original_bodies[self.selected_index].mass *= factor

    def scale_selected_velocity(self, factor: float) -> None:
        body = self.selected_body()
        body.velocity = body.velocity * factor
        self.original_bodies[self.selected_index].velocity = self.original_bodies[self.selected_index].velocity * factor

    def nudge_selected_position(self, direction: np.ndarray, distance_m: float) -> None:
        body = self.selected_body()
        body.position = body.position + direction * distance_m
        self.original_bodies[self.selected_index].position = self.original_bodies[self.selected_index].position + direction * distance_m
