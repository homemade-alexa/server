import logging
from datetime import datetime

from command.IntentModule import CommandOutput, IntentModule
from helpers.ReminderScheduler import format_reminder_time, get_scheduler

log = logging.getLogger(__name__)


class UsunPrzypomnienie(IntentModule):
    @property
    def tool_name(self) -> str:
        return "usun_przypomnienie"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "usun_przypomnienie",
            "description": "Użytkownik chce usunąć przypomnienie ustawione na określoną godzinę, np. 'usuń przypomnienie na 15:30'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scheduled_at": {
                        "type": "string",
                        "description": (
                            "Czas usuwanego przypomnienia jako ISO 8601, np. '2025-01-15T15:30:00'. "
                            "Oblicz go na podstawie aktualnej daty i godziny podanej w prompcie systemowym."
                        ),
                    },
                },
                "required": ["scheduled_at"],
            },
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        try:
            dt = datetime.fromisoformat(args["scheduled_at"])
        except (ValueError, KeyError) as e:
            log.warning(f"[REMOVE] could not parse scheduled_at: {args.get('scheduled_at')!r} — {e}")
            return CommandOutput("UsunPrzypomnienie", ["Przepraszam, nie rozumiem której godziny dotyczy to przypomnienie."])

        jobs = get_scheduler().get_jobs()
        matched = [j for j in jobs if j.next_run_time.hour == dt.hour and j.next_run_time.minute == dt.minute]

        if not matched:
            return CommandOutput("UsunPrzypomnienie", [f"Nie mam przypomnienia na {dt.strftime('%H:%M')}."])

        for job in matched:
            log.info(f"[REMOVE] removing job {job.id} at {job.next_run_time.isoformat()}")
            job.remove()

        when = format_reminder_time(matched[0].next_run_time)
        if len(matched) == 1:
            text = matched[0].args[0] if matched[0].args else "?"
            phrase = f"Usunęłam przypomnienie {when}: {text}."
        else:
            phrase = f"Usunęłam {len(matched)} przypomnienia {when}."
        return CommandOutput("UsunPrzypomnienie", [phrase], extra={"end": True})
