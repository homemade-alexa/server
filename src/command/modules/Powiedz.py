import logging

from command.IntentModule import IntentModule, CommandOutput

logger = logging.getLogger(__name__)


class Powiedz(IntentModule):
    @property
    def tool_name(self) -> str:
        return "powiedz"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "powiedz",
            "description": "Użytkownik prosi asystentkę żeby powtórzyła lub powiedziała konkretną frazę (np. 'powiedz dzień dobry').",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Tekst do wypowiedzenia",
                    }
                },
                "required": ["text"],
            },
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        text = args.get("text", "")
        logger.debug(f"SAYING {text}")
        return CommandOutput("OK, mówię", [text])
