# Product Redesign Plan: Orbital Dynamics Laboratory

## Product Goal

The application should open like a professional astronomy and mission-analysis tool: a live space viewport, object explorer, scientific inspector, experiment controls, and research dashboard. The physics engine remains the trusted core. The redesign focuses on presentation, workflow, and interpretability.

## Technology Choice

Use `pygame-ce` for the desktop app shell because the project is already Python/Pygame-based and competition judges can run it with one install command. The app uses custom rendering and custom UI widgets instead of a pre-built physics engine or heavyweight GUI framework.

Current implementation:

- Entry point: `astro_lab.py`
- Application shell: `app/lab.py`
- Camera: `app/camera.py`
- Renderer: `app/renderer.py`
- UI widgets: `app/widgets.py`
- Live metrics: `app/metrics.py`
- Research mode: `app/research.py`
- App state: `app/state.py`
- Theme: `app/theme.py`

Future premium option: migrate the UI shell to Qt/PySide while keeping `physics/`, `simulation/`, `analysis/`, and `experiments/` unchanged. For this competition timeline, the custom Pygame shell is the fastest route to a polished, reliable deliverable.

## Feature 1 - Modern UI

Priority: Critical

### Architecture

The application is divided into five stable regions:

- Top bar: play, pause, reset, analyze, speed, camera mode.
- Left panel: scenario explorer, body hierarchy, search field.
- Center viewport: cinematic orbital scene.
- Right panel: selected-object scientific inspector and experiment edits.
- Bottom panel: metrics, graphs, research summary.

Implementation:

- `app/lab.py`: owns layout rectangles and click routing.
- `app/widgets.py`: buttons, segmented controls, status pills, mini charts.
- `app/theme.py`: consistent color, text, and panel styling.

### UI Design

The UI uses a NASA-style dark control-room palette: deep background, restrained panels, high-contrast scientific text, and cyan/green accents for active controls and stable states. It avoids the plain black-screen Pygame assignment feel.

### Code Example

```python
self.top_bar = pygame.Rect(0, 0, width, 64)
self.left_panel = pygame.Rect(12, 76, 285, height - 340)
self.right_panel = pygame.Rect(width - 360, 76, 348, height - 340)
self.bottom_panel = pygame.Rect(12, height - 252, width - 24, 240)
self.viewport = pygame.Rect(
    self.left_panel.right + 12,
    76,
    self.right_panel.x - self.left_panel.right - 24,
    height - 340,
)
```

### Performance Considerations

The UI is immediate-mode and lightweight. Panels are drawn each frame, while physics remains independent and vectorized. If the body count grows, throttle dashboard sampling and trail length before touching physics.

## Feature 2 - Camera System

Priority: Critical

### Architecture

`SpaceCamera` provides:

- Zoom
- Pan
- Rotate yaw
- Pitch tilt
- Follow selected body
- Free camera
- Cinematic orbit camera
- Smooth interpolation

### UI Design

Top-bar segmented control switches camera modes: `Free`, `Follow`, `Cinema`. Mouse wheel zooms, right/middle drag pans, brackets rotate yaw, arrow keys adjust pitch.

### Code Example

```python
def project(self, position, viewport):
    relative = position - self.focus
    rotated_x = relative[0] * cos_yaw - relative[1] * sin_yaw
    rotated_y = relative[0] * sin_yaw + relative[1] * cos_yaw
    tilted_y = rotated_y * np.cos(self.pitch)
    return screen_x, screen_y, depth
```

### Performance Considerations

Projection is `O(N)` for bodies and `O(trail length)` for trails. Keep trails capped. The camera does not affect physics state.

## Feature 3 - Visual Quality

Priority: Critical

### Architecture

`SpaceRenderer` owns:

- Deterministic starfield
- Gradient space background
- Orbit-plane grid
- Anti-aliased orbit trails
- Body glow
- Planet labels
- Dynamic body scaling
- Selected-object rings
- Velocity and force vectors

### UI Design

The viewport should look like a space exploration scene, not a graph. Trails are subtle, labels are readable, and selected objects receive a clear cyan focus ring.

### Code Example

```python
pygame.draw.aalines(trail_surface, color, False, points)
pygame.draw.circle(glow_surface, (*body.color, alpha), (x, y), glow_radius)
```

### Performance Considerations

Glows are drawn on one alpha surface per frame. For large body counts, render glows only for selected and massive bodies. Trail length is capped by `state.trail_limit`.

## Feature 4 - Object Inspection System

Priority: Critical

### Architecture

The selected-object panel reads directly from current simulation state and `LiveMetrics`.

Displayed:

- Name
- Mass
- Radius
- Velocity
- Orbital period
- Distance from parent body
- Total energy
- Angular momentum
- Status

### UI Design

The right panel behaves like a spacecraft telemetry inspector. It shows a color swatch, body name, status pill, numeric metrics, and experiment controls.

### Code Example

```python
metric_row(screen, font, "Mass", format_si(body.mass, "kg"), x, y, width)
metric_row(screen, font, "Velocity", format_si(snapshot.orbital_velocity / 1000, "km/s"), x, y + 48, width)
draw_status_pill(screen, font, status_rect, snapshot.status)
```

### Performance Considerations

Metrics are scalar computations over current bodies and are cheap for small to medium N-body systems.

## Feature 5 - Scientific Dashboard

Priority: High Impact

### Architecture

`LiveMetrics` computes current:

- Total energy
- Potential energy
- Kinetic energy
- Angular momentum
- Orbital velocity
- Orbital radius
- Energy drift
- Lyapunov estimate when available

`TimeSeries` stores rolling data for in-app charts.

### UI Design

The bottom panel has tabs:

- Metrics
- Graphs
- Research

This keeps the interface dense but controlled.

### Code Example

```python
state.series.total.append(snapshot.total_energy)
state.series.selected_radius.append(snapshot.orbital_radius / AU)
state.series.selected_speed.append(snapshot.orbital_velocity / 1000.0)
```

### Performance Considerations

Dashboard sampling is throttled so graphs do not store every physics step. Keep only recent samples in bounded deques.

## Feature 6 - Experiment Lab

Priority: High Impact

### Architecture

The experiment lab modifies selected-object parameters and reruns the simulation using the original scenario bodies as editable seeds.

Current controls:

- Mass increase/decrease
- Velocity increase/decrease
- Position nudge
- Rerun
- Scenario switching

### UI Design

The lab lives inside the selected-object panel so users naturally select an object, edit it, and rerun.

### Code Example

```python
def scale_selected_velocity(self, factor):
    body = self.selected_body()
    body.velocity = body.velocity * factor
    self.original_bodies[self.selected_index].velocity *= factor
```

### Performance Considerations

Editing parameters does not require rebuilding the whole app. Only the simulator and trails reset.

## Feature 7 - Research Mode

Priority: Critical

### Architecture

`ResearchAnalyzer` runs a headless analysis from the current app state:

- Stability classification
- Orbital period
- Energy conservation error
- Collision clearance
- Escape evidence
- Lyapunov estimate for chaos scenarios

### UI Design

The `Analyze` button pauses the live simulation, runs the analysis, and switches the bottom panel to a concise scientific summary.

### Code Example

```python
report = self.research.analyze(self.state)
self.state.analysis_result = report.result
self.state.research_summary = report.summary_lines
self.state.active_bottom_tab = "Research"
```

### Performance Considerations

For interactive use, analysis duration is capped to the scientifically useful window. For final reports, use the batch runner for full-resolution plots.

## Feature 8 - Data Visualization

Priority: High Impact

### Architecture

Two layers exist:

- In-app mini charts for live judges' demo.
- Matplotlib export through existing `analysis/plots.py` for final report images.

Displayed in app:

- Energy vs time
- Distance vs time
- Velocity vs time

Generated externally:

- Energy vs time
- Distance vs time
- Velocity vs time
- Angular momentum can be added with the same plot interface
- Chaos divergence vs time

### UI Design

Charts sit in the bottom panel so the viewport remains dominant.

### Code Example

```python
mini_chart(screen, rect, state.series.total, font, "Energy vs Time")
mini_chart(screen, rect, state.series.selected_radius, font, "Distance vs Time")
mini_chart(screen, rect, state.series.selected_speed, font, "Velocity vs Time")
```

### Performance Considerations

Mini charts render at most the last 180 points, avoiding expensive per-frame plotting.

## Feature 9 - Software Feel

Priority: Critical

### Architecture

The app is not a collection of scripts. It has a product shell:

- App state object
- Renderer object
- Camera object
- Research analyzer object
- Widget toolkit
- Theme system

### UI Design

The feel should be:

- Mission control density
- Universe Sandbox interaction
- Scientific research credibility

The first screen is the working laboratory, not a splash screen.

### Performance Considerations

The most visible performance risk is trails and alpha glow, not gravity. Tune visual density per body count.

## Feature 10 - Implementation Plan

Priority: Critical

### Phase 1: Immediate WOW Pass

Status: Implemented

- Add `astro_lab.py`.
- Add professional layout.
- Add starfield, glow, orbit trails, labels.
- Add follow/free/cinematic camera.
- Add object inspector and dashboard.
- Add Analyze System.

### Phase 2: Scientific Polish

Status: Partially implemented

- Add angular momentum chart in the bottom panel.
- Add chaos divergence mini-chart after Analyze.
- Add export button for graphs and CSV.
- Add stability badges per body in object explorer.

### Phase 3: Premium Interaction

Status: Next

- Add drag-to-set velocity vector.
- Add timeline scrubber.
- Add save/load experiment presets.
- Add screenshot/video capture.

### Phase 4: Presentation Upgrade

Status: Next

- Add generated planet texture sprites.
- Add real NASA-style color maps for major objects.
- Add cinematic fly-through presets for demo video.

## Feature Priority Ranking

Critical:

- Modern UI shell
- 3D-feeling viewport
- Camera modes
- Object inspector
- Research mode
- Professional visual style

High Impact:

- Experiment lab
- Live dashboard
- In-app charts
- Body search and hierarchy
- Velocity and force vectors

Medium Impact:

- Parameter sliders instead of buttons
- Angular momentum chart tab
- Export controls inside app
- Saved presets

Nice to Have:

- Textured planets
- Video recording
- True 3D physics option
- Qt/PySide port
- Multi-window graph workspace

## Fastest Path to Making Judges Say WOW

1. Launch `python astro_lab.py --scenario stable`.
2. Start in cinematic camera mode and show the polished starfield, glow, labels, trails, and live telemetry.
3. Click Earth or the planet, show the selected-object inspector.
4. Open the Graphs tab and show energy, distance, and velocity updating live.
5. Click `Analyze`, then show the research summary with stability classification and energy conservation error.
6. Switch to `binary-chaos`, click `Analyze`, and show `Chaotic Motion` with a Lyapunov estimate.
7. Switch to `collision`, run briefly, and show that the same lab detects collision risk scientifically.

The strongest judging moment is the contrast between a beautiful live viewport and hard quantitative evidence in the dashboard. That combination makes it feel like professional astronomy software, not just an animation.
