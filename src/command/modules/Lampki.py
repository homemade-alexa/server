import logging

from command.IntentModule import IntentModule, CommandOutput
from helpers.MqttHelper import MqttHelper

logger = logging.getLogger(__name__)


class Lampki(IntentModule):
    @property
    def tool_name(self) -> str:
        return "lampki"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "lampki",
            "description": "Użytkownik chce włączyć lub wyłączyć lampki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "on — włącz lampki, off — wyłącz lampki",
                    }
                },
                "required": ["state"],
            },
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        if args.get("state") == "on":
            MqttHelper().publish('cmnd/tasmota_C2279B/Power1', 'ON')
            return CommandOutput('Włączam lampki', ['Lampka włączona', 'Włączam lampkę'])
        else:
            MqttHelper().publish('cmnd/tasmota_C2279B/Power1', 'OFF')
            return CommandOutput('Wyłączam lampki', ['Lampka wyłączona', 'Wyłączam lampkę'])
