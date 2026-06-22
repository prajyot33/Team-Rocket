from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from physics.body import Body
from physics.constants import (
    AU,
    EARTH_MASS,
    EARTH_RADIUS,
    G,
    JUPITER_MASS,
    JUPITER_RADIUS,
    MOON_MASS,
    MOON_RADIUS,
    SOLAR_MASS,
    SOLAR_RADIUS,
)
from physics.engine import center_of_mass_frame


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    bodies: list[Body]
    default_duration_days: float
    default_dt_hours: float
    expected: str
    explanation: str
    central_index: int = 0
    target_index: int = 1
    softening: float = 0.0

    def clone_bodies(self) -> list[Body]:
        return [body.copy() for body in self.bodies]


def _circular_speed(total_mass: float, radius: float) -> float:
    return float(np.sqrt(G * total_mass / radius))


def stable_star_planet_moon() -> Scenario:
    earth_distance = AU
    moon_distance = 384_400_000.0
    bodies = [
        Body("Sun", SOLAR_MASS, SOLAR_RADIUS, [0.0, 0.0], [0.0, 0.0], (255, 210, 70)),
        Body(
            "Earth",
            EARTH_MASS,
            EARTH_RADIUS,
            [earth_distance, 0.0],
            [0.0, _circular_speed(SOLAR_MASS, earth_distance)],
            (70, 150, 255),
        ),
        Body(
            "Moon",
            MOON_MASS,
            MOON_RADIUS,
            [earth_distance + moon_distance, 0.0],
            [0.0, _circular_speed(SOLAR_MASS, earth_distance) + 1_022.0],
            (210, 210, 210),
        ),
    ]
    center_of_mass_frame(bodies)
    return Scenario(
        key="stable",
        title="Stable star-planet-moon system",
        bodies=bodies,
        default_duration_days=420.0,
        default_dt_hours=2.0,
        expected="Earth completes a nearly closed orbit while the Moon remains bound to Earth.",
        explanation="The planet starts near circular velocity sqrt(GM/r), and the moon is given Earth's heliocentric velocity plus lunar orbital velocity.",
        target_index=1,
    )


def escape_trajectory() -> Scenario:
    r = AU
    escape_speed = np.sqrt(2.0 * G * SOLAR_MASS / r)
    jupiter_distance = 5.2 * AU
    bodies = [
        Body("Sun", SOLAR_MASS, SOLAR_RADIUS, [0.0, 0.0], [0.0, 0.0], (255, 210, 70)),
        Body("Probe", 1.0e20, EARTH_RADIUS, [r, 0.0], [0.0, 1.05 * escape_speed], (255, 110, 90)),
        Body(
            "Jupiter",
            JUPITER_MASS,
            JUPITER_RADIUS,
            [0.0, jupiter_distance],
            [-_circular_speed(SOLAR_MASS, jupiter_distance), 0.0],
            (220, 170, 120),
        ),
    ]
    center_of_mass_frame(bodies)
    return Scenario(
        key="escape",
        title="Escape trajectory",
        bodies=bodies,
        default_duration_days=700.0,
        default_dt_hours=4.0,
        expected="The probe has positive specific orbital energy and leaves the inner system.",
        explanation="At 1 AU the escape speed is sqrt(2GM/r). The probe is launched 5% above that speed.",
        target_index=1,
    )


def planet_star_collision() -> Scenario:
    start_radius = 0.10 * AU
    jupiter_distance = 3.8 * AU
    bodies = [
        Body("Sun", SOLAR_MASS, SOLAR_RADIUS, [0.0, 0.0], [0.0, 0.0], (255, 210, 70)),
        Body("FallingPlanet", EARTH_MASS, EARTH_RADIUS, [start_radius, 0.0], [-20_000.0, 0.0], (255, 70, 60)),
        Body(
            "OuterGiant",
            JUPITER_MASS,
            JUPITER_RADIUS,
            [-jupiter_distance, 0.0],
            [0.0, -_circular_speed(SOLAR_MASS, jupiter_distance)],
            (190, 150, 110),
        ),
    ]
    center_of_mass_frame(bodies)
    return Scenario(
        key="collision",
        title="Planet-star collision",
        bodies=bodies,
        default_duration_days=15.0,
        default_dt_hours=0.1,
        expected="The inner planet lacks tangential speed and falls into the star.",
        explanation="The planet is given a radial inward velocity and almost no tangential velocity, so angular momentum cannot prevent impact.",
        target_index=1,
    )


def binary_star_chaos() -> Scenario:
    separation = 1.0 * AU
    star_speed = np.sqrt(G * SOLAR_MASS / (2.0 * separation))
    bodies = [
        Body("StarA", SOLAR_MASS, SOLAR_RADIUS, [-0.5 * separation, 0.0], [0.0, -star_speed], (255, 220, 90)),
        Body("StarB", SOLAR_MASS, SOLAR_RADIUS, [0.5 * separation, 0.0], [0.0, star_speed], (255, 170, 70)),
        Body("Planet", 2.0 * EARTH_MASS, EARTH_RADIUS, [0.0, 1.35 * AU], [-18_000.0, 0.0], (110, 190, 255)),
        Body("Perturber", 0.08 * SOLAR_MASS, 0.25 * SOLAR_RADIUS, [1.6 * AU, -1.1 * AU], [8_000.0, 13_000.0], (180, 120, 255)),
    ]
    center_of_mass_frame(bodies)
    return Scenario(
        key="binary-chaos",
        title="Binary-star chaotic system",
        bodies=bodies,
        default_duration_days=250.0,
        default_dt_hours=2.0,
        expected="The planet's orbit is strongly perturbed by the binary and the passing low-mass star.",
        explanation="The time-dependent binary potential and nearby perturber create sensitive dependence on initial conditions.",
        central_index=0,
        target_index=2,
    )


def random_five_body(seed: int = 7) -> Scenario:
    rng = np.random.default_rng(seed)
    bodies: list[Body] = []
    palette = [(255, 214, 90), (90, 180, 255), (255, 120, 110), (150, 235, 150), (190, 140, 255)]
    for index in range(5):
        mass = float(rng.uniform(0.15, 1.2) * SOLAR_MASS)
        radius = float(np.clip((mass / SOLAR_MASS) ** 0.8, 0.25, 1.2) * SOLAR_RADIUS)
        position = rng.uniform(-1.4 * AU, 1.4 * AU, size=2)
        velocity = rng.normal(0.0, 12_000.0, size=2)
        bodies.append(Body(f"Body{index + 1}", mass, radius, position, velocity, palette[index]))
    center_of_mass_frame(bodies)
    return Scenario(
        key="random5",
        title="Random five-body gravitational system",
        bodies=bodies,
        default_duration_days=500.0,
        default_dt_hours=1.0,
        expected="Close encounters and energy exchange produce irregular bounded, escaping, or colliding outcomes depending on seed.",
        explanation="The system begins near virial speeds but with no symmetry, so interactions rapidly amplify small differences.",
        central_index=0,
        target_index=1,
        softening=0.0,
    )


def all_scenarios() -> dict[str, Scenario]:
    scenarios = [
        stable_star_planet_moon(),
        escape_trajectory(),
        planet_star_collision(),
        binary_star_chaos(),
        extended_solar_system(),
        random_five_body(),
    ]
    return {scenario.key: scenario for scenario in scenarios}


def get_scenario(key: str) -> Scenario:
    scenarios = all_scenarios()
    if key not in scenarios:
        options = ", ".join(sorted(scenarios))
        raise ValueError(f"Unknown scenario {key!r}. Choose one of: {options}")
    return scenarios[key]

def extended_solar_system() -> Scenario:
    earth_distance = AU
    moon_distance = 384_400_000

    jupiter_distance = 5.2 * AU

    jupiter_speed = _circular_speed(SOLAR_MASS, jupiter_distance)

    bodies = [
        Body("Sun", SOLAR_MASS, SOLAR_RADIUS,
             [0, 0], [0, 0], (255, 210, 70)),

        Body("Earth", EARTH_MASS, EARTH_RADIUS,
             [earth_distance, 0],
             [0, _circular_speed(SOLAR_MASS, earth_distance)],
             (70, 150, 255)),

        Body("Moon", MOON_MASS, MOON_RADIUS,
             [earth_distance + moon_distance, 0],
             [0, _circular_speed(SOLAR_MASS, earth_distance) + 1022],
             (220, 220, 220)),

        Body("Jupiter",
             JUPITER_MASS,
             JUPITER_RADIUS,
             [jupiter_distance, 0],
             [0, jupiter_speed],
             (210, 170, 120)),

        Body("Io",
             8.93e22,
             1.821e6,
             [jupiter_distance + 421_700_000, 0],
             [0, jupiter_speed + 17300],
             (255, 220, 120)),

        Body("Europa",
             4.80e22,
             1.560e6,
             [jupiter_distance + 671_000_000, 0],
             [0, jupiter_speed + 13740],
             (200, 200, 255)),

        Body("Ganymede",
             1.48e23,
             2.634e6,
             [jupiter_distance + 1_070_000_000, 0],
             [0, jupiter_speed + 10880],
             (180, 180, 180)),

        Body("Callisto",
             1.08e23,
             2.410e6,
             [jupiter_distance + 1_883_000_000, 0],
             [0, jupiter_speed + 8200],
             (150, 150, 150)),
    ]

    center_of_mass_frame(bodies)

    return Scenario(
        key="extended",
        title="Extended Solar System",
        bodies=bodies,
        default_duration_days=1000,
        default_dt_hours=4,
        expected="Planets and moons remain gravitationally bound.",
        explanation="Expanded solar system including Jupiter's Galilean moons.",
        target_index=1,
    )