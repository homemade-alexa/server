import base64
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from command.Interpreter import TTS_Type
from helpers.Auth import create_token
from .common import (
    AUTH_JWT_DAYS, AUTH_JWT_SECRET, AUTH_PASSWORD_HASH, AUTH_USERNAME,
    handle_ws, ingest_audio, interpreter, log, require_auth,
    verify_password, verify_token,
)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/api/public/auth/login")
async def auth_login(body: LoginRequest):
    if (not AUTH_USERNAME or body.username != AUTH_USERNAME
            or not AUTH_PASSWORD_HASH or not verify_password(body.password, AUTH_PASSWORD_HASH)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(AUTH_JWT_SECRET, AUTH_JWT_DAYS)
    return JSONResponse({"token": token})


@router.websocket("/ws/public")
async def ws_public(ws: WebSocket, token: str = Query(default="")):
    if not verify_token(token, AUTH_JWT_SECRET):
        await ws.accept()
        await ws.close(code=4001)
        return
    await handle_ws(ws, "WS/public")


@router.post("/api/public/stt", dependencies=[Depends(require_auth)])
async def stt_remote(request: Request):
    client_ip, command, filename = await ingest_audio(request)  # noqa: F841

    next_cmd: str = 'idle'
    audio_b64: str | None = None

    try:
        if command.strip():
            response = interpreter.interpret(command, TTS_Type.FILE)
            log.info(f"[STT/R] interpreter: {response}")
            if response.filename and os.path.isfile(response.filename):
                with open(response.filename, 'rb') as f:
                    audio_b64 = base64.b64encode(f.read()).decode()
                os.remove(response.filename)
            if not response.extra.get('end'):
                next_cmd = 'listen'
    finally:
        try:
            os.remove(filename)
        except OSError:
            pass

    return JSONResponse({'status': 'ok', 'command': command, 'next': next_cmd, 'audio_b64': audio_b64})
