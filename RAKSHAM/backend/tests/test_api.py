from fastapi.testclient import TestClient
from app.main import app, separation, OBJECTS, risk

client=TestClient(app)

def test_health_and_objects():
    assert client.get('/health').json()['status']=='ok'
    assert len(client.get('/api/v1/objects').json()['items'])==3

def test_screening_computes_close_approach_and_persists():
    response=client.post('/api/v1/screening/run',json={'horizon_hours':3,'step_minutes':5,'threshold_km':25})
    assert response.status_code==200
    body=response.json(); assert body['objects_screened']==3
    assert body['events'] and all(e['simulated'] for e in body['events'])
    assert client.get('/api/v1/events').json()['total']>=len(body['events'])

def test_screening_bounds_and_maneuver():
    assert client.post('/api/v1/screening/run',json={'horizon_hours':100}).status_code==422
    event=client.get('/api/v1/events').json()['items'][0]
    sim=client.post('/api/v1/simulations',json={'event_id':event['id'],'along_track_delta_v_m_s':2,'burn_lead_minutes':30})
    assert sim.status_code==200 and sim.json()['simulated']

def test_math_and_priority():
    assert separation(OBJECTS[0],OBJECTS[0],0)==0
    assert risk(0)['priority']=='CRITICAL'
