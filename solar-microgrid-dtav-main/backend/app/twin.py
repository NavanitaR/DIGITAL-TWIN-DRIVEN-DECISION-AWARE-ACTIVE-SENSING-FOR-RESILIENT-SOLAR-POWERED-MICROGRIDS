from dataclasses import dataclass, field
import math


@dataclass
class Twin:
    soc: float = 0.65
    capacity_ah: float = 5
    shade: list[float] = field(default_factory=lambda: [1.0] * 4)
    isolated: list[bool] = field(default_factory=lambda: [True] * 4)
    fault: list[str] = field(default_factory=lambda: ["none"] * 4)
    unserved_wh: float = 0
    t: float = 0

    @property
    def voltage(self):
        return 3.3 + 0.9 * self.soc

    def solar(self, t):
        irradiance = max(0, min(1, 0.7 + 0.25 * math.sin(t / 60)))
        return [
            5 * irradiance * self.shade[i] * (not self.isolated[i]) for i in range(4)
        ]

    def step(self, dt, control):
        self.t += dt
        panels = self.solar(self.t)
        pv = sum(panels)
        load = sum(p for p, on in zip((1, 3, 2), control.loads) if on)
        # Rev2 common protected PV bus. Existing MPPT DPM backs off charging
        # demand after direct loads; no fixed panel partition is imposed.
        solar_load = pv * 0.88 if control.source == "solar" else 0
        direct_input = load / 0.88 if control.source == "solar" else 0.0
        surplus = max(0, pv - direct_input)
        charge = (
            min(surplus * 0.90, self.voltage * 0.5)
            if self.soc < 0.98 and control.pending == "off"
            else 0
        )
        discharge = load / 0.85 if control.source == "battery" else 0
        current = (discharge - charge) / self.voltage
        self.soc = max(0, min(1, self.soc - current * dt / (3600 * self.capacity_ah)))
        self.unserved_wh += (6 - load) * dt / 3600
        loss = max(0, pv - charge - (load if control.source == "solar" else 0)) + (
            discharge - load if control.source == "battery" else 0
        )
        return dict(
            time=self.t,
            provenance="simulated",
            pv=panels,
            solar_w=pv,
            solar_available_w=pv * 0.88,
            clusters=[
                {
                    "voltage": 6 if sum(panels[i : i + 2]) else 0,
                    "current": sum(panels[i : i + 2]) / 6,
                    "power": sum(panels[i : i + 2]),
                    "temperature": 28 + 2 * math.sin(self.t / 80),
                    "humidity": 55.0,
                    "light": max(panels[i : i + 2]) / 5,
                }
                for i in (0, 2)
            ],
            battery_v=self.voltage,
            battery_a=current,
            soc=self.soc,
            load_w=load,
            load_powers=[p if on else 0 for p, on in zip((1, 3, 2), control.loads)],
            load_voltages=[12.0 if control.source != "off" else 0.0] * 3,
            load_currents=[
                p / 12 if on else 0 for p, on in zip((1, 3, 2), control.loads)
            ],
            bus_v=12 if control.source != "off" else 0,
            source=control.source,
            state=control.state,
            loads=control.loads[:],
            isolated=self.isolated[:],
            faults=[
                {"panel": i, "type": f, "isolated": self.isolated[i]}
                for i, f in enumerate(self.fault)
                if f != "none"
            ],
            charge_w=charge,
            loss_w=max(0, loss),
            runtime_h=self.soc * self.capacity_ah * self.voltage * 0.85 / load
            if load
            else None,
            unserved_wh=self.unserved_wh,
            relay={
                "solar": control.source == "solar",
                "battery": control.source == "battery",
            },
            allocation="Shared PV: loads first, MPPT surplus",
            pv_surplus_w=surplus,
            charge_inhibited=control.pending != "off",
        )
