# Architecture

The Vite React client calls a versioned FastAPI REST service. The service owns screening and maneuver computations; SQLite stores calculated events and candidate results. The browser displays API results and exposes clear synthetic-data labels. The 3D-like view is a CSS schematic and does not render propagated ephemerides.

Each screening request validates horizon (1–72 h), sampling step (1–60 min), and threshold (0–1000 km). The service checks the fixture pairs, refines the best sampled instant at 1-second increments, returns provenance/limitations/runtime, and saves the computed event. The maneuver endpoint retrieves the saved event, applies an illustrative velocity delta, computes the model separation, and stores its comparison.

SQLite is initialized on demand; `RAKSHAM_DB_PATH` selects its location. This prototype has no migration framework or multi-user access controls.
