import logging
import os
from datetime import datetime
from pathlib import Path

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from helpers.AudioClient import AudioClient
from helpers.TTSHelper import TTSHelper

log = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent.parent.parent / "reminders.db"

_scheduler = AsyncIOScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=f"sqlite:///{_DB_PATH}")}
)


_DAY_NAMES = {
    0: "w poniedziałek",
    1: "we wtorek",
    2: "w środę",
    3: "w czwartek",
    4: "w piątek",
    5: "w sobotę",
    6: "w niedzielę",
}


def format_reminder_time(dt: datetime) -> str:
    today = datetime.now().date()
    delta = (dt.date() - today).days
    time_str = dt.strftime("%H:%M")
    if delta == 0:
        return f"o {time_str}"
    if delta == 1:
        return f"jutro o {time_str}"
    if 2 <= delta <= 6:
        return f"{_DAY_NAMES[dt.weekday()]} o {time_str}"
    if delta == 7:
        return f"za tydzień o {time_str}"
    return f"za {delta} dni o {time_str}"


def get_scheduler() -> AsyncIOScheduler:
    return _scheduler


def fire_reminder(text: str) -> None:
    log.info(f"[REMINDER] firing: {text!r}")
    try:
        filename = TTSHelper().say(f"Przypominam zgodnie z życzeniem, że masz {text}")
        AudioClient.send(filename)
        os.remove(filename)
    except Exception as e:
        log.error(f"[REMINDER] error: {e}")
