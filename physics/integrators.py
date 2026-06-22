from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .body import Body
from .engine import (
    compute_accelerations,
    masses_array,
    positions_array,
    set_body_state,
    velocities_array,
)


class Integrator:
    name = "base"

    def step(self, bodies: list[Body], dt: float, *, softening: float = 0.0) -> None:
        raise NotImplementedError


@dataclass
class EulerIntegrator(Integrator):
    """Simple explicit Euler, included only as a comparison baseline."""

    name: str = "euler"

    def step(self, bodies: list[Body], dt: float, *, softening: float = 0.0) -> None:
        positions = positions_array(bodies)
        velocities = velocities_array(bodies)
        masses = masses_array(bodies)
        accelerations = compute_accelerations(positions, masses, softening=softening)
        set_body_state(bodies, positions + velocities * dt, velocities + accelerations * dt)


@dataclass
class VelocityVerletIntegrator(Integrator):
    """Symplectic second-order integrator for long-running orbital systems."""

    name: str = "velocity-verlet"

    def step(self, bodies: list[Body], dt: float, *, softening: float = 0.0) -> None:
        positions = positions_array(bodies)
        velocities = velocities_array(bodies)
        masses = masses_array(bodies)

        acceleration_now = compute_accelerations(positions, masses, softening=softening)
        positions_next = positions + velocities * dt + 0.5 * acceleration_now * dt * dt
        acceleration_next = compute_accelerations(positions_next, masses, softening=softening)
        velocities_next = velocities + 0.5 * (acceleration_now + acceleration_next) * dt

        set_body_state(bodies, positions_next, velocities_next)


@dataclass
class RK4Integrator(Integrator):
    """Classical fourth-order Runge-Kutta.

    RK4 is very accurate per step for short integrations, but it is not
    symplectic. In long gravitational runs it can drift in total energy even
    when each local step looks accurate.
    """

    name: str = "rk4"

    def step(self, bodies: list[Body], dt: float, *, softening: float = 0.0) -> None:
        positions = positions_array(bodies)
        velocities = velocities_array(bodies)
        masses = masses_array(bodies)

        def derivative(pos: np.ndarray, vel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            return vel, compute_accelerations(pos, masses, softening=softening)

        k1_x, k1_v = derivative(positions, velocities)
        k2_x, k2_v = derivative(positions + 0.5 * dt * k1_x, velocities + 0.5 * dt * k1_v)
        k3_x, k3_v = derivative(positions + 0.5 * dt * k2_x, velocities + 0.5 * dt * k2_v)
        k4_x, k4_v = derivative(positions + dt * k3_x, velocities + dt * k3_v)

        positions_next = positions + (dt / 6.0) * (k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x)
        velocities_next = velocities + (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)
        set_body_state(bodies, positions_next, velocities_next)


def make_integrator(name: str) -> Integrator:
    normalized = name.strip().lower()
    if normalized in {"verlet", "velocity-verlet", "velocity_verlet", "vv"}:
        return VelocityVerletIntegrator()
    if normalized in {"rk4", "runge-kutta", "runge_kutta"}:
        return RK4Integrator()
    if normalized in {"euler", "explicit-euler", "explicit_euler"}:
        return EulerIntegrator()
    raise ValueError(f"Unknown integrator: {name}")
