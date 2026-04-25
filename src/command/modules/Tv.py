import logging

from command.IntentModule import IntentModule, CommandOutput
from helpers.MqttHelper import MqttHelper

logger = logging.getLogger(__name__)


class Tv(IntentModule):
    @property
    def tool_name(self) -> str:
        return "tv"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "tv",
            "description": "Użytkownik chce włączyć lub wyłączyć telewizor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "on — włącz telewizor, off — wyłącz telewizor",
                    }
                },
                "required": ["state"],
            },
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        if args.get("state") == "on":
            MqttHelper().publish('xis/command', '{"command": "tv", "state": "on"}')
            return CommandOutput('Włączam telewizor', ['Telewizor włączony', 'Włączam telewizor'])
        else:
            MqttHelper().publish('xis/command', '{"command": "tv", "state": "off"}')
            return CommandOutput('Wyłączam telewizor', ['Telewizor wyłączony', 'Wyłączam telewizor'])
