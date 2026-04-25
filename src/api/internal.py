import random
import time
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .common import (
    FIRMWARE_DIR, PORT, SERVE_URL, abort_audio, handle_ws,
    ingest_audio, interpreter, log, process_stt, registry, _stt_seq,
)
from command.Interpreter import TTS_Type

router = APIRouter()


@router.websocket("/ws/internal")
async def ws_internal(ws: WebSocket):
    await handle_ws(ws, "WS/internal")


@router.post("/api/internal/stt")
async def stt(request: Request, background_tasks: BackgroundTasks):
    client_ip, command, filename = await ingest_audio(request)
    seq = _stt_seq.get(client_ip, 0) + 1
    _stt_seq[client_ip] = seq
    background_tasks.add_task(process_stt, client_ip, command, filename, seq)
    return JSONResponse(content={"status": "ok", "command": command})


@router.post("/api/internal/abort")
async def abort():
    abort_audio()
    return JSONResponse({"status": "ok"})


@router.post("/api/internal/listen")
async def trigger_listen():
    if not registry:
        raise HTTPException(status_code=503, detail="No devices connected")
    ok = await registry.broadcast({"cmd": "listen"})
    log.info(f"[LISTEN] sent to {ok}/{len(registry)} device(s)")
    return JSONResponse(content={"status": "sent", "devices_notified": ok, "devices_total": len(registry)})


class DisplayRequest(BaseModel):
    text: str
    title: str = ""


@router.post("/api/internal/display")
async def trigger_display(body: DisplayRequest):
    if not registry:
        raise HTTPException(status_code=503, detail="No devices connected")
    cmd = {"cmd": "display", "data": {"title": body.title, "text": body.text}}
    ok = await registry.broadcast(cmd)
    log.info(f"[DISPLAY] sent to {ok}/{len(registry)} device(s): {body.text!r}")
    return JSONResponse(content={"status": "sent", "devices_notified": ok, "devices_total": len(registry)})


@router.post("/api/internal/ota")
async def trigger_ota(request: Request):
    if not registry:
        raise HTTPException(status_code=503, detail="No devices connected")

    requested_name: Optional[str] = None
    try:
        body = await request.json()
        requested_name = body.get("filename")
    except Exception:
        pass

    if requested_name:
        firmware_path = FIRMWARE_DIR / requested_name
        if not firmware_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {requested_name}")
    else:
        bin_files = sorted(FIRMWARE_DIR.glob("*.bin"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not bin_files:
            raise HTTPException(status_code=404, detail=f"No .bin file in {FIRMWARE_DIR.resolve()}")
        firmware_path = bin_files[0]

    base_url = SERVE_URL or f"http://{request.client.host}:{PORT}"
    firmware_url = f"{base_url}/firmware/{firmware_path.name}"

    log.info(f"[OTA] triggering update on {len(registry)} device(s) with {firmware_path.name}")
    log.info(f"[OTA] firmware URL: {firmware_url}")

    ok = await registry.broadcast({"cmd": "ota_start", "ota_url": firmware_url})
    return JSONResponse(content={
        "status": "sent",
        "firmware": firmware_path.name,
        "url": firmware_url,
        "devices_notified": ok,
        "devices_total": len(registry),
    })


class ChatRequest(BaseModel):
    command: str


@router.post("/api/internal/chat")
async def chat(body: ChatRequest):
    if not body.command.strip():
        raise HTTPException(status_code=400, detail="Empty command")
    output = interpreter.interpret(body.command, TTS_Type.NONE)
    phrase = random.choice(output.response_phrase) if output.response_phrase else ""
    log.info(f"[CHAT] command={body.command!r} → {phrase!r}")
    return JSONResponse(content={"response_phrase": phrase, "label": output.label})


@router.get("/api/internal/status")
async def status():
    return JSONResponse(content={
        "devices": [
            {
                "ip": d.client_ip,
                "hostname": d.info.get("hostname"),
                "hw_type": d.info.get("hw_type"),
                "connected_seconds": int(time.time() - d.connected_at),
            }
            for d in registry.all()
        ],
        "firmware_dir": str(FIRMWARE_DIR.resolve()),
        "firmware_files": [f.name for f in sorted(FIRMWARE_DIR.glob("*.bin"))],
    })


@router.get("/firmware/{filename}")
async def serve_firmware(filename: str):
    path = (FIRMWARE_DIR / filename).resolve()
    if not str(path).startswith(str(FIRMWARE_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not path.exists() or path.suffix != ".bin":
        raise HTTPException(status_code=404, detail=f"Firmware not found: {filename}")
    log.info(f"[OTA] serving {filename} ({path.stat().st_size} bytes)")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)
