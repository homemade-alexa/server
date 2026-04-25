import importlib
import logging
import random
import sys
from enum import Enum
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from command.IntentModule import CommandOutput
from command.LLMRouter import LLMRouter
from helpers.TTSHelper import TTSHelper
from helpers.VoiceHelper import VoiceHelper

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.toml"

_MODULES = [
    'Alexa', 'Stop', 'NowyTemat', 'Godzina', 'Dzien',
    'Pogoda', 'Lampki', 'Tv',
    'SimpleDialog', 'Powiedz',
    'Przypomnienie', 'ListaPrzypomnien', 'UsunPrzypomnienie',
]


def _load(name: str):
    mod = importlib.import_module(f'command.modules.{name}')
    return getattr(mod, name)()

class TTS_Type(Enum):
    FILE = 1
    LOCAL = 2
    NONE = 3

class Interpreter:
    def __init__(self):
        with open(CONFIG_PATH, "rb") as f:
            cfg = tomllib.load(f)
        api_key = cfg["openai"]["api_key"]
        model = cfg["openai"].get("model", "gpt-4.1")
        session_timeout = cfg["openai"].get("session_timeout_seconds", 300)
        instances = [_load(name) for name in _MODULES]
        self.router = LLMRouter(instances, api_key, model, session_timeout=session_timeout)

    def interpret(self, command: str, tts_type: TTS_Type = TTS_Type.NONE) -> CommandOutput:
        command = command.rstrip('.,? ').replace(', ', ' ').lower()
        module, args = self.router.route(command)

        if module:
            logger.info(f'[Interpreter] → {module.tool_name}({args})')
            output = module.execute(args)
        else:
            logger.info('[Interpreter] → chat fallback')
            output = CommandOutput("ChatGPT", [args["text"]])

        if output.extra.get("end") or output.extra.get("reset"):
            self.router.reset_history()

        if output.response_phrase:
            phrase = random.choice(output.response_phrase)
            if tts_type == TTS_Type.LOCAL:
                VoiceHelper().say(phrase)
            elif tts_type == TTS_Type.FILE:
                output.filename = TTSHelper().say(phrase)
                logger.info(f"[TTS] got response filename {output.filename}")

        return output
