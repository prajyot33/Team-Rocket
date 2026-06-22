from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.simulator import NBodySimulator


@dataclass
class LyapunovResult:
    times: np.ndarray
    divergence: np.ndarray
    exponent: float


def estimate_lyapunov(
    simulator: NBodySimulator,
    *,
    duration: float,
    perturb_body_index: int = 1,
    perturbation_m: float = 10.0,
    sample_interval: float | None = None,
) -> LyapunovResult:
    """Estimate a simplified largest Lyapunov exponent.

    Two simulations are run with identical masses and velocities. One body is
    displaced by a tiny amount. The fitted slope of ln(d(t)/d0) is the exponent.
    """

    base = simulator.copy()
    perturbed = simulator.copy()
    perturbed.bodies[perturb_body_index].position[0] += perturbation_m

    sample_interval = sample_interval or simulator.dt
    next_sample = base.time
    end_time = base.time + duration
    times: list[float] = []
    divergence: list[float] = []

    while base.time < end_time:
        base.step()
        perturbed.step()
        if base.time + 1.0e-9 >= next_sample:
            base_positions = np.concatenate([body.position for body in base.bodies])
            perturbed_positions = np.concatenate([body.position for body in perturbed.bodies])
            d = float(np.linalg.norm(perturbed_positions - base_positions))
            times.append(base.time - simulator.time)
            divergence.append(max(d, perturbation_m * 1.0e-30))
            next_sample += sample_interval

    t = np.array(times, dtype=float)
    d = np.array(divergence, dtype=float)
    valid = (t > 0.0) & np.isfinite(d) & (d > 0.0)
    if np.count_nonzero(valid) < 2:
        exponent = 0.0
    else:
        y = np.log(d[valid] / perturbation_m)
        exponent = float(np.polyfit(t[valid], y, deg=1)[0])
    return LyapunovResult(times=t, divergence=d, exponent=exponent)
