from fastapi import FastAPI
from producer import publish_event
from database import init_db, Event, SessionLocal, get_events, get_projections

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

@app.post("/events/")
async def create_event(event: dict):
    async with SessionLocal() as session:
        new_event = Event(event_type=event["event_type"], data=event["data"])
        session.add(new_event)
        await session.commit()

    publish_event(event)
    return {"message": "Event created and published"}

@app.get("/get/events/")
async def read_events():
    events = await get_events()
    return {"events": events}

@app.get("/get/projections/")
async def read_projections():
    projections = await get_projections()
    return {"projections": projections}