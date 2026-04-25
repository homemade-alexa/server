from command.IntentModule import IntentModule, CommandOutput


class NowyTemat(IntentModule):
    @property
    def tool_name(self) -> str:
        return "nowy_temat"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "nowy_temat",
            "description": "Użytkownik chce zresetować kontekst rozmowy i zacząć od nowa (np. 'zmieńmy temat', 'zacznijmy od nowa', 'nowa rozmowa').",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        return CommandOutput(
            "Nowy temat",
            ["Jasne, zacznijmy od nowa!", "Oczywiście, o czym chcesz porozmawiać?"],
            extra={"reset": True},
        )
