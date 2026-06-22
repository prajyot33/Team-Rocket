from __future__ import annotations

import numpy as np

from simulation.recorder import SimulationHistory


def estimate_orbital_period(
    history: SimulationHistory,
    *,
    central_index: int = 0,
    body_index: int = 1,
) -> float | None:
    """Estimate period from full revolutions in recorded trajectory data.

    The method unwraps the polar angle of a body around a central body and
    interpolates the times when the angle advances by 2*pi. It works for mildly
    eccentric orbits and is intentionally independent of Kepler's analytic law.
    """

    positions = history.positions_array
    times = history.times_array
    relative = positions[:, body_index] - positions[:, central_index]
    angles = np.unwrap(np.arctan2(relative[:, 1], relative[:, 0]))
    progress = angles - angles[0]
    if abs(progress[-1]) < 2.0 * np.pi:
        return None
    if progress[-1] < 0.0:
        progress = -progress

    crossings: list[float] = []
    max_orbits = int(progress[-1] // (2.0 * np.pi))
    for orbit_number in range(1, max_orbits + 1):
        target = orbit_number * 2.0 * np.pi
        after = np.flatnonzero(progress >= target)
        if len(after) == 0:
            continue
        hi = int(after[0])
        lo = max(hi - 1, 0)
        if hi == lo:
            crossings.append(float(times[hi]))
            continue
        fraction = (target - progress[lo]) / (progress[hi] - progress[lo])
        crossings.append(float(times[lo] + fraction * (times[hi] - times[lo])))

    if not crossings:
        return None
    if len(crossings) == 1:
        return crossings[0] - times[0]
    return float(np.mean(np.diff(crossings)))
