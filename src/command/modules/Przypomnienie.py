import logging
from datetime import datetime

from command.IntentModule import CommandOutput, IntentModule
from helpers.ReminderScheduler import fire_reminder, format_reminder_time, get_scheduler

log = logging.getLogger(__name__)


class Przypomnienie(IntentModule):
    @property
    def tool_schema(self) -> dict:
        return {
            "name": "przypomnienie",
            "description": (
                "Użytkownik chce ustawić przypomnienie na określony czas w przyszłości, "
                "np. 'przypomnij mi za godzinę', 'ustaw przypomnienie na 15:30'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scheduled_at": {
                        "type": "string",
                        "description": (
                            "Dokładny czas przypomnienia jako ISO 8601, np. '2025-01-15T15:30:00'. "
                            "Oblicz go na podstawie aktualnej daty i godziny podanej w prompcie systemowym."
                        ),
                    },
                    "reminder_text": {
                        "type": "string",
                        "description": "Treść przypomnienia w bezokoliczniku, np. 'wyjść na spacer z psem'",
                    },
                },
                "required": ["scheduled_at", "reminder_text"],
            },
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        try:
            dt = datetime.fromisoformat(args["scheduled_at"])
        except (ValueError, KeyError) as e:
            log.warning(f"[REMINDER] could not parse scheduled_at: {args.get('scheduled_at')!r} — {e}")
            return CommandOutput(
                "Przypomnienie",
                ["Przepraszam, nie rozumiem kiedy mam Ci przypomnieć."],
            )

        if dt <= datetime.now():
            log.warning(f"[REMINDER] scheduled time is in the past: {dt.isoformat()}")
            return CommandOutput(
                "Przypomnienie",
                ["Ten czas już minął. Podaj czas w przyszłości."],
            )

        reminder_text = args["reminder_text"]
        get_scheduler().add_job(
            fire_reminder,
            "date",
            run_date=dt,
            args=[reminder_text],
            misfire_grace_time=60,
        )
        log.info(f"[REMINDER] scheduled at {dt.isoformat()}: {reminder_text!r}")
        phrase = f"Powiadomię Cię {format_reminder_time(dt)}, że masz {reminder_text}"
        return CommandOutput("Przypomnienie", [phrase], extra={"end": True})
