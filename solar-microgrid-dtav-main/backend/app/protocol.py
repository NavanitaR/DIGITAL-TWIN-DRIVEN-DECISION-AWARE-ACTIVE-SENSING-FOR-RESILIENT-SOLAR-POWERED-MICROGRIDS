"""Wire v1: little endian, bounded binary packets shared with C firmware."""

import struct
from enum import IntEnum


class Kind(IntEnum):
    HEARTBEAT = 1
    SENSOR_REPORT = 2
    PANEL_REPORT = 3
    FAULT_EVENT = 4
    MEASUREMENT_REQUEST = 5
    MEASUREMENT_RESPONSE = 6
    PANEL_ISOLATION_REQUEST = 7
    ACK = 8
    NACK = 9
    CONFIG_GET = 10
    CONFIG_SET = 11
    CONTROL = 12
    CENTRAL_REPORT = 13


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1) & 0xFFFF
    return crc


def encode(kind: int, seq: int, payload=b"", node=1, timestamp=0) -> bytes:
    if len(payload) > 180:
        raise ValueError("payload too large")
    body = (
        struct.pack("<BBBBHIB", 0xA7, 1, kind, node, seq, timestamp, len(payload))
        + payload
    )
    return body + struct.pack("<H", crc16(body))


def decode(data: bytes):
    if len(data) < 13:
        raise ValueError("short packet")
    magic, ver, kind, node, seq, stamp, n = struct.unpack("<BBBBHIB", data[:11])
    if magic != 0xA7 or ver != 1 or n > 180 or len(data) != 13 + n:
        raise ValueError("header")
    if crc16(data[:-2]) != struct.unpack("<H", data[-2:])[0]:
        raise ValueError("CRC")
    if kind not in Kind._value2member_map_:
        raise ValueError("type")
    return dict(kind=kind, node=node, seq=seq, timestamp=stamp, payload=data[11:-2])


class Stream:
    """UART: COBS packet + zero delimiter. Corruption resyncs at next zero."""

    def __init__(self):
        self.buffer = bytearray()
        self.errors = 0

    def feed(self, data):
        out = []
        for b in data:
            if b:
                if len(self.buffer) < 256:
                    self.buffer.append(b)
                else:
                    self.buffer.clear()
                    self.errors += 1
            elif self.buffer:
                try:
                    out.append(decode(uncobs(bytes(self.buffer))))
                except ValueError:
                    self.errors += 1
                self.buffer.clear()
        return out


def cobs(data):
    out = bytearray([0])
    start = 0
    code = 1
    for b in data:
        if b == 0:
            out[start] = code
            start = len(out)
            out.append(0)
            code = 1
        else:
            out.append(b)
            code += 1
            if code == 255:
                out[start] = code
                start = len(out)
                out.append(0)
                code = 1
    out[start] = code
    return bytes(out) + b"\0"


def uncobs(data):
    out = bytearray()
    i = 0
    while i < len(data):
        n = data[i]
        i += 1
        if n == 0 or i + n - 1 > len(data):
            raise ValueError("COBS")
        out.extend(data[i : i + n - 1])
        i += n - 1
        if n < 255 and i < len(data):
            out.append(0)
    return bytes(out)
