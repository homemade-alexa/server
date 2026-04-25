import datetime
import locale
import logging

from command.IntentModule import IntentModule, CommandOutput

logger = logging.getLogger(__name__)


class Dzien(IntentModule):
    @property
    def tool_name(self) -> str:
        return "dzien"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "dzien",
            "description": "Użytkownik pyta o aktualną datę, dzień miesiąca albo tygodnia.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        locale.setlocale(locale.LC_TIME, "pl_PL.UTF-8")
        now = datetime.datetime.now()
        current_date = now.strftime("%A, %d %B %Y")
        resp = f'Jest {current_date}.'
        return CommandOutput(resp, [resp])
