from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analysis.orbital_period import estimate_orbital_period
from physics.constants import AU, DAY
from physics.quantities import (
    angular_momentum_z,
    kinetic_energy,
    orbital_radius,
    orbital_velocity,
    potential_energy,
    total_energy,
)
from simulation.recorder import SimulationHistory


@dataclass
class MetricSnapshot:
    kinetic_energy: float
    potential_energy: float
    total_energy: float
    angular_momentum: float
    orbital_velocity: float
    orbital_radius: float
    orbital_period: float | None
    energy_drift: float
    status: str


class LiveMetrics:
    def __init__(self) -> None:
        self.initial_energy: float | None = None
        self.period_sample_counter = 0
        self.cached_period: float | None = None

    def snapshot(self, state) -> MetricSnapshot:
        bodies = state.simulator.bodies
        selected = state.selected_body()
        central = state.central_body()
        kinetic = kinetic_energy(bodies)
        potential = potential_energy(bodies, softening=state.simulator.softening)
        total = total_energy(bodies, softening=state.simulator.softening)
        angular = angular_momentum_z(bodies)
        radius = orbital_radius(selected, central)
        velocity = orbital_velocity(selected, central)

        if self.initial_energy is None:
            self.initial_energy = total
        drift = abs((total - self.initial_energy) / self.initial_energy) if self.initial_energy else 0.0

        if state.analysis_result is not None:
            status = state.analysis_result.label
            self.cached_period = state.analysis_result.metrics.get("estimated_orbital_period_s", self.cached_period)
        else:
            status = self._quick_status(radius, velocity, drift)

        return MetricSnapshot(
            kinetic_energy=kinetic,
            potential_energy=potential,
            total_energy=total,
            angular_momentum=angular,
            orbital_velocity=velocity,
            orbital_radius=radius,
            orbital_period=self.cached_period,
            energy_drift=drift,
            status=status,
        )

    def record(self, state, snapshot: MetricSnapshot) -> None:
        state.series.time_days.append(state.elapsed_days())
        state.series.kinetic.append(snapshot.kinetic_energy)
        state.series.potential.append(snapshot.potential_energy)
        state.series.total.append(snapshot.total_energy)
        state.series.angular_momentum.append(snapshot.angular_momentum)
        state.series.selected_speed.append(snapshot.orbital_velocity / 1000.0)
        state.series.selected_radius.append(snapshot.orbital_radius / AU)
        lyap = 0.0
        if state.analysis_result is not None:
            lyap = state.analysis_result.metrics.get("lyapunov_exponent_1_s", 0.0)
        state.series.lyapunov.append(lyap)

    def reset(self) -> None:
        self.initial_energy = None
        self.period_sample_counter = 0
        self.cached_period = None

    def update_period_from_history(
        self,
        history: SimulationHistory,
        *,
        central_index: int,
        body_index: int,
    ) -> None:
        self.cached_period = estimate_orbital_period(
            history,
            central_index=central_index,
            body_index=body_index,
        )

    @staticmethod
    def _quick_status(radius: float, velocity: float, drift: float) -> str:
        if drift > 5.0e-2:
            return "Numerically Sensitive"
        if radius > 8.0 * AU and velocity > 5_000.0:
            return "Escape Watch"
        return "Live"


def format_si(value: float, unit: str = "") -> str:
    if value == 0.0:
        return f"0 {unit}".strip()
    abs_value = abs(value)
    if 1.0e-3 <= abs_value < 1.0e4:
        return f"{value:,.3f} {unit}".strip()
    return f"{value:.3e} {unit}".strip()
