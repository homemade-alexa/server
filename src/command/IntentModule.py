from dataclasses import dataclass, field


@dataclass
class CommandOutput:
    label: str
    response_phrase: list[str]
    filename: str = None
    extra: dict = field(default_factory=dict)


class IntentModule:
    @property
    def tool_name(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def tool_schema(self) -> dict | None:
        return None

    def reset(self):
        pass

    def matches(self, phrase: str) -> bool:
        pass

    def execute(self, args: dict = {}) -> CommandOutput:
        pass
