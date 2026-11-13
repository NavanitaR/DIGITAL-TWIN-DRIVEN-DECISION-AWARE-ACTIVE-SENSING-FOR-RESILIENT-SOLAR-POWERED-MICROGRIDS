from app.engine import Engine
from app.store import Store
from fastapi.testclient import TestClient


def test_websocket_provenance(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main, "engine", Engine(Store(":memory:")))
    main.engine.tick()
    with TestClient(main.app).websocket_connect("/ws") as ws:
        sample = ws.receive_json()
        assert sample["mode"] == "simulation" and sample["provenance"] == "simulated"
