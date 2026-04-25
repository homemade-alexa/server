import logging

import requests

logger = logging.getLogger(__name__)

AUDIO_SERVER_HOST = "192.168.0.44"
AUDIO_SERVER_PORT = 1234


class AudioClient:
    @staticmethod
    def send(filename: str) -> None:
        url = f"http://{AUDIO_SERVER_HOST}:{AUDIO_SERVER_PORT}/api/play"
        try:
            logger.info(f"[AudioClient] sending {filename} to {url}")
            with open(filename, "rb") as f:
                requests.post(url, data=f, timeout=10)
        except Exception as e:
            logger.exception(f"[AudioClient] error: {e}")
