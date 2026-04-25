import logging

from command.IntentModule import IntentModule, CommandOutput
from helpers.WeatherHelper import WeatherHelper

logger = logging.getLogger(__name__)


class Pogoda(IntentModule):
    @property
    def tool_name(self) -> str:
        return "pogoda"

    @property
    def tool_schema(self) -> dict:
        return {
            "name": "pogoda",
            "description": "Użytkownik pyta o pogodę lub temperaturę na zewnątrz.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, args: dict = {}) -> CommandOutput:
        w = WeatherHelper().get_weather()
        logger.debug(f'Got weather info: {w}')
        return CommandOutput('Podaję informacje o pogodzie', [w])
