import logging

from command.IntentModule import CommandOutput, IntentModule
from helpers.ReminderScheduler import format_reminder_time, get_scheduler

log = logging.getLogger(__name__)


class ListaPrzypomnien(IntentModule):
    @property
    def tool_name(self) -> str:
        return "lista_przypomnien"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "lista_przypomnien",
            "description": "Użytkownik pyta o zaplanowane przypomnienia, np. 'jakie mam przypomnienia', 'co mam zaplanowane'.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        jobs = get_scheduler().get_jobs()
        if not jobs:
            return CommandOutput("ListaPrzypomnien", ["Nie masz żadnych zaplanowanych przypomnień."])

        parts = []
        for job in sorted(jobs, key=lambda j: j.next_run_time):
            when = format_reminder_time(job.next_run_time)
            text = job.args[0] if job.args else "?"
            parts.append(f"{when} — {text}")

        count = len(jobs)
        noun = "przypomnienie" if count == 1 else ("przypomnienia" if count in (2, 3, 4) else "przypomnień")
        phrase = f"Masz {count} {noun}: " + ", ".join(parts)
        log.info(f"[LIST] {phrase}")
        return CommandOutput("ListaPrzypomnien", [phrase])
