"""Each simulated hop validates the same v1 wire format as real devices."""

from collections import deque
from .protocol import encode, decode, cobs, Stream, Kind


class Chain:
    def __init__(self):
        self.up = 0
        self.down = 0
        self.dropped = 0
        self.lora = True
        self.gateway = True
        self.seq = 0
        self.trace = deque(maxlen=100)

    def transfer(self, kind, payload=b"", down=False):
        self.seq = (self.seq + 1) & 65535
        packet = encode(kind, self.seq, payload)
        if not self.gateway or (not self.lora and kind in (2, 3, 4, 5, 6, 7)):
            self.dropped += 1
            return None
        # UART stream deliberately fragmented to exercise framing.
        serial = Stream()
        wire = cobs(packet)
        decoded = serial.feed(wire[:5]) + serial.feed(wire[5:])
        if not decoded:
            raise RuntimeError("UART frame lost")
        result = decode(packet)
        self.down += int(down)
        self.up += int(not down)
        self.trace.append(
            {
                "seq": self.seq,
                "kind": int(kind),
                "direction": "down" if down else "up",
                "hops": ["MQTT", "C3", "UART", "STM32", "LoRa", "S3"]
                if down
                else ["S3", "LoRa", "STM32", "UART", "C3", "MQTT"],
            }
        )
        return result
