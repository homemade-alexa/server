import logging

from command.IntentModule import IntentModule, CommandOutput

logger = logging.getLogger(__name__)


class Stop(IntentModule):
    @property
    def tool_name(self) -> str:
        return "stop"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "stop",
            "description": "Użytkownik chce zakończyć rozmowę lub podziękować (ok, dziękuję, stop, koniec, cicho, wystarczy, dzięki, przestań).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        return CommandOutput('Oczywiście', ['Tak jest', 'Oczywiście'], extra={"end": True})
