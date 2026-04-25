import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import requests
from fastapi import Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from command.Interpreter import Interpreter, TTS_Type
from helpers.AudioClient import AudioClient
from helpers.Auth import verify_password, verify_token
from helpers.DeviceRegistry import DeviceConnection, DeviceRegistry
from helpers.SpeechToText import SpeechToText
from helpers.WavHelper import WavHelper
from helpers.WavSaver import WavSaver

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = _ROOT / "config.toml"

with open(CONFIG_PATH, "rb") as f:
    _cfg = tomllib.load(f)

HOST: str = _cfg["server"]["host"]
PORT: int = _cfg["server"]["port"]
SERVE_URL: str = _cfg["server"].get("serve_url", "").rstrip("/")
FIRMWARE_DIR = Path(_cfg["firmware"]["dir"])
AUDIO_LOG_DIR = Path(_cfg["audio"]["log_dir"])
AUDIO_SERVER_URL: str = _cfg.get("audio_server", {}).get("url", "").rstrip("/")
SOUNDS_DIR = Path(_cfg["sounds"]["dir"])

_auth_cfg = _cfg.get("auth", {})
AUTH_USERNAME: str = _auth_cfg.get("username", "")
AUTH_PASSWORD_HASH: str = _auth_cfg.get("password_hash", "")
AUTH_JWT_SECRET: str = _auth_cfg.get("jwt_secret", "")
AUTH_JWT_DAYS: int = int(_auth_cfg.get("jwt_expire_days", 30))

WEBAPP_DIR = _ROOT / "web"
WEBAPP_BASE: str = _cfg.get("webapp", {}).get("base", "/alexa")

FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_LOG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("alexa_server")

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

registry = DeviceRegistry()
interpreter = Interpreter()
_stt_seq: dict[str, int] = {}
_wakeword_events: dict[str, asyncio.Event] = {}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)) -> None:
    if not credentials or not verify_token(credentials.credentials, AUTH_JWT_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def abort_audio() -> None:
    if not AUDIO_SERVER_URL:
        log.warning("[ABORT] audio_server URL not configured")
        return
    try:
        requests.post(f"{AUDIO_SERVER_URL}/api/abort", timeout=2)
    except Exception as e:
        log.warning(f"[ABORT] failed to reach audio server: {e}")


async def ingest_audio(request: Request) -> tuple[str, str, str]:
    """Read audio request → write WAV → run STT. Returns (client_ip, command, wav_path)."""
    body = await request.body()
    h = request.headers
    rate     = h.get("x-audio-sample-rate", "16000")
    bits     = h.get("x-audio-bits", "16")
    channels = h.get("x-audio-channel", "1")
    codec    = h.get("x-audio-codec", "?")
    client_ip = request.client.host if request.client else h.get("x-forwarded-for", "unknown")

    log.info(f"[STT] audio from {client_ip} — {len(body)} bytes, codec={codec}, {rate}Hz/{bits}bit/{channels}ch")

    filename = WavSaver().write_wav(AUDIO_LOG_DIR, list(body), int(rate), int(bits), int(channels))

    command = ''
    if body:
        command = SpeechToText().recognize(filename)
        log.info(f'[STT] recognized from {client_ip}: "{command}"')

    return client_ip, command, filename


async def process_stt(client_ip: str, command: str, filename: str, seq: int) -> None:
    wakeword_ev = asyncio.Event()
    _wakeword_events[client_ip] = wakeword_ev
    continue_conversation = False
    try:
        if command.strip():
            duration = 0
            response = interpreter.interpret(command, TTS_Type.FILE)
            log.info(f"[STT] interpreter response: {response}")
            if response:
                if response.filename and os.path.isfile(response.filename):
                    duration = WavHelper.get_duration(response.filename)
                    log.info(f"[STT] playing response ({duration}s)")
                    AudioClient.send(response.filename)
                    os.remove(response.filename)

                if not response.extra.get("end"):
                    continue_conversation = True

            if duration:
                log.info(f"[STT] waiting {duration}s for playback")
                try:
                    await asyncio.wait_for(wakeword_ev.wait(), timeout=duration)
                    log.info(f"[STT] playback interrupted by wakeword for {client_ip}")
                except asyncio.TimeoutError:
                    pass
        else:
            log.info(f"[STT] empty audio from {client_ip}")
    except Exception as e:
        log.error(f"[STT] background processing error: {e}")
    finally:
        if _wakeword_events.get(client_ip) is wakeword_ev:
            del _wakeword_events[client_ip]
        try:
            os.remove(filename)
        except OSError:
            pass

        if _stt_seq.get(client_ip) != seq or wakeword_ev.is_set():
            log.info(f"[STT] stale/interrupted task (seq {seq}), skipping cmd for {client_ip}")
        else:
            if not continue_conversation:
                AudioClient.send(f"{SOUNDS_DIR}/end.wav")

            cmd = "listen" if continue_conversation else "idle"
            log.info(f"[STT] sending {cmd} command to {client_ip}")

            await registry.send_to_ip(client_ip, {"cmd": cmd})


async def handle_ws_message(dev: DeviceConnection, raw: str) -> None:
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        log.warning(f"[WS] non-JSON from {dev}: {raw!r}")
        return

    if "hello" in msg:
        dev.info = msg["hello"]
        log.info(f"[WS] hello from {dev}")
        return

    if msg.get("event") == "wakeword":
        log.info(f"[WS] wakeword from {dev} — aborting audio playback")
        abort_audio()
        AudioClient.send(f"{SOUNDS_DIR}/start.wav")
        ev = _wakeword_events.get(dev.client_ip)
        if ev:
            ev.set()
        return

    log.info(f"[WS] message from {dev}: {msg}")


async def handle_ws(ws: WebSocket, label: str) -> None:
    await ws.accept()
    dev = registry.register(ws, ws.client.host)
    log.info(f"[{label}] connected from {dev.client_ip}  (total: {len(registry)})")

    try:
        while True:
            raw = await ws.receive_text()
            await handle_ws_message(dev, raw)
    except WebSocketDisconnect:
        log.info(f"[{label}] disconnected: {dev}")
    except Exception as e:
        log.error(f"[{label}] error for {dev}: {e}")
    finally:
        registry.unregister(ws)
        log.info(f"[{label}] devices remaining: {len(registry)}")
