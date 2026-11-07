"""RAKSHAM research prototype API. Synthetic states use a transparent toy model."""
from __future__ import annotations

import json
import math
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("RAKSHAM_DB_PATH", str(ROOT / "backend" / "raksham.sqlite3")))
NOW = datetime.now(timezone.utc)


class ScreenRequest(BaseModel):
    horizon_hours: int = Field(default=24, ge=1, le=72)
    step_minutes: int = Field(default=5, ge=1, le=60)
    threshold_km: float = Field(default=25, gt=0, le=1000)


class ManeuverRequest(BaseModel):
    event_id: str
    along_track_delta_v_m_s: float = Field(ge=-100, le=100)
    burn_lead_minutes: int = Field(default=30, ge=1, le=1440)


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, created_at TEXT, payload TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS simulations (id TEXT PRIMARY KEY, created_at TEXT, payload TEXT)")
    return db


# Stable synthetic fixture, SI-derived km coordinates in a shared illustrative inertial frame.
OBJECTS = [
    {"id":"SYN-1001", "name":"Demo Observer", "epoch":NOW.isoformat(), "source":"Synthetic fixture", "frame":"illustrative inertial", "position_km":[7000,0,0], "velocity_km_s":[0,7.5,0], "simulated":True},
    {"id":"SYN-1002", "name":"Demo Target A", "epoch":NOW.isoformat(), "source":"Synthetic fixture", "frame":"illustrative inertial", "position_km":[7000,-60,0], "velocity_km_s":[0,7.51,0.004], "simulated":True},
    {"id":"SYN-1003", "name":"Demo Target B", "epoch":NOW.isoformat(), "source":"Synthetic fixture", "frame":"illustrative inertial", "position_km":[7200,100,25], "velocity_km_s":[0,7.2,0], "simulated":True},
]


def position(obj, seconds, dv=0.0, burn_after=0.0):
    dt = max(0.0, seconds - burn_after)
    return tuple(obj["position_km"][i] + obj["velocity_km_s"][i] * seconds + ((dv * dt / 1000) if i == 1 else 0) for i in range(3))


def separation(a, b, seconds):
    pa, pb = position(a, seconds), position(b, seconds)
    return math.sqrt(sum((pa[i]-pb[i])**2 for i in range(3)))


def risk(distance, age_hours=0):
    level = "CRITICAL" if distance < 1 else "HIGH" if distance < 5 else "GUARDED" if distance < 25 else "LOW"
    if age_hours > 24 and level != "LOW":
        level = "DATA LIMITED"
    return {"priority":level,"score":round(max(0,min(100,100-distance*2)),1),"basis":"Heuristic geometric-distance bands; score is not collision probability.","data_warning":"Synthetic fixture; no covariance or operational uncertainty model."}


app = FastAPI(title="RAKSHAM API", version="0.1.0", description="Research prototype; synthetic demo states are not flight data.")
origins = os.getenv("RAKSHAM_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    try:
        with connect() as db: db.execute("SELECT 1")
        return {"status":"ok","database":"ok","version":"0.1.0"}
    except sqlite3.Error:
        raise HTTPException(503, "Database unavailable")


@app.get("/api/v1/system/status")
def status():
    return {"product":"RAKSHAM","version":"0.1.0","mode":"synthetic-demo","database":"SQLite","data_source":{"status":"offline","provider":"CelesTrak adapter not configured"},"model":"constant-velocity illustrative model","disclaimer":"Research and education only; not operational flight advice."}


@app.get("/api/v1/objects")
def objects(search: str = "", limit: int = Query(100, ge=1, le=500)):
    return {"items":[o for o in OBJECTS if search.lower() in (o["id"]+o["name"]).lower()][:limit],"total":len(OBJECTS)}


@app.get("/api/v1/objects/{object_id}")
def object_detail(object_id: str):
    for obj in OBJECTS:
        if obj["id"] == object_id: return obj
    raise HTTPException(404, "Object not found")


@app.get("/api/v1/data/status")
def data_status(): return {"provider":"CelesTrak","status":"not configured","records":0,"cached_records":0,"message":"Demo currently uses labelled synthetic fixtures."}


@app.post("/api/v1/data/refresh")
def refresh(): raise HTTPException(503, "No external orbital-data provider is configured; existing demo data is unchanged.")


@app.post("/api/v1/screening/run")
def screening(req: ScreenRequest):
    start = time.perf_counter(); events=[]; samples=req.horizon_hours*60//req.step_minutes
    for i,a in enumerate(OBJECTS):
        for b in OBJECTS[i+1:]:
            best=(float("inf"),0)
            for n in range(samples+1):
                sec=n*req.step_minutes*60; d=separation(a,b,sec)
                if d<best[0]: best=(d,sec)
            # local refinement at 1-second increments around best sample
            low=max(0,best[1]-req.step_minutes*60); high=min(req.horizon_hours*3600,best[1]+req.step_minutes*60)
            for sec in range(low,high+1):
                d=separation(a,b,sec)
                if d<best[0]: best=(d,sec)
            if best[0]<=req.threshold_km:
                event={"id":str(uuid.uuid4()),"object_a":a["id"],"object_b":b["id"],"tca":(NOW+timedelta(seconds=best[1])).isoformat(),"seconds_from_start":best[1],"miss_distance_km":round(best[0],4),"horizon_hours":req.horizon_hours,"step_minutes":req.step_minutes,"simulated":True,"frame":a["frame"],"risk":risk(best[0])}
                events.append(event)
    elapsed=round((time.perf_counter()-start)*1000,2)
    with connect() as db:
        for e in events: db.execute("INSERT INTO events VALUES(?,?,?)",(e["id"],NOW.isoformat(),json.dumps(e)))
    return {"job_id":str(uuid.uuid4()),"status":"complete","events":events,"objects_screened":len(OBJECTS),"pairs_screened":len(OBJECTS)*(len(OBJECTS)-1)//2,"runtime_ms":elapsed,"model":"constant velocity; coarse scan plus 1-second local refinement","limitations":["Synthetic fixture coordinates.","No gravity, perturbations, covariance, or validated collision probability."]}


@app.get("/api/v1/events")
def get_events(limit: int=Query(100,ge=1,le=500)):
    with connect() as db: rows=db.execute("SELECT payload FROM events ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
    return {"items":[json.loads(x[0]) for x in rows],"total":len(rows)}


@app.get("/api/v1/events/{event_id}")
def event_detail(event_id: str):
    with connect() as db: row=db.execute("SELECT payload FROM events WHERE id=?",(event_id,)).fetchone()
    if not row: raise HTTPException(404,"Event not found")
    return json.loads(row[0])


@app.post("/api/v1/simulations")
def simulate(req: ManeuverRequest):
    with connect() as db: row=db.execute("SELECT payload FROM events WHERE id=?",(req.event_id,)).fetchone()
    if not row: raise HTTPException(404,"Run and save a screening event first")
    e=json.loads(row[0]); a=next(o for o in OBJECTS if o["id"]==e["object_a"]); b=next(o for o in OBJECTS if o["id"]==e["object_b"])
    t=max(0,e["seconds_from_start"]); burn=req.burn_lead_minutes*60; dv=req.along_track_delta_v_m_s
    before=separation(a,b,t); after=math.sqrt(sum((position(a,t,dv,burn)[i]-position(b,t)[i])**2 for i in range(3)))
    out={"id":str(uuid.uuid4()),"event_id":e["id"],"created_at":datetime.now(timezone.utc).isoformat(),"delta_v_m_s":dv,"burn_lead_minutes":req.burn_lead_minutes,"baseline_separation_km":round(before,4),"candidate_separation_km":round(after,4),"change_km":round(after-before,4),"improved":after>before,"simulated":True,"model":"instantaneous along-track velocity perturbation in constant-velocity model","limitations":["Illustrative only; no orbital dynamics, propulsion, attitude, constraints, or uncertainty model."]}
    with connect() as db: db.execute("INSERT INTO simulations VALUES(?,?,?)",(out["id"],out["created_at"],json.dumps(out)))
    return out


@app.get("/api/v1/simulations")
def simulations(limit: int=Query(100,ge=1,le=500)):
    with connect() as db: rows=db.execute("SELECT payload FROM simulations ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
    return {"items":[json.loads(x[0]) for x in rows],"total":len(rows)}


@app.get("/api/v1/simulations/{simulation_id}")
def simulation_detail(simulation_id: str):
    with connect() as db: row=db.execute("SELECT payload FROM simulations WHERE id=?",(simulation_id,)).fetchone()
    if not row: raise HTTPException(404,"Simulation not found")
    return json.loads(row[0])


@app.post("/api/v1/simulations/{simulation_id}/compare")
def compare(simulation_id: str, req: ManeuverRequest):
    candidate=simulate(req)
    with connect() as db: row=db.execute("SELECT payload FROM simulations WHERE id=?",(simulation_id,)).fetchone()
    if not row: raise HTTPException(404,"Simulation not found")
    return {"baseline":json.loads(row[0]),"candidate":candidate}


@app.get("/api/v1/analytics/summary")
def analytics():
    ev=get_events(500)["items"]; sims=simulations(500)["items"]
    return {"event_count":len(ev),"simulation_count":len(sims),"risk_counts":{k:sum(1 for e in ev if e["risk"]["priority"]==k) for k in ["CRITICAL","HIGH","GUARDED","LOW","DATA LIMITED"]},"simulated_only":True}


@app.get("/api/v1/reports/events.csv")
def event_csv():
    rows=get_events(500)["items"]; lines=["id,object_a,object_b,tca,miss_distance_km,priority,simulated"]
    lines += [f'{e["id"]},{e["object_a"]},{e["object_b"]},{e["tca"]},{e["miss_distance_km"]},{e["risk"]["priority"]},true' for e in rows]
    return Response("\n".join(lines),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=raksham-events.csv"})


@app.get("/api/v1/reports/simulations.csv")
def simulation_csv():
    rows=simulations(500)["items"]; lines=["id,event_id,delta_v_m_s,baseline_km,candidate_km,change_km,simulated"]
    lines += [f'{s["id"]},{s["event_id"]},{s["delta_v_m_s"]},{s["baseline_separation_km"]},{s["candidate_separation_km"]},{s["change_km"]},true' for s in rows]
    return Response("\n".join(lines),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=raksham-simulations.csv"})


@app.post("/api/v1/explanations")
def explanation(payload: dict):
    return {"generated":False,"provider":"deterministic","text":"This synthetic screening result reports geometric minimum separation only. Its heuristic priority is not a collision probability. Validate current source data, uncertainty, frame, and epoch before drawing conclusions. No maneuver result is flight advice.","evidence_id":payload.get("event_id")}
