import asyncio
import csv
import io
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .models import Command, Settings, Injection
from .store import Store
from .mqtt import MqttBridge
from .engine import Engine

store = Store(os.getenv("MICROGRID_DB", "microgrid.db"))
mqtt = MqttBridge()
engine = Engine(store, mqtt)


@asynccontextmanager
async def lifespan(app):
    mqtt.start()

    async def run():
        while True:
            engine.tick()
            await asyncio.sleep(1)

    task = asyncio.create_task(run())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    mqtt.stop()


app = FastAPI(title="Solar Microgrid DTAV", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/state")
def state():
    return engine.state


@app.get("/api/history")
def history():
    return store.history()


@app.get("/api/events")
def events():
    return store.events()


@app.post("/api/command")
def command(c: Command):
    try:
        return engine.command(c)
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.post("/api/settings")
def settings(c: Settings):
    engine.switch(c.mode, c.strategy)
    return {"mode": engine.mode, "strategy": engine.strategy}


@app.post("/api/inject")
def inject(c: Injection):
    try:
        engine.inject(c)
        return {"status": "applied to simulation"}
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.get("/api/export.csv")
def export():
    buf = io.StringIO()
    w = csv.DictWriter(
        buf,
        fieldnames=[
            "mode",
            "provenance",
            "time",
            "solar_w",
            "load_w",
            "soc",
            "battery_v",
            "source",
            "unserved_wh",
        ],
        extrasaction="ignore",
    )
    w.writeheader()
    w.writerows(store.history(10000))
    return Response(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=microgrid.csv"},
    )


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(engine.state)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
