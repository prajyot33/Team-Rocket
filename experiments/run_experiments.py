from __future__ import annotations

from pathlib import Path

from analysis.lyapunov import estimate_lyapunov
from analysis.plots import plot_divergence, plot_energy, plot_radius, plot_velocity
from analysis.stability import StabilityAnalyzer
from experiments.scenarios import all_scenarios
from physics.constants import DAY, HOUR
from physics.integrators import make_integrator
from simulation.simulator import NBodySimulator


def run_all(output_dir: Path, *, integrator_name: str = "verlet") -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    analyzer = StabilityAnalyzer()
    summary_lines = ["scenario,label,energy_drift_or_lyapunov,notes"]

    for scenario in all_scenarios().values():
        scenario_dir = output_dir / scenario.key
        scenario_dir.mkdir(parents=True, exist_ok=True)
        simulator = NBodySimulator(
            bodies=scenario.clone_bodies(),
            dt=scenario.default_dt_hours * HOUR,
            integrator=make_integrator(integrator_name),
            softening=scenario.softening,
        )
        duration = scenario.default_duration_days * DAY
        record_interval = simulator.dt if scenario.key == "collision" else max(simulator.dt, DAY)
        history = simulator.run(duration, record_interval=record_interval)
        history.write_csv(scenario_dir / "history.csv", central_index=scenario.central_index)

        lyapunov = None
        if scenario.key in {"binary-chaos", "random5"}:
            lyapunov = estimate_lyapunov(
                NBodySimulator(
                    bodies=scenario.clone_bodies(),
                    dt=scenario.default_dt_hours * HOUR,
                    integrator=make_integrator(integrator_name),
                    softening=scenario.softening,
                ),
                duration=min(duration, 250.0 * DAY),
                perturb_body_index=scenario.target_index,
                sample_interval=DAY,
            )
            plot_divergence(lyapunov.times, lyapunov.divergence, scenario_dir / "divergence.png")

        result = analyzer.classify(
            history,
            [body.mass for body in simulator.bodies],
            [body.radius for body in simulator.bodies],
            central_index=scenario.central_index,
            target_index=scenario.target_index,
            lyapunov_exponent=None if lyapunov is None else lyapunov.exponent,
        )
        plot_energy(history, scenario_dir / "energy.png")
        plot_velocity(history, scenario_dir / "velocity.png")
        plot_radius(history, scenario_dir / "radius.png", central_index=scenario.central_index)

        metric = result.metrics.get("lyapunov_exponent_1_s", result.metrics.get("relative_energy_drift", 0.0))
        summary_lines.append(f"{scenario.key},{result.label},{metric},{' | '.join(result.reasons)}")

    (output_dir / "summary.csv").write_text("\n".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    run_all(Path("results"))
