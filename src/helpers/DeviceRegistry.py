import json
import logging
import time

from fastapi import WebSocket

log = logging.getLogger(__name__)


class DeviceConnection:
    def __init__(self, ws: WebSocket, client_ip: str):
        self.ws = ws
        self.client_ip = client_ip
        self.connected_at = time.time()
        self.info: dict = {}

    def __repr__(self) -> str:
        name = self.info.get("hostname", self.client_ip)
        hw = self.info.get("hw_type", "?")
        return f"<Device {name} ({hw}) @ {self.client_ip}>"


class DeviceRegistry:
    def __init__(self):
        self._devices: dict[WebSocket, DeviceConnection] = {}

    def register(self, ws: WebSocket, client_ip: str) -> DeviceConnection:
        dev = DeviceConnection(ws, client_ip)
        self._devices[ws] = dev
        return dev

    def unregister(self, ws: WebSocket) -> None:
        self._devices.pop(ws, None)

    def all(self) -> list[DeviceConnection]:
        return list(self._devices.values())

    def __len__(self) -> int:
        return len(self._devices)

    def __bool__(self) -> bool:
        return bool(self._devices)

    async def broadcast(self, message: dict) -> int:
        text = json.dumps(message)
        ok = 0
        for dev in self.all():
            try:
                await dev.ws.send_text(text)
                ok += 1
            except Exception as e:
                log.warning(f"Failed to send to {dev}: {e}")
        return ok

    async def send_to_ip(self, ip: str, message: dict) -> bool:
        text = json.dumps(message)
        for dev in self.all():
            if dev.client_ip == ip:
                try:
                    await dev.ws.send_text(text)
                    return True
                except Exception as e:
                    log.warning(f"Failed to send to {dev}: {e}")
                    return False
        log.warning(f"No WebSocket connection for IP {ip}")
        return False
