from __future__ import annotations

import argparse
from pathlib import Path

from analysis.lyapunov import estimate_lyapunov
from analysis.plots import plot_divergence, plot_energy, plot_radius, plot_velocity
from analysis.stability import StabilityAnalyzer
from experiments.scenarios import all_scenarios, get_scenario
from physics.constants import DAY, HOUR
from physics.integrators import make_integrator
from simulation.simulator import NBodySimulator
from visualization.pygame_viewer import PygameViewer


def parse_args() -> argparse.Namespace:
    scenarios = sorted(all_scenarios())
    parser = argparse.ArgumentParser(description="Orbital Dynamics and Stability Simulation")
    parser.add_argument("--scenario", choices=scenarios, default="stable")
    parser.add_argument("--integrator", choices=["verlet", "rk4", "euler"], default="verlet")
    parser.add_argument("--duration-days", type=float, default=None)
    parser.add_argument("--dt-hours", type=float, default=None)
    parser.add_argument("--headless", action="store_true", help="Run without Pygame and write data/plots")
    parser.add_argument("--plots", action="store_true", help="Generate Matplotlib plots in headless mode")
    parser.add_argument("--lyapunov", action="store_true", help="Run paired-simulation chaos analysis")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scenario = get_scenario(args.scenario)
    dt = (args.dt_hours if args.dt_hours is not None else scenario.default_dt_hours) * HOUR
    duration = (args.duration_days if args.duration_days is not None else scenario.default_duration_days) * DAY
    simulator = NBodySimulator(
        bodies=scenario.clone_bodies(),
        dt=dt,
        integrator=make_integrator(args.integrator),
        softening=scenario.softening,
    )

    if not args.headless:
        print(f"Launching {scenario.title} with {args.integrator} integrator")
        print("Controls: space pause, +/- zoom, arrows/WASD pan, v velocity, f force, t trails, tab select")
        PygameViewer(simulator).run()
        return

    output_dir = args.output_dir / scenario.key
    output_dir.mkdir(parents=True, exist_ok=True)
    record_interval = dt if scenario.key == "collision" else max(dt, DAY)
    history = simulator.run(duration, record_interval=record_interval)
    history.write_csv(output_dir / "history.csv", central_index=scenario.central_index)

    lyapunov_result = None
    if args.lyapunov:
        lyapunov_result = estimate_lyapunov(
            NBodySimulator(
                bodies=scenario.clone_bodies(),
                dt=dt,
                integrator=make_integrator(args.integrator),
                softening=scenario.softening,
            ),
            duration=duration,
            perturb_body_index=scenario.target_index,
            sample_interval=max(dt, DAY),
        )

    result = StabilityAnalyzer().classify(
        history,
        [body.mass for body in simulator.bodies],
        [body.radius for body in simulator.bodies],
        central_index=scenario.central_index,
        target_index=scenario.target_index,
        lyapunov_exponent=None if lyapunov_result is None else lyapunov_result.exponent,
    )

    if args.plots:
        plot_energy(history, output_dir / "energy.png")
        plot_velocity(history, output_dir / "velocity.png")
        plot_radius(history, output_dir / "radius.png", central_index=scenario.central_index)
        if lyapunov_result is not None:
            plot_divergence(lyapunov_result.times, lyapunov_result.divergence, output_dir / "divergence.png")

    print(f"Scenario: {scenario.title}")
    print(f"Expected: {scenario.expected}")
    print(f"Classification: {result.label}")
    for reason in result.reasons:
        print(f"- {reason}")
    print("Metrics:")
    for key, value in sorted(result.metrics.items()):
        print(f"  {key}: {value:.6e}")
    print(f"Data written to: {output_dir}")


if __name__ == "__main__":
    main()
