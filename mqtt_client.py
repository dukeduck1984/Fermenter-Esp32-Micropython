import machine
import ubinascii

from umqtt.robust import MQTTClient
from logger import init_logger


logger = init_logger(__name__)

class MQTT:
    def __init__(self, user_settings_dict):
        settings = user_settings_dict.get('mqtt')
        server = settings.get('brokerAddr')
        port = settings.get('brokerPort')
        username = settings.get('username')
        password = settings.get('password')
        client_id = 'fermenter-' + str(ubinascii.hexlify(machine.unique_id()), 'UTF-8')
        self.enabled = settings.get('enabled')
        self.interval_ms = settings.get('pubIntervalMs')
        self.topic = settings.get('topic')
        if self.topic.endswith('/'):
            self.topic = self.topic[:-1]
        self.client = MQTTClient(client_id, server, port, username, password)

    def is_enabled(self):
        return self.enabled

    def manually_enable(self):
        self.enabled = True

    def manually_disable(self):
        self.enabled = False

    def get_update_interval_ms(self):
        return self.interval_ms

    def connect(self):
        try:
            self.client.connect()
        except Exception as e:
            logger.warning('Failed to connect to the MQTT broker.')

    def disconnect(self):
        self.client.disconnect()

    def publish(self, str_msg):
        try:
            self.connect()
        except Exception:
            logger.warning('Failed to publish the data to the MQTT broker.')
        else:
            logger.debug('Data have been published to the MQTT broker.')
            self.client.publish(self.topic, str_msg)
            self.disconnect()
