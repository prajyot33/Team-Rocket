from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .body import Body
from .constants import G
from .engine import masses_array, positions_array, velocities_array


def kinetic_energy(bodies: Sequence[Body]) -> float:
    masses = masses_array(bodies)
    velocities = velocities_array(bodies)
    return float(0.5 * np.sum(masses * np.sum(velocities * velocities, axis=1)))


def potential_energy(bodies: Sequence[Body], *, softening: float = 0.0) -> float:
    positions = positions_array(bodies)
    masses = masses_array(bodies)
    total = 0.0
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            separation = float(np.linalg.norm(positions[j] - positions[i]))
            total -= G * masses[i] * masses[j] / max(separation, softening)
    return total


def total_energy(bodies: Sequence[Body], *, softening: float = 0.0) -> float:
    return kinetic_energy(bodies) + potential_energy(bodies, softening=softening)


def angular_momentum_z(bodies: Sequence[Body]) -> float:
    total = 0.0
    for body in bodies:
        total += body.mass * (body.position[0] * body.velocity[1] - body.position[1] * body.velocity[0])
    return float(total)


def orbital_radius(body: Body, central_body: Body) -> float:
    return float(np.linalg.norm(body.position - central_body.position))


def orbital_velocity(body: Body, central_body: Body) -> float:
    return float(np.linalg.norm(body.velocity - central_body.velocity))


def specific_orbital_energy(body: Body, central_body: Body) -> float:
    r = orbital_radius(body, central_body)
    v = orbital_velocity(body, central_body)
    return 0.5 * v * v - G * (body.mass + central_body.mass) / r


def pairwise_distances(bodies: Sequence[Body]) -> np.ndarray:
    positions = positions_array(bodies)
    delta = positions[None, :, :] - positions[:, None, :]
    distances = np.sqrt(np.sum(delta * delta, axis=2))
    np.fill_diagonal(distances, np.inf)
    return distances
