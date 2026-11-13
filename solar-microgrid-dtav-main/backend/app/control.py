"""Deterministic supervisory policy. Embedded controller remains authoritative."""

from dataclasses import dataclass, field
import math


@dataclass
class Controller:
    source: str = "off"
    loads: list[bool] = field(default_factory=lambda: [False] * 3)
    pending: str = "off"
    transfer_at: float = -100
    last_switch: float = -100
    restore_at: float = -100
    solar_since: float | None = None
    state: str = "INIT"
    manual_source: str | None = None
    manual_loads: dict = field(default_factory=dict)
    service_budget: float = 6.0
    service_at: float = 0.0

    def step(self, t, solar_w, battery_v, soc, valid=True):
        if t - self.service_at > 30:
            self.service_budget = 6.0
        if (
            not valid
            or not all(math.isfinite(x) for x in (solar_w, battery_v, soc))
            or not 2.5 <= battery_v <= 4.30
            or not 0 <= soc <= 1
        ):
            self.source = "off"
            self.pending = "off"
            self.loads = [False] * 3
            self.state = "FAULT"
            return
        if solar_w >= 7.5:
            if self.solar_since is None:
                self.solar_since = t
        else:
            self.solar_since = None
        bat_ok = battery_v >= 3.35 and soc > 0.08
        solar_ok = solar_w >= 2
        desired = "battery" if bat_ok else "off"
        if self.solar_since is not None and t - self.solar_since >= 10:
            desired = "solar"
        if (
            self.source == "solar"
            and solar_w >= sum(p for p, on in zip((1, 3, 2), self.loads) if on) + 0.5
        ):
            desired = "solar"
        if self.manual_source == "solar" and solar_ok:
            desired = "solar"
        if self.manual_source == "battery" and bat_ok:
            desired = "battery"
        if self.manual_source == "off":
            desired = "off"
        emergency = (self.source == "solar" and not solar_ok) or (
            self.source == "battery" and not bat_ok
        )
        if self.pending != "off":
            # Revalidate target after dead time; never close onto an unavailable source.
            ready = (self.pending == "solar" and solar_ok) or (
                self.pending == "battery" and bat_ok
            )
            if not ready:
                self.pending = "off"
            elif t - self.transfer_at >= 0.25:
                self.source = self.pending
                self.pending = "off"
                self.last_switch = t
        elif desired != self.source and (
            emergency or desired == "off" or t - self.last_switch >= 15
        ):
            self.source = "off"
            self.loads = [False] * 3
            self.pending = desired
            self.transfer_at = t
        budget = (
            solar_w - 0.5
            if self.source == "solar"
            else (6 if soc > 0.25 else 4 if soc > 0.12 else 1.2)
            if self.source == "battery"
            else 0
        )
        # Host service requests can reduce optional loads; critical service remains local.
        budget = min(budget, max(1.0, self.service_budget))
        # Reduce lower priorities before restoring higher priorities one at a time.
        for i in (2, 1, 0):
            if (
                sum(p for p, on in zip((1, 3, 2), self.loads) if on) > budget
                or self.manual_loads.get(i) is False
            ):
                self.loads[i] = False
        if t - self.restore_at >= 2:
            for i, p in enumerate((1, 3, 2)):
                if (
                    not self.loads[i]
                    and self.manual_loads.get(i) is not False
                    and sum(q for q, on in zip((1, 3, 2), self.loads) if on) + p
                    <= budget
                ):
                    self.loads[i] = True
                    self.restore_at = t
                    break
        self.state = (
            "RECOVERY"
            if self.pending != "off"
            else "SAFE_SHUTDOWN"
            if self.source == "off"
            else "LOAD_SHEDDING"
            if not all(self.loads)
            else self.source.upper() + "_ACTIVE"
        )

    def command(self, c, solar_w, battery_v, soc):
        if c.kind == "auto":
            self.manual_source = None
            self.manual_loads.clear()
            return
        if c.kind == "measure":
            return
        if not c.confirmed:
            raise ValueError("explicit confirmation required")
        if c.kind == "source":
            target = ("off", "solar", "battery")[c.value]
            if target == "solar" and solar_w < 7.5:
                raise ValueError("solar power unavailable")
            if target == "battery" and (battery_v < 3.35 or soc <= 0.08):
                raise ValueError("battery unavailable")
            self.manual_source = target
        elif c.kind == "load":
            if c.target > 2 or c.value > 1:
                raise ValueError("invalid load")
            if c.value and (
                self.source == "off" or (self.source == "battery" and soc <= 0.12)
            ):
                raise ValueError("insufficient reserve")
            self.manual_loads[c.target] = bool(c.value)
