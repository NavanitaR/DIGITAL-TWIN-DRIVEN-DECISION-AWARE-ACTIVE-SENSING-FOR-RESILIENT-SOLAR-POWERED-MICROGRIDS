import math, struct
import pytest
from app.protocol import *
from app.control import Controller
from app.twin import Twin
from app.dtav import decision_value, Sensing
from app.engine import Engine
from app.store import Store
from app.models import Command, Injection


@pytest.mark.parametrize(
    "payload", [b"", bytes(range(180)), b"\0" * 180, b"\xff" * 180]
)
def test_wire_and_fragmentation(payload):
    p = encode(Kind.SENSOR_REPORT, 65535, payload, timestamp=0xFFFFFFFF)
    assert decode(p)["payload"] == payload
    s = Stream()
    output = []
    for b in cobs(p):
        output += s.feed(bytes([b]))
    assert len(output) == 1 and output[0]["payload"] == payload
    bad = bytearray(p)
    bad[-1] ^= 1
    with pytest.raises(ValueError):
        decode(bytes(bad))


def test_stream_recovers():
    s = Stream()
    out = s.feed(b"bad\0" + cobs(encode(1, 1)))
    assert len(out) == 1 and s.errors == 1


def test_break_before_make_and_revalidate():
    c = Controller()
    c.step(0, 10, 3.8, 0.6)
    assert c.source == "off"
    c.step(0.1, 10, 3.8, 0.6)
    assert c.source == "off"
    c.step(0.3, 10, 3.8, 0.6)
    assert c.source == "battery"
    for t in range(1, 32):
        c.step(t, 10, 3.8, 0.6)
        assert not (c.source == "solar" and c.source == "battery")
    assert c.source == "solar"
    c.step(32, 0, 3.2, 0.05)
    assert c.source == "off" and not any(c.loads)
    c.step(33, 0, 3.2, 0.05)
    assert c.source == "off"


def test_invalid_and_low_battery():
    c = Controller(source="battery", loads=[True] * 3)
    c.step(100, 0, float("nan"), 0.1)
    assert c.state == "FAULT" and not any(c.loads)
    c.step(101, 0, 3.2, 0.02)
    assert c.source == "off"
    with pytest.raises(ValueError):
        c.command(Command(kind="source", value=2, confirmed=True), 0, 3.2, 0.02)


def test_shedding_and_staggered_restore():
    c = Controller(source="battery", loads=[True] * 3)
    c.step(0, 0, 3.7, 0.2)
    assert c.loads == [True, True, False]
    c.step(1, 0, 3.5, 0.1)
    assert c.loads == [True, False, False]
    c.step(3, 0, 3.8, 0.6)
    assert c.loads == [True, True, False]
    c.step(4, 0, 3.8, 0.6)
    assert c.loads == [True, True, False]
    c.step(5, 0, 3.8, 0.6)
    assert c.loads == [True] * 3


def test_battery_energy_and_load_priority_surplus_charging():
    t = Twin(isolated=[False] * 4)
    c = Controller(source="battery", loads=[True] * 3)
    old = t.soc
    s = t.step(1, c)
    assert s["battery_a"] > 0 and t.soc < old
    expected = old - s["battery_a"] / (3600 * 5)
    assert t.soc == pytest.approx(expected)
    c.source = "solar"
    s = t.step(1, c)
    assert s["charge_w"] > 0 and s["battery_a"] < 0
    assert s["pv_surplus_w"] == pytest.approx(max(0, s["solar_w"] - 6 / 0.88))
    assert s["charge_w"] / 0.9 + 6 / 0.88 <= s["solar_w"] + 1e-6


def test_dtav_value_depends_on_action_ambiguity():
    certain = decision_value(12, 0.01)
    ambiguous = decision_value(4.5, 2, cost=0.001)
    assert not certain["request"]
    assert ambiguous["request"]
    assert ambiguous["evsi"] > certain["evsi"]
    assert not decision_value(4.5, 2, cost=100)["request"]


def test_mppt_receives_only_surplus_and_can_run_with_solar_loads():
    t = Twin(isolated=[False] * 4)
    c = Controller(source="solar", loads=[True] * 3)
    s = t.step(1, c)
    assert s["load_w"] == 6 and s["charge_w"] > 0
    t.shade = [0.05] * 4
    low = t.step(1, c)
    assert low["charge_w"] == 0


def test_real_charge_supervisor_packet_is_not_synthetic():
    e = Engine(Store(":memory:"))
    e.switch("hardware", "dtav")
    e.ingest(decode(encode(Kind.PANEL_REPORT, 1, struct.pack("<fB", 5.6, 1), node=2)))
    assert e.state["pv_bus_v"] == pytest.approx(5.6) and e.state["charge_inhibited"]


def test_baseline_counts():
    counts = {}
    for name in ("continuous", "periodic", "event", "dtav"):
        s = Sensing(name)
        for t in range(120):
            s.step(t, 10)
        counts[name] = s.reports
    assert counts["continuous"] == 120
    assert counts["periodic"] == 4
    assert all(counts[x] < 120 for x in ("periodic", "event", "dtav"))


def test_end_to_end_fault_recovery_and_replay_barrier():
    e = Engine(Store(":memory:"))
    for _ in range(40):
        e.tick()
    result = e.command(Command(kind="panel", target=0, value=1, confirmed=True))
    assert "acknowledged" in result["status"] and e.twin.isolated[0]
    assert e.chain.down and e.chain.up
    e.inject(Injection(kind="reverse", panel=1))
    assert e.twin.isolated[1]
    with pytest.raises(ValueError):
        e.command(Command(kind="panel", target=1, value=0, confirmed=True))
    e.inject(Injection(kind="lora_loss"))
    before = e.chain.dropped
    e.tick()
    e.chain.transfer(5, down=True)
    assert e.chain.dropped > before
    e.inject(Injection(kind="restore"))
    assert e.chain.lora
    e.switch("replay", "dtav")
    e.tick()
    assert e.state["provenance"] == "replayed"
    with pytest.raises(ValueError):
        e.command(Command(kind="measure"))
    e.switch("hardware", "dtav")
    e.tick()
    assert "solar_w" not in e.state and e.state["stale"]
    with pytest.raises(ValueError):
        e.command(Command(kind="measure"))


def test_store_and_real_packet_ingest():
    st = Store(":memory:")
    e = Engine(st)
    e.switch("hardware", "dtav")
    raw = struct.pack(
        "<15f4B",
        3.8,
        0.2,
        0.6,
        12,
        5,
        1,
        1,
        0,
        0,
        12,
        12,
        12,
        1 / 12,
        0,
        0,
        2,
        1,
        3,
        127,
    )
    e.ingest(decode(encode(Kind.CENTRAL_REPORT, 1, raw, node=2)))
    e.tick()
    assert e.state["battery_v"] == pytest.approx(3.8) and not e.state["stale"]
    assert len(st.history()) == 1
    assert e.state["load_voltages"] == [12, 12, 12]


def test_communication_loss_does_not_refresh_estimator():
    s = Sensing("continuous")
    s.step(0, 8)
    _, r = s.step(1, 1, available=False)
    assert r["estimate"] == 8 and r["age_s"] == 1 and not r["delivered"]


def test_supervisory_request_cannot_override_critical_safety():
    c = Controller(source="battery", loads=[True] * 3, service_budget=0)
    c.step(1, 15, 3.8, 0.6)
    assert c.loads == [True, False, False]
    c.step(2, 0, 3.2, 0.01)
    assert not any(c.loads)


def test_no_actuation_across_disconnected_chain():
    e = Engine(Store(":memory:"))
    e.chain.lora = False
    with pytest.raises(ValueError):
        e.command(Command(kind="panel", target=0, value=1, confirmed=True))
    assert not e.twin.isolated[0]


def test_hardware_mode_discards_preexisting_queue():
    import queue, time

    class Bridge:
        def __init__(self):
            self.queue = queue.Queue()
            self.connected = False

    b = Bridge()
    e = Engine(Store(":memory:"), b)
    b.queue.put(({"kind": 1}, time.monotonic()))
    e.switch("hardware", "dtav")
    assert b.queue.empty()
    e.tick()
    assert e.state["stale"]


def test_prioritised_candidate_action_is_logged_and_constrained():
    e = Engine(Store(":memory:"))
    e.twin.shade = [0.1] * 4
    for _ in range(45):
        e.tick()
    assert any(ev["type"] == "supervisory_decision" for ev in e.store.events())
    assert e.controller.service_budget in (0, 1, 4, 6)
    assert e.state["load_w"] <= 6


def test_api(monkeypatch):
    import app.main as main
    from fastapi.testclient import TestClient

    monkeypatch.setattr(main, "store", Store(":memory:"))
    monkeypatch.setattr(main, "engine", Engine(main.store))
    main.engine.tick()
    client = TestClient(main.app)
    assert client.get("/api/state").status_code == 200
    assert client.post("/api/command", json={"kind": "nonsense"}).status_code == 422
    assert (
        client.post("/api/command", json={"kind": "source", "value": 1}).status_code
        == 409
    )
    assert (
        client.post(
            "/api/settings", json={"mode": "replay", "strategy": "dtav"}
        ).status_code
        == 200
    )
    assert client.post("/api/inject", json={"kind": "reverse"}).status_code == 409
    assert "text/csv" in client.get("/api/export.csv").headers["content-type"]
