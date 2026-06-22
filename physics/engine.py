from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .body import Body
from .constants import G


def positions_array(bodies: Sequence[Body]) -> np.ndarray:
    return np.vstack([body.position for body in bodies])


def velocities_array(bodies: Sequence[Body]) -> np.ndarray:
    return np.vstack([body.velocity for body in bodies])


def masses_array(bodies: Sequence[Body]) -> np.ndarray:
    return np.array([body.mass for body in bodies], dtype=float)


def compute_accelerations(
    positions: np.ndarray,
    masses: np.ndarray,
    *,
    softening: float = 0.0,
) -> np.ndarray:
    """Return gravitational acceleration on every body.

    a_i = G * sum_j m_j * (r_j - r_i) / (|r_j - r_i|^2 + eps^2)^(3/2)

    softening is optional and should be kept at 0 for physical experiments
    unless a random many-body scenario would otherwise suffer numerical blow-up.
    """

    delta = positions[None, :, :] - positions[:, None, :]
    distance_squared = np.sum(delta * delta, axis=2) + softening * softening
    np.fill_diagonal(distance_squared, np.inf)
    inv_distance_cubed = distance_squared ** -1.5
    weighted = delta * masses[None, :, None] * inv_distance_cubed[:, :, None]
    return G * np.sum(weighted, axis=1)


def accelerations_for_bodies(bodies: Sequence[Body], *, softening: float = 0.0) -> np.ndarray:
    return compute_accelerations(
        positions_array(bodies),
        masses_array(bodies),
        softening=softening,
    )


def set_body_state(bodies: Sequence[Body], positions: np.ndarray, velocities: np.ndarray) -> None:
    for index, body in enumerate(bodies):
        body.position = positions[index].copy()
        body.velocity = velocities[index].copy()


def center_of_mass_frame(bodies: Sequence[Body]) -> None:
    """Move bodies into the center-of-mass frame in-place."""

    masses = masses_array(bodies)
    total_mass = float(np.sum(masses))
    positions = positions_array(bodies)
    velocities = velocities_array(bodies)
    center_position = np.sum(positions * masses[:, None], axis=0) / total_mass
    center_velocity = np.sum(velocities * masses[:, None], axis=0) / total_mass

    for body in bodies:
        body.position = body.position - center_position
        body.velocity = body.velocity - center_velocity
