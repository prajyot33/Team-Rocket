# Demo Video Script

## 0:00-0:15 - Opening

"This project is a Newtonian N-body orbital dynamics simulator. It computes pairwise gravitational forces between arbitrary bodies using real SI constants, then analyzes whether the resulting motion is stable, escaping, colliding, or chaotic."

Show the Pygame stable scenario.

```powershell
python main.py --scenario stable
```

## 0:15-0:45 - Physics Engine

"The engine uses Newton's gravitational law for every pair of bodies. The default integrator is Velocity Verlet, chosen because it is symplectic and keeps long-term energy drift small in orbital systems."

Toggle velocity vectors with `v` and force vectors with `f`.

## 0:45-1:15 - Stable Orbit

"In the stable star-planet-moon scenario, Earth starts near circular velocity at 1 AU. The measured period is about one year, and total energy remains nearly constant."

Show:

```powershell
python main.py --headless --scenario stable --duration-days 370 --dt-hours 4 --plots
```

Display `results/stable/energy.png` and `results/stable/radius.png`.

## 1:15-1:40 - Escape Trajectory

"The escape scenario launches a probe at 1.05 times solar escape speed at 1 AU. The classifier marks it as escape because its specific orbital energy is positive and radial velocity is outward."

```powershell
python main.py --headless --scenario escape --plots
```

## 1:40-2:00 - Collision

"The collision scenario gives a planet too little angular momentum, so gravity pulls it into the star. Collision is detected when distance becomes less than the sum of physical radii."

```powershell
python main.py --headless --scenario collision
```

## 2:00-2:35 - Chaos

"For chaos, I run two simulations that differ by only a 10-meter displacement. Their separation grows exponentially in the binary-star system, and the fitted Lyapunov exponent crosses the chaos threshold."

```powershell
python main.py --headless --scenario binary-chaos --duration-days 250 --dt-hours 4 --lyapunov --plots
```

Display `results/binary-chaos/divergence.png`.

## 2:35-3:00 - Closing

"The same engine handles all scenarios: stable orbit, escape, collision, chaos, and random five-body motion. The output includes CSV data and plots for energy, speed, radius, and trajectory divergence, making the simulation both visual and scientifically testable."
