from __future__ import annotations

from pathlib import Path

import numpy as np

from physics.constants import AU, DAY
from simulation.recorder import SimulationHistory


def _load_pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for plotting. Install with: pip install matplotlib") from exc
    return plt


def plot_energy(history: SimulationHistory, path: Path) -> None:
    plt = _load_pyplot()
    path.parent.mkdir(parents=True, exist_ok=True)
    time_days = history.times_array / DAY
    plt.figure(figsize=(9, 5))
    plt.plot(time_days, history.kinetic, label="Kinetic")
    plt.plot(time_days, history.potential, label="Potential")
    plt.plot(time_days, history.total, label="Total")
    plt.xlabel("Time (days)")
    plt.ylabel("Energy (J)")
    plt.title("Energy vs Time")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_velocity(history: SimulationHistory, path: Path) -> None:
    plt = _load_pyplot()
    path.parent.mkdir(parents=True, exist_ok=True)
    time_days = history.times_array / DAY
    speeds = history.speeds()
    plt.figure(figsize=(9, 5))
    for index, body_name in enumerate(history.body_names):
        plt.plot(time_days, speeds[:, index] / 1000.0, label=body_name)
    plt.xlabel("Time (days)")
    plt.ylabel("Speed (km/s)")
    plt.title("Velocity vs Time")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_radius(history: SimulationHistory, path: Path, *, central_index: int = 0) -> None:
    plt = _load_pyplot()
    path.parent.mkdir(parents=True, exist_ok=True)
    time_days = history.times_array / DAY
    radii = history.radii_from(central_index=central_index)
    plt.figure(figsize=(9, 5))
    for index, body_name in enumerate(history.body_names):
        if index == central_index:
            continue
        plt.plot(time_days, radii[:, index] / AU, label=body_name)
    plt.xlabel("Time (days)")
    plt.ylabel("Radius from central body (AU)")
    plt.title("Orbital Radius vs Time")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_divergence(times: np.ndarray, divergence: np.ndarray, path: Path) -> None:
    plt = _load_pyplot()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5))
    plt.semilogy(times / DAY, divergence)
    plt.xlabel("Time (days)")
    plt.ylabel("Trajectory divergence (m)")
    plt.title("Lyapunov Divergence vs Time")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
