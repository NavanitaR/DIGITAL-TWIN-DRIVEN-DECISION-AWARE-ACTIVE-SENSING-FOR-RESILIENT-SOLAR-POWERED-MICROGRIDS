from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    kind: Literal["load", "source", "panel", "measure", "auto"]
    target: int = Field(default=0, ge=0, le=3)
    value: int = Field(default=0, ge=0, le=2)
    confirmed: bool = False


class Settings(BaseModel):
    mode: Literal["simulation", "hardware", "replay"] = "simulation"
    strategy: Literal["continuous", "periodic", "event", "dtav"] = "dtav"


class Injection(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    kind: Literal["shade", "disconnect", "reverse", "lora_loss", "restore"]
    panel: int = Field(default=0, ge=0, le=3)
    severity: float = Field(default=0.8, ge=0, le=1)
