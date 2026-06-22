from __future__ import annotations

from dataclasses import dataclass

from analysis.lyapunov import estimate_lyapunov
from analysis.stability import StabilityAnalyzer, StabilityResult
from physics.constants import DAY
from physics.integrators import make_integrator
from simulation.simulator import NBodySimulator


@dataclass
class ResearchReport:
    result: StabilityResult
    summary_lines: list[str]
    divergence_m: list[float]


class ResearchAnalyzer:
    def analyze(self, state) -> ResearchReport:
        scenario = state.scenario
        duration = min(scenario.default_duration_days * DAY, 250.0 * DAY)
        simulator = NBodySimulator(
            bodies=[body.copy() for body in state.simulator.bodies],
            dt=state.simulator.dt,
            integrator=make_integrator(state.integrator_name),
            softening=state.simulator.softening,
        )
        record_interval = state.simulator.dt if scenario.key == "collision" else max(state.simulator.dt, DAY)
        history = simulator.run(duration, record_interval=record_interval)

        lyapunov = None
        if scenario.key in {"binary-chaos", "random5"}:
            lyapunov = estimate_lyapunov(
                NBodySimulator(
                    bodies=[body.copy() for body in state.simulator.bodies],
                    dt=state.simulator.dt,
                    integrator=make_integrator(state.integrator_name),
                    softening=state.simulator.softening,
                ),
                duration=min(duration, 180.0 * DAY),
                perturb_body_index=scenario.target_index,
                sample_interval=max(state.simulator.dt, DAY),
            )

        result = StabilityAnalyzer().classify(
            history,
            [body.mass for body in simulator.bodies],
            [body.radius for body in simulator.bodies],
            central_index=scenario.central_index,
            target_index=scenario.target_index,
            lyapunov_exponent=None if lyapunov is None else lyapunov.exponent,
        )
        summary = self._build_summary(scenario, result)
        divergence = [] if lyapunov is None else [float(value) for value in lyapunov.divergence]
        return ResearchReport(result=result, summary_lines=summary, divergence_m=divergence)

    @staticmethod
    def _build_summary(scenario, result: StabilityResult) -> list[str]:
        metrics = result.metrics
        lines = [
            f"System: {scenario.title}",
            f"Classification: {result.label}",
        ]
        lines.append(f"Escape probability estimate: {ResearchAnalyzer._escape_probability(scenario, result):.0%}")
        if "relative_energy_drift" in metrics:
            lines.append(f"Energy conservation error: {metrics['relative_energy_drift']:.3e}")
        if "estimated_orbital_period_s" in metrics:
            lines.append(f"Measured orbital period: {metrics['estimated_orbital_period_s'] / DAY:.2f} days")
        if "lyapunov_exponent_1_s" in metrics:
            lines.append(f"Lyapunov estimate: {metrics['lyapunov_exponent_1_s']:.3e} 1/s")
        if "final_specific_orbital_energy_J_kg" in metrics:
            lines.append(f"Final specific orbital energy: {metrics['final_specific_orbital_energy_J_kg']:.3e} J/kg")
        if "min_collision_clearance_m" in metrics:
            lines.append(f"Minimum collision clearance: {metrics['min_collision_clearance_m']:.3e} m")
        for reason in result.reasons:
            lines.append(f"Interpretation: {reason}.")
        return lines[:8]

    @staticmethod
    def _escape_probability(scenario, result: StabilityResult) -> float:
        if result.label == "Escape Trajectory":
            return 0.98
        if result.label == "Collision":
            return 0.0
        if result.label == "Stable Orbit":
            return 0.02
        if result.label == "Chaotic Motion":
            energy = result.metrics.get("final_specific_orbital_energy_J_kg", -1.0)
            return 0.55 if energy > 0.0 else 0.35
        return 0.15
