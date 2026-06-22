from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from physics.constants import G
from analysis.orbital_period import estimate_orbital_period
from simulation.recorder import SimulationHistory


@dataclass
class StabilityThresholds:
    collision_radius_factor: float = 1.0
    escape_radius_multiplier: float = 6.0
    energy_drift_stable: float = 5.0e-3
    radius_cv_stable: float = 0.25
    min_orbits_for_stable: float = 0.75
    chaos_lyapunov_threshold: float = 1.0e-8
    chaos_radius_cv: float = 0.55


@dataclass
class StabilityResult:
    label: str
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


class StabilityAnalyzer:
    def __init__(self, thresholds: StabilityThresholds | None = None) -> None:
        self.thresholds = thresholds or StabilityThresholds()

    def classify(
        self,
        history: SimulationHistory,
        masses: list[float],
        radii: list[float],
        *,
        central_index: int = 0,
        target_index: int = 1,
        lyapunov_exponent: float | None = None,
    ) -> StabilityResult:
        positions = history.positions_array
        velocities = history.velocities_array
        times = history.times_array
        body_count = positions.shape[1]
        metrics: dict[str, float] = {}
        reasons: list[str] = []

        min_clearance = np.inf
        collision_pair: tuple[int, int] | None = None
        for i in range(body_count):
            for j in range(i + 1, body_count):
                distances = np.linalg.norm(positions[:, j] - positions[:, i], axis=1)
                clearance = float(np.min(distances - self.thresholds.collision_radius_factor * (radii[i] + radii[j])))
                if clearance < min_clearance:
                    min_clearance = clearance
                    collision_pair = (i, j)
        metrics["min_collision_clearance_m"] = min_clearance
        if min_clearance <= 0.0:
            reasons.append(f"surface overlap detected for body indices {collision_pair}")
            return StabilityResult("Collision", reasons, metrics)

        central_positions = positions[:, central_index]
        central_velocities = velocities[:, central_index]
        target_positions = positions[:, target_index]
        target_velocities = velocities[:, target_index]
        relative_positions = target_positions - central_positions
        relative_velocities = target_velocities - central_velocities
        radii_from_central = np.linalg.norm(relative_positions, axis=1)
        speeds = np.linalg.norm(relative_velocities, axis=1)

        r0 = max(float(radii_from_central[0]), 1.0)
        final_r = float(radii_from_central[-1])
        max_r = float(np.max(radii_from_central))
        radial_velocity = float(np.dot(relative_positions[-1], relative_velocities[-1]) / max(final_r, 1.0))
        specific_energy = float(0.5 * speeds[-1] ** 2 - G * (masses[central_index] + masses[target_index]) / max(final_r, 1.0))
        metrics.update(
            {
                "initial_radius_m": r0,
                "final_radius_m": final_r,
                "max_radius_m": max_r,
                "final_radial_velocity_m_s": radial_velocity,
                "final_specific_orbital_energy_J_kg": specific_energy,
            }
        )

        escaped_by_radius = max_r > self.thresholds.escape_radius_multiplier * r0
        escaped_by_energy = specific_energy > 0.0 and radial_velocity > 0.0 and final_r > 1.5 * r0
        if escaped_by_radius or escaped_by_energy:
            reasons.append("positive outward orbital energy or large radius growth")
            return StabilityResult("Escape Trajectory", reasons, metrics)

        total_energy = np.array(history.total, dtype=float)
        initial_energy = total_energy[0]
        energy_drift = float(abs((total_energy[-1] - initial_energy) / initial_energy)) if initial_energy != 0.0 else np.inf
        radius_cv = float(np.std(radii_from_central) / max(np.mean(radii_from_central), 1.0))
        angles = np.unwrap(np.arctan2(relative_positions[:, 1], relative_positions[:, 0]))
        completed_orbits = float(abs(angles[-1] - angles[0]) / (2.0 * np.pi))
        period = estimate_orbital_period(history, central_index=central_index, body_index=target_index)
        metrics.update(
            {
                "relative_energy_drift": energy_drift,
                "target_radius_cv": radius_cv,
                "completed_orbits": completed_orbits,
                "duration_s": float(times[-1] - times[0]),
            }
        )
        if period is not None:
            metrics["estimated_orbital_period_s"] = period

        if lyapunov_exponent is not None:
            metrics["lyapunov_exponent_1_s"] = lyapunov_exponent
            if lyapunov_exponent > self.thresholds.chaos_lyapunov_threshold:
                reasons.append("nearby trajectories diverged exponentially")
                return StabilityResult("Chaotic Motion", reasons, metrics)

        if (
            energy_drift < self.thresholds.energy_drift_stable
            and radius_cv < self.thresholds.radius_cv_stable
            and completed_orbits >= self.thresholds.min_orbits_for_stable
        ):
            reasons.append("bounded radius, low energy drift, and repeated revolution")
            return StabilityResult("Stable Orbit", reasons, metrics)

        if radius_cv > self.thresholds.chaos_radius_cv or body_count >= 4:
            reasons.append("bounded but irregular radius variation without clean periodicity")
            return StabilityResult("Chaotic Motion", reasons, metrics)

        reasons.append("motion is bounded but not periodic over the sampled duration")
        return StabilityResult("Stable Orbit", reasons, metrics)
