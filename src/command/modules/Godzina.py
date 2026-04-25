import datetime
import logging

from command.IntentModule import IntentModule, CommandOutput

logger = logging.getLogger(__name__)


class Godzina(IntentModule):
    @property
    def tool_name(self) -> str:
        return "godzina"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "godzina",
            "description": "Użytkownik pyta o aktualną godzinę lub porę dnia.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        resp = f'Jest {current_time}.'
        return CommandOutput(resp, [resp])
