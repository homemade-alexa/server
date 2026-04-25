import random

from command.IntentModule import IntentModule, CommandOutput

_dialogs = {
    "milosc": ['Ja ciebie też!', 'Ja ciebie bardziej!'],
    "dobranoc": ['Dobrej nocy...', 'Kolorowych snów'],
    "powitanie": ['Dzień dobry!', 'Witaj!', 'Cześć!', 'Hej!'],
}


class SimpleDialog(IntentModule):
    @property
    def tool_name(self) -> str:
        return "simple_dialog"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "simple_dialog",
            "description": "Użytkownik wypowiada standardową formułę grzecznościową: powitanie, wyznanie uczuć lub dobranoc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dialog_type": {
                        "type": "string",
                        "enum": ["powitanie", "milosc", "dobranoc"],
                        "description": "Typ wypowiedzi",
                    }
                },
                "required": ["dialog_type"],
            },
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        dialog_type = args.get("dialog_type", "powitanie")
        responses = _dialogs.get(dialog_type, _dialogs["powitanie"])
        return CommandOutput(responses[0], responses)
