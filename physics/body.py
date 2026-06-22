from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


VectorLike = Iterable[float]


@dataclass
class Body:
    """A celestial body represented in SI units.

    position and velocity are two-dimensional vectors in meters and meters per
    second. The engine is deliberately 2D for clear visualization, but the force
    law and architecture are the same as a 3D implementation.
    """

    name: str
    mass: float
    radius: float
    position: VectorLike
    velocity: VectorLike
    color: tuple[int, int, int] = (255, 255, 255)
    trail: list[np.ndarray] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.position = np.array(self.position, dtype=float)
        self.velocity = np.array(self.velocity, dtype=float)
        if self.position.shape != (2,) or self.velocity.shape != (2,):
            raise ValueError(f"{self.name} must use 2D position and velocity vectors")
        if self.mass <= 0.0:
            raise ValueError(f"{self.name} must have positive mass")
        if self.radius <= 0.0:
            raise ValueError(f"{self.name} must have positive radius")

    def copy(self) -> "Body":
        clone = Body(
            name=self.name,
            mass=self.mass,
            radius=self.radius,
            position=self.position.copy(),
            velocity=self.velocity.copy(),
            color=self.color,
        )
        clone.trail = [point.copy() for point in self.trail]
        return clone

    @property
    def speed(self) -> float:
        return float(np.linalg.norm(self.velocity))

    def momentum(self) -> np.ndarray:
        return self.mass * self.velocity
