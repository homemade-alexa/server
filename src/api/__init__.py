from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .common import FIRMWARE_DIR, HOST, PORT, SERVE_URL, WEBAPP_BASE, WEBAPP_DIR, log
from .internal import router as internal_router
from .public import router as public_router

from helpers.ReminderScheduler import get_scheduler

app = FastAPI(title="Alexa Server", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(public_router)
app.include_router(internal_router)

if WEBAPP_DIR.exists():
    app.mount(WEBAPP_BASE, StaticFiles(directory=WEBAPP_DIR, html=True), name="webapp")


@app.on_event("startup")
async def on_startup():
    log.info(f"Alexa Server starting on {HOST}:{PORT}")
    log.info(f"Firmware dir: {FIRMWARE_DIR.resolve()}")
    log.info(f"Serve URL: {SERVE_URL or '(derived from client IP)'}")
    get_scheduler().start()
    log.info("[REMINDER] scheduler started")


@app.on_event("shutdown")
async def on_shutdown():
    get_scheduler().shutdown(wait=False)
    log.info("[REMINDER] scheduler stopped")
