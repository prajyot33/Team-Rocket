# Technical Report: Orbital Dynamics and Stability Simulation

## Phase 1 - Physics Engine Upgrade

### Concept Explanation

The GitHub-style solar-system script becomes a reusable N-body simulator. Instead of hard-coding planet-to-sun forces, every body interacts with every other body. This improves the score because the competition asks for at least three interacting celestial bodies and dynamic gravitational forces; a generic N-body engine proves the implementation is physically general.

### Physics Background

Each body is treated as a point mass for gravity and as a sphere for collision detection. Newton's law of universal gravitation gives equal-and-opposite attraction between all pairs. The model uses SI units throughout: kilograms, meters, seconds, joules.

### Mathematical Equations

Pairwise force:

```text
F_ij = G m_i m_j (r_j - r_i) / |r_j - r_i|^3
```

Acceleration on body `i`:

```text
a_i = G sum(j != i) m_j (r_j - r_i) / |r_j - r_i|^3
```

Velocity Verlet:

```text
r(t + dt) = r(t) + v(t) dt + 0.5 a(t) dt^2
v(t + dt) = v(t) + 0.5 [a(t) + a(t + dt)] dt
```

RK4 is also implemented, but Velocity Verlet is the recommended default. RK4 has high local accuracy, while Velocity Verlet is symplectic and usually preserves orbital energy better over long runs.

### Software Architecture

- `physics/body.py`: body dataclass.
- `physics/engine.py`: vectorized N-body acceleration.
- `physics/integrators.py`: Euler, Velocity Verlet, and RK4.
- `simulation/simulator.py`: time stepping and simulation orchestration.

### Complete Python Code

Complete implementation:

- `physics/body.py`
- `physics/engine.py`
- `physics/integrators.py`
- `simulation/simulator.py`

Run:

```powershell
python main.py --headless --scenario stable --integrator verlet --duration-days 370
```

### Improvements and Extensions

- Add adaptive timestep reduction during close encounters.
- Add 3D vectors by changing vector shape from `(2,)` to `(3,)`.
- Add Barnes-Hut approximation for large `N`.

## Phase 2 - Stability Analysis System

### Concept Explanation

The project does not merely show orbits; it classifies behavior automatically. This improves judging because the results become measurable and repeatable.

### Physics Background

Bound orbits have negative specific orbital energy and bounded radius. Escape trajectories have positive specific orbital energy and outward radial velocity. Collision occurs when spherical radii overlap. Chaotic motion is detected through sensitivity to initial conditions.

### Mathematical Equations

Collision:

```text
d_ij <= R_i + R_j
```

Specific orbital energy of target relative to central mass:

```text
epsilon = 0.5 |v_rel|^2 - G (M + m) / r
```

Escape if:

```text
epsilon > 0 and dr/dt > 0
```

Stable orbit criteria:

```text
|E_final - E_initial| / |E_initial| < 5e-3
std(r) / mean(r) < 0.25
completed_orbits >= 0.75
```

### Software Architecture

- `analysis/stability.py`: event and classification logic.
- `analysis/orbital_period.py`: period estimation from recorded trajectory.
- `simulation/recorder.py`: stores positions, velocities, energy, angular momentum.

### Complete Python Code

Complete implementation:

- `analysis/stability.py`
- `analysis/orbital_period.py`
- `simulation/recorder.py`

Run:

```powershell
python main.py --headless --scenario collision
python main.py --headless --scenario escape
```

### Improvements and Extensions

- Use per-scenario tuned thresholds in a config file.
- Add eccentricity classification from apoapsis and periapsis.
- Add conserved momentum checks.

## Phase 3 - Physical Quantities

### Concept Explanation

Judges need evidence that the simulation is not just animation. Energy, velocity, period, and angular momentum turn the demo into a scientific experiment.

### Physics Background

Kinetic energy tracks motion, potential energy tracks gravitational binding, and total energy should remain nearly constant in an isolated system. Angular momentum should also remain nearly constant unless numerical error is large.

### Mathematical Equations

Kinetic energy:

```text
K = sum_i 0.5 m_i |v_i|^2
```

Potential energy:

```text
U = - sum_i<j G m_i m_j / |r_i - r_j|
```

Total energy:

```text
E = K + U
```

Angular momentum in 2D:

```text
L_z = sum_i m_i (x_i v_yi - y_i v_xi)
```

Orbital period from trajectory:

```text
theta(t) = unwrap(atan2(y_rel, x_rel))
T = mean time between theta crossing multiples of 2*pi
```

### Software Architecture

- `physics/quantities.py`: energy, speed, radius, angular momentum.
- `analysis/orbital_period.py`: measured period.
- `analysis/plots.py`: graphs.

### Complete Python Code

Complete implementation:

- `physics/quantities.py`
- `analysis/orbital_period.py`
- `analysis/plots.py`

Run:

```powershell
python main.py --headless --scenario stable --duration-days 370 --plots
```

### Improvements and Extensions

- Add eccentricity and semi-major axis estimation.
- Compare measured period with Kepler's third law.
- Add a conservation-error scoreboard in the Pygame panel.

## Phase 4 - Experimental Framework

### Concept Explanation

A competition-winning project should show controlled experiments, not one hand-picked animation. The scenarios demonstrate different regimes with the same engine.

### Physics Background and Initial Conditions

Scenario A: Stable star-planet-moon system.

- Sun at origin, Earth near `1 AU`, Moon at Earth plus `384,400 km`.
- Earth velocity near `sqrt(GM_sun/r)`.
- Moon velocity is Earth heliocentric velocity plus lunar orbital velocity.
- Expected behavior: Earth completes a near-year orbit; Moon remains bound.

Scenario B: Escape trajectory.

- Probe starts at `1 AU`.
- Speed is `1.05 * sqrt(2GM_sun/r)`.
- Jupiter is included as a third interacting body.
- Expected behavior: positive specific energy and outward motion.

Scenario C: Planet-star collision.

- Planet starts at `0.10 AU` with inward radial velocity and little angular momentum.
- Expected behavior: surface overlap with the star.

Scenario D: Binary-star chaos system.

- Two solar-mass stars orbit a shared center.
- A planet and low-mass perturber move through the time-dependent binary potential.
- Expected behavior: sensitive dependence and irregular bounded motion during the primary analysis window. If run much longer, the same instability can later eject a body, which is also physically plausible.

Scenario E: Random five-body system.

- Five bodies receive seeded random masses, positions, and velocities.
- Expected behavior: close encounters, energy exchange, escape, collision, or irregular bounded motion.

### Mathematical Equations

Circular speed:

```text
v_c = sqrt(GM/r)
```

Escape speed:

```text
v_esc = sqrt(2GM/r)
```

### Software Architecture

- `experiments/scenarios.py`: named scenarios and initial conditions.
- `experiments/run_experiments.py`: runs all scenarios and writes result files.

### Complete Python Code

Complete implementation:

- `experiments/scenarios.py`
- `experiments/run_experiments.py`

Run:

```powershell
python -m experiments.run_experiments
```

### Improvements and Extensions

- Sweep launch velocity from `0.5 v_c` to `1.2 v_esc`.
- Sweep timestep to demonstrate numerical convergence.
- Save scenario metadata as JSON for reproducibility.

## Phase 5 - Advanced Visualization Features

### Concept Explanation

Visual features make the demo interpretable in real time. Vectors and trails help judges see cause and effect instead of only moving dots.

### Physics Background

Velocity vectors show tangential and radial motion. Force vectors show the instantaneous gravitational acceleration direction. Trails reveal whether motion is periodic, escaping, colliding, or irregular.

### Mathematical Equations

Velocity vector:

```text
v = dr/dt
```

Force direction:

```text
F_net,i = m_i a_i
```

### Software Architecture

- `visualization/pygame_viewer.py`: camera, trails, body selection, vectors, stats panel.
- `main.py`: launches viewer unless `--headless` is provided.

### Complete Python Code

Complete implementation:

- `visualization/pygame_viewer.py`
- `main.py`

Run:

```powershell
python main.py --scenario binary-chaos
```

### Improvements and Extensions

- Add screenshot/video recording.
- Add live classification label in the panel.
- Add click-and-drag impulse editing for live experiments.

## Phase 6 - Chaos Detection

### Concept Explanation

Chaos is not the same as random-looking motion. The project runs two nearly identical simulations and measures whether their trajectories diverge exponentially.

### Physics Background

Chaotic deterministic systems show sensitive dependence on initial conditions. A tiny initial separation grows approximately as `d(t) = d0 exp(lambda t)` over a useful time window.

### Mathematical Equations

Divergence:

```text
d(t) = ||x_perturbed(t) - x_base(t)||
```

Largest Lyapunov estimate:

```text
lambda = slope of ln(d(t) / d0) versus t
```

Classification threshold:

```text
lambda > 1e-8 s^-1 => chaotic for this demonstration scale
```

### Software Architecture

- `analysis/lyapunov.py`: paired-simulation divergence.
- `analysis/plots.py`: semilog divergence plot.
- `analysis/stability.py`: uses Lyapunov exponent for automatic classification.

### Complete Python Code

Complete implementation:

- `analysis/lyapunov.py`
- `analysis/stability.py`
- `analysis/plots.py`

Run:

```powershell
python main.py --headless --scenario binary-chaos --duration-days 250 --dt-hours 4 --lyapunov --plots
```

### Improvements and Extensions

- Add Benettin renormalization for a more rigorous largest Lyapunov exponent.
- Run a perturbation ensemble and report confidence intervals.
- Fit only the early linear region before saturation.

## Phase 7 - Data Collection and Graphs

### Concept Explanation

CSV and plots let you defend every claim. Judges can see energy conservation, radius growth, collision timing, and chaotic divergence.

### Physics Background

Stable orbits should show bounded radius and nearly constant total energy. Escape should show increasing radius. Collision should show radius dropping to body overlap. Chaos should show divergence on a semilog plot.

### Mathematical Equations

Recorded scalar quantities:

```text
speed = |v|
radius = |r_body - r_central|
E = K + U
L_z = sum m (x v_y - y v_x)
```

### Software Architecture

- `simulation/recorder.py`: writes `history.csv`.
- `analysis/plots.py`: writes `.png` figures.
- `results/`: stores generated outputs.

### Complete Python Code

Complete implementation:

- `simulation/recorder.py`
- `analysis/plots.py`

Run:

```powershell
python main.py --headless --scenario stable --plots
```

### Improvements and Extensions

- Add JSON summaries for automatic report generation.
- Add comparison plots for Euler vs Verlet vs RK4.
- Add parameter-sweep heatmaps for stability regions.

## Phase 8 - Software Engineering

### Concept Explanation

A clean folder structure makes the project look engineered rather than improvised. It also lets you test and explain each subsystem independently.

### Physics Background

The physics engine should not depend on Pygame. The same equations should drive visualization, headless experiments, and graphs.

### Mathematical Equations

All modules share the same SI-unit state:

```text
state = {m_i, R_i, r_i, v_i}
```

### Software Architecture

Responsibilities:

- `main.py`: command-line entry point.
- `physics/`: constants, bodies, forces, integrators, measured quantities.
- `simulation/`: timestep loop and data recorder.
- `visualization/`: Pygame user interface.
- `analysis/`: classification, Lyapunov, orbital period, plots.
- `experiments/`: scenario definitions and batch runner.
- `reports/`: written submission material.
- `results/`: generated CSV and figures.
- `tests/`: smoke tests for energy behavior.

### Complete Python Code

Complete implementation is the full project tree. The engine can be used independently:

```python
from experiments.scenarios import stable_star_planet_moon
from physics.constants import DAY, HOUR
from physics.integrators import VelocityVerletIntegrator
from simulation.simulator import NBodySimulator

scenario = stable_star_planet_moon()
sim = NBodySimulator(scenario.clone_bodies(), dt=4 * HOUR, integrator=VelocityVerletIntegrator())
history = sim.run(365 * DAY)
```

### Improvements and Extensions

- Add `pyproject.toml` and package metadata.
- Add continuous integration tests.
- Add typed configuration files for experiments.

## Phase 9 - Competition Strategy

### Concept Explanation

Judges reward correctness, interpretation, and evidence. The best return on effort is to show one accurate stable run, then prove the same engine handles failure and chaos cases.

### Physics Background

A high-quality demonstration should connect visuals with conserved quantities and physical thresholds. For example, collision is not "the dots touched"; it is `d <= R_i + R_j`.

### Mathematical Equations

Use these in slides or the report:

```text
F = G m1 m2 / r^2
E = K + U
epsilon = 0.5 v^2 - GM/r
lambda = d/dt ln(d(t)/d0)
```

### Software Architecture

Lead with:

1. Stable orbit and energy conservation.
2. Escape trajectory classified by positive specific energy.
3. Collision classified by radius overlap.
4. Binary chaos classified by Lyapunov divergence.
5. Parameter and timestep comparison if time permits.

### Complete Python Code

Use:

- `main.py` for the demo.
- `experiments/run_experiments.py` for reproducible batch results.
- `analysis/plots.py` for evidence figures.

### Improvements and Extensions

Maximum score per effort:

- Energy conservation plot.
- Automatic classification.
- Lyapunov divergence plot.
- Clean README and report.

Nice to have:

- 3D rendering.
- More parameter sweeps.
- Video export.

Likely to impress judges:

- Verlet vs Euler energy-drift comparison.
- Scenario table with initial conditions and expected physics.
- A live stats panel showing energy and angular momentum.

## Phase 10 - Final Submission

### Concept Explanation

The final submission should make the project easy to run and easy to evaluate. A judge should understand what is being simulated, how accuracy is checked, and what each scenario proves.

### Physics Background

Your conclusion should connect outcomes to the measured quantities: stable means bounded radius and conserved energy; escape means positive energy; collision means radius overlap; chaos means exponential divergence.

### Mathematical Equations

Include:

```text
a_i = G sum m_j (r_j-r_i)/|r_j-r_i|^3
K = sum 0.5 m v^2
U = -sum G m_i m_j/r_ij
L_z = sum m(xv_y-yv_x)
lambda = slope ln(d/d0)
```

### Software Architecture

Submission package:

- `README.md`: install and run instructions.
- `reports/technical_report.md`: this document.
- `reports/demo_video_script.md`: narration plan.
- `results/`: generated CSV and plots.
- source folders: complete implementation.

### Complete Python Code

All code is under `orbital_dynamics_project/`. Generate final result artifacts with:

```powershell
python -m experiments.run_experiments
```

### Improvements and Extensions

Before submitting:

- Run all scenarios with `--plots`.
- Capture a 2-3 minute demo video.
- Add screenshots of the energy and divergence plots.
- Include a table of classification results from `results/summary.csv`.
