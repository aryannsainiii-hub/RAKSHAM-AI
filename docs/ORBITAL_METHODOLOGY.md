# Orbital methodology

## Current implemented model

Synthetic fixtures use position `r(t) = r0 + v*t`, where positions and separation are kilometres, velocity is kilometres per second, and `t` is elapsed seconds from fixture epoch. All pair coordinates are declared to share an **illustrative inertial** frame. The UI scene is schematic and its coordinates are not mapped to scene geometry. Fixture epoch is UTC ISO-8601.

The screening samples each fixture pair at the requested interval, keeps its closest sample, then searches a bounded interval around that sample at 1-second increments. A pair is returned when its minimum geometric separation is below the configured distance. This is not a gravitational orbit propagator, SGP4, validated encounter refinement, or complete catalogue search.

The candidate maneuver instantaneously changes the along-track y velocity by Δv after a configured lead interval, then evaluates position under the same constant-velocity model. No gravity, Earth oblateness, drag, attitude, propulsion, uncertainty, covariance, or mission constraints are included.

Priority bands use geometric distance only: <1 km critical, <5 km high, <25 km guarded, otherwise low. Score is a simple heuristic display value and is never a probability. The screening event and resulting scenario are synthetic.

## Intended next scientific step

Use compatible, validated TLE inputs with an established SGP4 implementation, explicit TEME handling and epoch/time conversion; propagate objects into a common frame and test known vectors. OMM must use a compatible parser/propagator and must not be silently treated as TLE. Operational-grade probability requires state covariance and a validated probabilistic encounter method, none of which is implemented here.
