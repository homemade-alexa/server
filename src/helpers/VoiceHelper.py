import logging
import json

from helpers.MqttHelper import MqttHelper

logger = logging.getLogger(__name__)

topic = 'hermes/tts/say'


class VoiceHelper(MqttHelper):
    def say(self, text: str):
        logger.debug(f"SAYING {text}")
        txt = json.dumps(text)
        self.publish(topic, f'{{"text": {txt}}}')
