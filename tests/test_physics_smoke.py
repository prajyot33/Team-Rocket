from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.scenarios import stable_star_planet_moon
from physics.constants import DAY, HOUR
from physics.integrators import EulerIntegrator, VelocityVerletIntegrator
from simulation.simulator import NBodySimulator


def _energy_drift(integrator) -> float:
    scenario = stable_star_planet_moon()
    simulator = NBodySimulator(
        bodies=scenario.clone_bodies(),
        dt=4.0 * HOUR,
        integrator=integrator,
    )
    history = simulator.run(60.0 * DAY, record_interval=DAY)
    return abs((history.total[-1] - history.total[0]) / history.total[0])


def test_velocity_verlet_has_small_energy_drift() -> None:
    assert _energy_drift(VelocityVerletIntegrator()) < 1.0e-3


def test_verlet_beats_euler_for_orbit_energy() -> None:
    assert _energy_drift(VelocityVerletIntegrator()) < _energy_drift(EulerIntegrator())
