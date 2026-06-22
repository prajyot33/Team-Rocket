from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from physics.body import Body
from physics.integrators import Integrator, VelocityVerletIntegrator
from simulation.recorder import SimulationHistory


@dataclass
class NBodySimulator:
    bodies: list[Body]
    dt: float
    integrator: Integrator | None = None
    softening: float = 0.0
    time: float = 0.0

    def __post_init__(self) -> None:
        if len(self.bodies) < 2:
            raise ValueError("NBodySimulator requires at least two bodies")
        if self.dt <= 0.0:
            raise ValueError("dt must be positive")
        if self.integrator is None:
            self.integrator = VelocityVerletIntegrator()

    def step(self) -> None:
        assert self.integrator is not None
        self.integrator.step(self.bodies, self.dt, softening=self.softening)
        self.time += self.dt

    def copy(self) -> "NBodySimulator":
        return NBodySimulator(
            bodies=[body.copy() for body in self.bodies],
            dt=self.dt,
            integrator=self.integrator,
            softening=self.softening,
            time=self.time,
        )

    def run(
        self,
        duration: float,
        *,
        record_interval: float | None = None,
        stop_on_event: Callable[["NBodySimulator"], bool] | None = None,
    ) -> SimulationHistory:
        history = SimulationHistory([body.name for body in self.bodies])
        record_interval = record_interval if record_interval is not None else self.dt
        next_record_time = self.time + record_interval
        history.record(self.time, self.bodies, softening=self.softening)

        end_time = self.time + duration
        while self.time < end_time:
            self.step()
            if self.time + 1.0e-9 >= next_record_time:
                history.record(self.time, self.bodies, softening=self.softening)
                next_record_time += record_interval
            if stop_on_event is not None and stop_on_event(self):
                break
        return history
