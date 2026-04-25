import random
from paho.mqtt import client as mqtt
import logging

logger = logging.getLogger(__name__)

mqtt_host: str = '192.168.0.11'
mqtt_port: int = 1883


class MqttHelper:
    mqtt: mqtt.Client

    def __init__(self):
        self.mqtt = mqtt.Client(f'intent-detector-{random.randint(0, 1000)}')

    def publish(self, topic: str, msg: str):
        logger.debug(f'Publishing {msg} on topic {topic}')
        self.mqtt.connect(mqtt_host, mqtt_port)
        self.mqtt.publish(topic, msg)
