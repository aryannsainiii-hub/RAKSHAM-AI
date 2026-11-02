# API

Base URL: `http://localhost:8000`; interactive OpenAPI: `/docs`.

- `GET /health`, `GET /api/v1/system/status`
- `GET /api/v1/objects?search=&limit=100`, `GET /api/v1/objects/{object_id}`
- `GET /api/v1/data/status`; refresh returns 503 until a provider is configured.
- `POST /api/v1/screening/run` body `{"horizon_hours":24,"step_minutes":5,"threshold_km":25}`
- `GET /api/v1/events?limit=100`, `GET /api/v1/events/{event_id}`
- `POST /api/v1/simulations` body `{"event_id":"…","along_track_delta_v_m_s":2,"burn_lead_minutes":30}`
- `GET /api/v1/simulations`, `GET /api/v1/simulations/{simulation_id}`
- `POST /api/v1/simulations/{simulation_id}/compare` accepts the same body as simulation creation.
- `GET /api/v1/analytics/summary`
- `GET /api/v1/reports/events.csv`, `GET /api/v1/reports/simulations.csv`
- `POST /api/v1/explanations` accepts an event reference and returns a deterministic limitations-aware explanation.

Screening response includes `job_id`, `events`, counts, runtime, model, and limitations. Events contain both IDs, ISO UTC TCA, geometric miss distance in km, heuristic risk, frame, and `simulated: true`. Invalid inputs receive FastAPI 422 validation responses; missing stored IDs receive 404. Errors are not yet normalized to a custom envelope.
