import os
import time
import queue
import paho.mqtt.client as mqtt
from .protocol import decode


class MqttBridge:
    def __init__(self):
        self.queue = queue.Queue(maxsize=256)
        self.connected = False
        self.last = 0
        self.errors = 0
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id="microgrid-host"
        )
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = lambda *args: setattr(self, "connected", False)
        self.client.on_message = self.on_message
        if os.getenv("MQTT_USERNAME"):
            self.client.username_pw_set(
                os.environ["MQTT_USERNAME"], os.getenv("MQTT_PASSWORD")
            )

    def on_connect(self, client, userdata, flags, reason, properties):
        self.connected = not reason.is_failure
        if self.connected:
            client.subscribe("microgrid/v1/up", qos=1)

    def on_message(self, client, userdata, msg):
        try:
            packet = decode(msg.payload)
            self.last = time.monotonic()
            self.queue.put_nowait((packet, self.last))
        except (ValueError, queue.Full):
            self.errors += 1

    def start(self):
        self.client.connect_async(
            os.getenv("MQTT_HOST", "localhost"), int(os.getenv("MQTT_PORT", "1883")), 30
        )
        self.client.loop_start()

    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()

    def send(self, packet):
        if not self.connected:
            raise ValueError("MQTT disconnected")
        result = self.client.publish("microgrid/v1/down", packet, qos=1, retain=False)
        if result.rc:
            raise ValueError("MQTT publish rejected")
