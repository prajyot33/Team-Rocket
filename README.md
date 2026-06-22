# Orbital Dynamics and Stability Simulation

Competition-ready Newtonian multi-body simulator with real SI constants, generic N-body force calculation, Velocity Verlet/RK4 integration, automated stability classification, Lyapunov chaos detection, data export, Matplotlib plots, and an interactive Pygame visualizer.

## Why This Scores Well

- **Simulation accuracy:** uses Newtonian pairwise gravity with real `G`, masses, radii, AU, and SI units.
- **Numerical stability:** defaults to Velocity Verlet, a symplectic integrator that keeps long-term orbital energy bounded.
- **Experimental depth:** includes stable orbit, escape, collision, binary-star chaos, and random five-body experiments.
- **Physical interpretation:** computes energy, angular momentum, orbital velocity, orbital period, radius, and Lyapunov divergence.
- **Technical implementation:** separates physics, simulation, visualization, analysis, and experiments into clean modules.

## Install

```powershell
cd C:\Users\prajy\OneDrive\Documents\MediGuide\orbital_dynamics_project
python -m pip install -r requirements.txt
```

The visualizer imports `pygame`; the requirements use `pygame-ce`, a maintained drop-in package that provides the same import name and works better on newer Python versions.

## Run Interactive Demo

Professional astronomy lab interface:

```powershell
python astro_lab.py --scenario stable
python astro_lab.py --scenario binary-chaos
```

Classic compact viewer:

```powershell
python main.py --scenario stable
python main.py --scenario escape
python main.py --scenario collision
python main.py --scenario binary-chaos
python main.py --scenario random5
```

Controls:

- `space`: play/pause
- mouse wheel: zoom
- right/middle drag: pan
- `[` / `]`: rotate camera yaw
- arrow up/down: change camera pitch
- `tab`: select next body and follow it
- `r`: reset

Classic viewer controls:

- `space`: pause/resume
- `+` / `-` or mouse wheel: zoom
- arrow keys or `WASD`: pan camera
- `v`: velocity vectors
- `f`: force vectors
- `t`: trajectory trails
- `tab`: select body
- `c`: center camera on selected body
- `.` / `,`: simulation speed up/down

## Run Headless Experiments

```powershell
python main.py --headless --scenario stable --duration-days 370 --dt-hours 4 --plots
python main.py --headless --scenario binary-chaos --duration-days 250 --dt-hours 4 --lyapunov --plots
python -m experiments.run_experiments
```

Outputs are written under `results/`:

- `history.csv`: time, position, velocity, speed, radius, energy, angular momentum
- `energy.png`: kinetic, potential, and total energy vs time
- `velocity.png`: velocity vs time
- `radius.png`: orbital radius vs time
- `divergence.png`: Lyapunov divergence vs time for chaos scenarios
- `summary.csv`: classification summary when running all experiments

## Folder Structure

```text
orbital_dynamics_project/
├── main.py
├── astro_lab.py
├── app/
│   ├── camera.py
│   ├── lab.py
│   ├── metrics.py
│   ├── renderer.py
│   ├── research.py
│   ├── state.py
│   ├── theme.py
│   └── widgets.py
├── physics/
│   ├── body.py
│   ├── constants.py
│   ├── engine.py
│   ├── integrators.py
│   └── quantities.py
├── simulation/
│   ├── recorder.py
│   └── simulator.py
├── visualization/
│   └── pygame_viewer.py
├── analysis/
│   ├── lyapunov.py
│   ├── orbital_period.py
│   ├── plots.py
│   └── stability.py
├── experiments/
│   ├── run_experiments.py
│   └── scenarios.py
├── reports/
│   ├── demo_video_script.md
│   ├── product_redesign_plan.md
│   └── technical_report.md
├── results/
└── tests/
```

## Key Design Choice: Velocity Verlet vs RK4

Velocity Verlet is the default because orbital simulations need good long-term conservation of invariants. RK4 has higher local order, but it is not symplectic, so total energy may drift over long integrations. The project includes RK4 and Euler for comparison:

```powershell
python main.py --headless --scenario stable --integrator verlet --duration-days 370
python main.py --headless --scenario stable --integrator rk4 --duration-days 370
python main.py --headless --scenario stable --integrator euler --duration-days 370
```

## Stability Criteria

- **Collision:** any pair reaches `d_ij <= R_i + R_j`.
- **Escape:** target body has positive specific orbital energy and outward radial velocity, or radius grows beyond `6 * initial_radius`.
- **Stable Orbit:** energy drift below `5e-3`, radius coefficient of variation below `0.25`, and at least `0.75` revolutions.
- **Chaotic Motion:** simplified Lyapunov exponent above `1e-8 s^-1`, or bounded but strongly irregular motion.

## Competition Pitch

Open with the stable orbit and energy conservation plot, then show the same engine detecting escape, collision, and chaos automatically. Judges usually respond strongly to quantitative validation: show the stable orbit period near one year, total-energy drift near zero, and the Lyapunov divergence curve for the binary-star scenario.
