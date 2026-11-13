import struct
import time
import queue
import os
from .twin import Twin
from .control import Controller
from .dtav import Sensing, decision_value
from .transport import Chain
from .protocol import Kind, encode
from .models import Command


class Engine:
    def __init__(self, store, mqtt=None):
        self.store = store
        self.mqtt = mqtt
        self.mode = "simulation"
        self.strategy = "dtav"
        self.generation = 0
        self.reset()

    def reset(self):
        self.twin = Twin(isolated=[False] * 4)
        self.controller = Controller()
        self.sensing = Sensing(self.strategy)
        self.chain = Chain()
        self.state = {}
        self.replay = []
        self.index = 0
        self.last_hardware = 0.0
        self.pending = {}
        self.seq = 0
        self.central_seq = None
        self.sensor_seq = None
        self.hardware_sensor_time = 0
        self.hardware_request_at = -100.0
        self.hardware_action = None
        self.previous_source = None
        self.previous_faults = None

    def switch(self, mode, strategy):
        replay = self.store.history(10000) if mode == "replay" else []
        self.mode = mode
        self.strategy = strategy
        self.generation += 1
        self.reset()
        self.replay = replay
        if self.mqtt:
            while True:
                try:
                    self.mqtt.queue.get_nowait()
                except queue.Empty:
                    break

    def tick(self, dt=1):
        if self.mode == "simulation":
            t = self.twin.t
            solar = sum(self.twin.solar(t)) * 0.88
            report, research = self.sensing.step(
                t, solar, available=self.chain.lora and self.chain.gateway
            )
            if report:
                if research["request"] and self.strategy == "dtav":
                    self.chain.transfer(Kind.MEASUREMENT_REQUEST, b"\0", True)
                panel = self.twin.solar(t)
                fields = []
                for i in (0, 2):
                    fields.extend(
                        [
                            28.0,
                            55.0,
                            6.0,
                            sum(panel[i : i + 2]) / 6,
                            sum(panel[i : i + 2]),
                            max(panel[i : i + 2]) / 5,
                        ]
                    )
                fields.extend(panel + [panel[0] / 6, panel[1] / 6])
                raw = struct.pack(
                    "<18f4B",
                    *fields,
                    sum(int(x) << i for i, x in enumerate(self.twin.isolated)),
                    63,
                    0,
                    self.chain.seq % 256,
                )
                self.chain.transfer(
                    Kind.MEASUREMENT_RESPONSE
                    if research["request"] and self.strategy == "dtav"
                    else Kind.SENSOR_REPORT,
                    raw,
                )
            # Reevaluate the candidate after observation. A safety-limited service
            # request travels down the chain; the local controller can still shed it.
            target = research["action_after"]
            if (
                target != self.controller.service_budget
                or t - self.controller.service_at >= 15
            ) and self.chain.gateway:
                result = self.chain.transfer(
                    Kind.CONTROL, bytes([6, int(target), 0, 1]), True
                )
                if result:
                    self.controller.service_budget = target
                    self.controller.service_at = t
                    self.chain.transfer(Kind.ACK, b"\0\0\0")
                    research["approved_service_w"] = target
                    self.store.event(
                        {
                            "time": t,
                            "type": "supervisory_decision",
                            "requested_w": target,
                            "strategy": self.strategy,
                            "safety": "local source/battery/priority checks remain authoritative",
                        }
                    )
            self.controller.step(t, solar, self.twin.voltage, self.twin.soc)
            self.state = self.twin.step(dt, self.controller)
            self.state["research"] = research
            self.state["connectivity"] = {
                "lora": self.chain.lora,
                "gateway": self.chain.gateway,
                "mqtt": True,
                "controller": True,
                "up": self.chain.up,
                "down": self.chain.down,
                "dropped": self.chain.dropped,
            }
            self.state["chain"] = list(self.chain.trace)[-8:]
        elif self.mode == "replay":
            if self.replay:
                self.state = dict(self.replay[self.index % len(self.replay)])
                self.index += 1
                self.state["provenance"] = "replayed"
        else:
            # Empty/unknown fields remain absent until actual packets arrive.
            if self.mqtt:
                for _ in range(128):
                    try:
                        packet, received = self.mqtt.queue.get_nowait()
                        if time.monotonic() - received <= 5:
                            self.ingest(packet, received)
                    except queue.Empty:
                        break
            self.state["provenance"] = "measured"
            self.state["stale"] = time.monotonic() - self.last_hardware > 5
            self.state["connectivity"] = {
                "mqtt": bool(self.mqtt and self.mqtt.connected),
                "controller": not self.state["stale"],
                "gateway": bool(self.mqtt and self.mqtt.connected),
                "lora": time.time() - self.state.get("sensor_received", 0) < 180,
            }
            for seq, item in list(self.pending.items()):
                if time.monotonic() - item["at"] > 65:
                    self.store.event(
                        {"time": time.time(), "type": "command_timeout", "seq": seq}
                    )
                    del self.pending[seq]
            try:
                self.hardware_dtav()
            except ValueError as exc:
                self.state["research_error"] = str(exc)
        self.state["mode"] = self.mode
        self.state["generation"] = self.generation
        source = self.state.get("source")
        faults = self.state.get("faults")
        if source != self.previous_source and source is not None:
            self.store.event(
                {
                    "time": self.state.get("time", time.time()),
                    "type": "source_transition",
                    "from": self.previous_source,
                    "to": source,
                    "mode": self.mode,
                }
            )
            self.previous_source = source
        if faults != self.previous_faults and faults is not None:
            self.store.event(
                {
                    "time": self.state.get("time", time.time()),
                    "type": "fault_transition",
                    "faults": faults,
                    "mode": self.mode,
                }
            )
            self.previous_faults = faults
        if self.state and self.mode != "replay":
            self.store.sample(self.mode, self.state)
        return self.state

    def hardware_dtav(self):
        if (
            self.strategy != "dtav"
            or self.state.get("stale", True)
            or self.state.get("solar_w") is None
            or not self.mqtt
            or not self.mqtt.connected
        ):
            return
        now = time.monotonic()
        received = self.state.get("sensor_received", 0)
        if received != self.hardware_sensor_time:
            self.hardware_sensor_time = received
            self.sensing.mean = self.state["solar_w"] * 0.88
            self.sensing.last = now
            self.sensing.reports += 1
        age = now - self.sensing.last
        result = decision_value(self.sensing.mean, 0.2 + 0.12 * age)
        result.update(
            estimate=self.sensing.mean,
            age_s=age,
            reports=self.sensing.reports,
            requests=self.sensing.requests,
            communication_savings=None,
            model_error_w=None,
            armed=os.getenv("MICROGRID_DTAV_ARMED") == "1",
        )
        if (
            result["request"]
            and now - self.hardware_request_at >= 15
            and not self.pending
        ):
            self.command(Command(kind="measure", confirmed=True))
            self.hardware_request_at = now
            self.sensing.requests += 1
        # After a genuinely new observation, optional automatic service requests
        # require explicit local commissioning configuration. No source forcing.
        if (
            result["armed"]
            and age < 2
            and self.state.get("source") == "solar"
            and result["action"] != self.hardware_action
            and not self.pending
        ):
            self.seq = (self.seq + 1) & 65535
            self.mqtt.send(
                encode(
                    Kind.CONTROL,
                    self.seq,
                    bytes([6, int(result["action"]), 0, 1]),
                    node=9,
                )
            )
            self.pending[self.seq] = {
                "command": {"kind": "dtav_service", "watts": result["action"]},
                "at": now,
            }
            self.hardware_action = result["action"]
            self.store.event(
                {
                    "time": time.time(),
                    "type": "dtav_approved_command",
                    "service_w": result["action"],
                }
            )
        self.state["research"] = result

    def ingest(self, p, received=None):
        payload = p["payload"]
        now = received if received is not None else time.monotonic()
        if p["kind"] == Kind.PANEL_REPORT and p["node"] == 2 and len(payload) == 5:
            import math

            pv, inhibited = struct.unpack("<fB", payload)
            self.state.update(
                pv_bus_v=pv if math.isfinite(pv) else None,
                charge_inhibited=bool(inhibited),
                allocation="Shared PV: loads first, MPPT surplus",
            )
        if p["kind"] in (Kind.ACK, Kind.NACK) and len(payload) >= 3:
            seq, status = struct.unpack("<HB", payload[:3])
            request = self.pending.pop(seq, None)
            self.store.event(
                {
                    "time": time.time(),
                    "type": "command_result",
                    "seq": seq,
                    "status": status,
                    "request": request,
                }
            )
        if p["kind"] == Kind.MEASUREMENT_RESPONSE:
            request = self.pending.pop(p["seq"], None)
            if request:
                self.store.event(
                    {
                        "time": time.time(),
                        "type": "measurement_completed",
                        "seq": p["seq"],
                    }
                )
        if p["kind"] == Kind.CENTRAL_REPORT and len(payload) == 64:
            if self.central_seq == p["seq"]:
                return
            self.central_seq = p["seq"]
            values = struct.unpack("<15f4B", payload)
            v, amps, soc, bus, solar, load, l1, l2, l3 = values[:9]
            source, mask, state, health = values[15:]
            import math

            if not all(math.isfinite(x) for x in values[:15]) or not 0 <= soc <= 1:
                return
            self.state.update(
                battery_v=v,
                battery_a=amps,
                soc=soc,
                bus_v=bus,
                solar_capacity_w=solar,
                load_w=load,
                load_powers=[l1, l2, l3],
                load_voltages=list(values[9:12]),
                load_currents=list(values[12:15]),
                source=["off", "solar", "battery"][min(source, 2)],
                loads=[bool(mask & (1 << i)) for i in range(3)],
                state=str(state),
                health=health,
                device_ms=p["timestamp"],
            )
            self.last_hardware = now
        if (
            p["kind"] in (Kind.SENSOR_REPORT, Kind.MEASUREMENT_RESPONSE)
            and len(payload) == 76
        ):
            values = struct.unpack("<18f4B", payload)
            import math

            def valid(x):
                return x if math.isfinite(x) else None

            self.state.update(
                pv=[valid(x) for x in values[12:16]],
                isolated=[bool(values[18] & (1 << i)) for i in range(4)],
                sensor_health=values[19],
                sensor_received=time.time(),
                lora_rssi=None,
                clusters=[
                    dict(
                        zip(
                            (
                                "temperature",
                                "humidity",
                                "voltage",
                                "current",
                                "power",
                                "light",
                            ),
                            [valid(x) for x in values[i : i + 6]],
                        )
                    )
                    for i in (0, 6)
                ],
            )
            self.state["solar_w"] = (
                sum(values[12:16])
                if all(math.isfinite(x) for x in values[12:16])
                else None
            )
            self.state["faults"] = [
                {
                    "panel": i,
                    "type": "panel_condition (cause requires local diagnosis)",
                    "isolated": bool(values[18] & (1 << i)),
                }
                for i in range(4)
                if values[20] & (1 << i)
            ]
            self.state["connectivity"] = {"lora": True}

    def command(self, c):
        if self.mode == "replay":
            raise ValueError("replay is read-only")
        if self.mode == "hardware":
            if not self.state or self.state.get("stale", True):
                raise ValueError("controller measurements stale")
            if c.kind != "measure" and not c.confirmed:
                raise ValueError("confirmation required")
            if not self.mqtt:
                raise ValueError("MQTT unavailable")
            self.seq = (self.seq + 1) & 65535
            payload = bytes(
                [
                    {"load": 1, "source": 2, "panel": 3, "measure": 4, "auto": 5}[
                        c.kind
                    ],
                    c.target,
                    c.value,
                    int(c.confirmed),
                ]
            )
            if len(self.pending) >= 8:
                raise ValueError("command queue full")
            self.mqtt.send(encode(Kind.CONTROL, self.seq, payload, node=9, timestamp=0))
            self.pending[self.seq] = {"command": c.model_dump(), "at": time.monotonic()}
            return {"status": "pending", "sequence": self.seq}
        kind = (
            Kind.MEASUREMENT_REQUEST
            if c.kind == "measure"
            else Kind.PANEL_ISOLATION_REQUEST
            if c.kind == "panel"
            else Kind.CONTROL
        )
        if self.chain.transfer(kind, bytes([c.target, c.value]), True) is None:
            raise ValueError("communication unavailable")
        self.controller.command(
            c,
            sum(self.twin.solar(self.twin.t)) * 0.88,
            self.twin.voltage,
            self.twin.soc,
        )
        if c.kind == "panel":
            if c.value > 1:
                raise ValueError("invalid panel state")
            if not c.value and self.twin.fault[c.target] not in ("none", "shade"):
                raise ValueError("latched fault requires inspection")
            self.twin.isolated[c.target] = bool(c.value)
        self.chain.transfer(Kind.ACK, b"\0\0\0")
        self.store.event(
            {
                "time": self.twin.t,
                "type": "command",
                "command": c.model_dump(),
                "response": "acknowledged",
            }
        )
        return {"status": "acknowledged (simulation)"}

    def inject(self, c):
        if self.mode != "simulation":
            raise ValueError("fault injection requires simulation")
        if c.kind == "lora_loss":
            self.chain.lora = False
        elif c.kind == "restore":
            self.chain.lora = True
            self.twin.shade[c.panel] = 1
            if self.twin.fault[c.panel] == "shade":
                self.twin.fault[c.panel] = "none"
        elif c.kind == "shade":
            self.twin.shade[c.panel] = 1 - c.severity
            self.twin.fault[c.panel] = "shade"
        else:
            self.twin.shade[c.panel] = 0
            self.twin.isolated[c.panel] = True
            self.twin.fault[c.panel] = c.kind
        self.store.event(
            {"time": self.twin.t, "type": "fault", "injection": c.model_dump()}
        )
