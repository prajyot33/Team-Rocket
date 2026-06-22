from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from physics.body import Body
from physics.engine import positions_array, velocities_array
from physics.quantities import angular_momentum_z, kinetic_energy, potential_energy, total_energy


@dataclass
class SimulationHistory:
    body_names: list[str]
    times: list[float] = field(default_factory=list)
    positions: list[np.ndarray] = field(default_factory=list)
    velocities: list[np.ndarray] = field(default_factory=list)
    kinetic: list[float] = field(default_factory=list)
    potential: list[float] = field(default_factory=list)
    total: list[float] = field(default_factory=list)
    angular_momentum: list[float] = field(default_factory=list)

    def record(self, time: float, bodies: list[Body], *, softening: float = 0.0) -> None:
        self.times.append(float(time))
        self.positions.append(positions_array(bodies).copy())
        self.velocities.append(velocities_array(bodies).copy())
        self.kinetic.append(kinetic_energy(bodies))
        self.potential.append(potential_energy(bodies, softening=softening))
        self.total.append(total_energy(bodies, softening=softening))
        self.angular_momentum.append(angular_momentum_z(bodies))

    @property
    def times_array(self) -> np.ndarray:
        return np.array(self.times, dtype=float)

    @property
    def positions_array(self) -> np.ndarray:
        return np.array(self.positions, dtype=float)

    @property
    def velocities_array(self) -> np.ndarray:
        return np.array(self.velocities, dtype=float)

    def speeds(self) -> np.ndarray:
        return np.linalg.norm(self.velocities_array, axis=2)

    def radii_from(self, central_index: int = 0) -> np.ndarray:
        positions = self.positions_array
        return np.linalg.norm(positions - positions[:, central_index : central_index + 1, :], axis=2)

    def write_csv(self, path: Path, *, central_index: int = 0) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        radii = self.radii_from(central_index=central_index)
        speeds = self.speeds()
        positions = self.positions_array
        velocities = self.velocities_array

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "time_s",
                    "body",
                    "x_m",
                    "y_m",
                    "vx_m_s",
                    "vy_m_s",
                    "speed_m_s",
                    "radius_from_central_m",
                    "kinetic_J",
                    "potential_J",
                    "total_energy_J",
                    "angular_momentum_kg_m2_s",
                ]
            )
            for sample_index, time in enumerate(self.times):
                for body_index, body_name in enumerate(self.body_names):
                    writer.writerow(
                        [
                            time,
                            body_name,
                            positions[sample_index, body_index, 0],
                            positions[sample_index, body_index, 1],
                            velocities[sample_index, body_index, 0],
                            velocities[sample_index, body_index, 1],
                            speeds[sample_index, body_index],
                            radii[sample_index, body_index],
                            self.kinetic[sample_index],
                            self.potential[sample_index],
                            self.total[sample_index],
                            self.angular_momentum[sample_index],
                        ]
                    )
