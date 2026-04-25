import json
import logging
import time
from datetime import datetime

import requests

from command.IntentModule import IntentModule

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Jesteś asystentką głosową o imieniu Aleksa rozmawiającą z użytkownikiem za pomocą mowy. "
    "Masz do dyspozycji zestaw narzędzi. "
    "Jeśli wypowiedź użytkownika pasuje do jednego z nich — wywołaj odpowiednie narzędzie. "
    "Jeśli żadne narzędzie nie pasuje — odpowiedz krótko i uprzejmie jako asystentka. "
    "Nie stosuj emotikon. Odpowiadaj zwięźle."
)

_MAX_HISTORY_EXCHANGES = 10


class LLMRouter:
    def __init__(self, modules: list[IntentModule], api_key: str, model: str = "gpt-4.1",
                 session_timeout: int = 300):
        self._modules: dict[str, IntentModule] = {
            m.tool_name: m for m in modules if m.tool_schema is not None
        }
        self._tools = [
            {"type": "function", "function": m.tool_schema}
            for m in modules if m.tool_schema is not None
        ]
        self._api_key = api_key
        self._model = model
        self._history: list[dict] = []
        self._last_activity: float = 0.0
        self._session_timeout = session_timeout
        log.info(f"[LLMRouter] loaded tools: {list(self._modules.keys())}")

    def reset_history(self) -> None:
        self._history.clear()
        log.info("[LLMRouter] conversation history cleared")

    def route(self, phrase: str) -> tuple[IntentModule | None, dict]:
        now = time.monotonic()
        if self._history and self._session_timeout > 0:
            elapsed = now - self._last_activity
            if elapsed > self._session_timeout:
                log.info(f"[LLMRouter] session timeout after {elapsed:.0f}s — history cleared")
                self._history.clear()
        self._last_activity = now

        user_msg = {"role": "user", "content": phrase}
        system_content = f"Aktualna data i godzina: {datetime.now().strftime('%Y-%m-%d %H:%M')}.\n{SYSTEM_PROMPT}"
        messages = [{"role": "system", "content": system_content}] + self._history + [user_msg]

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": messages,
            "tools": self._tools,
            "tool_choice": "auto",
        }
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers=headers,
        ).json()

        choice = res["choices"][0]["message"]

        if choice.get("tool_calls"):
            tool_call = choice["tool_calls"][0]
            name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])
            log.info(f"[LLMRouter] tool call → {name}({args})")
            module = self._modules.get(name)
            if module:
                return module, args
            log.warning(f"[LLMRouter] unknown tool: {name}")

        content = choice.get("content", "")
        log.info(f"[LLMRouter] chat response: {content!r}")

        self._history.append(user_msg)
        self._history.append({"role": "assistant", "content": content})
        if len(self._history) > _MAX_HISTORY_EXCHANGES * 2:
            self._history = self._history[-_MAX_HISTORY_EXCHANGES * 2:]

        return None, {"text": content}
