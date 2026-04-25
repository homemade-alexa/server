import logging

from command.IntentModule import IntentModule, CommandOutput

logger = logging.getLogger(__name__)


class Alexa(IntentModule):
    @property
    def tool_name(self) -> str:
        return "alexa"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "alexa",
            "description": "Użytkownik zwraca się bezpośrednio do asystentki po imieniu (Aleksa, Alexa, hej) bez konkretnej komendy.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        return CommandOutput('Tak?', ['Tak?'])
