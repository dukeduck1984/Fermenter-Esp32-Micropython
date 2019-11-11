import uos
import ujson
from logger import init_logger


logger = init_logger(__name__)

class CrashRecovery:
    def __init__(self, filename='recovery.json', interval_ms=300000):
        self.filename = filename
        self.interval_ms = interval_ms

    def get_interval_ms(self):
        return self.interval_ms

    def set_interval_ms(self, interval_ms):
        self.interval_ms = interval_ms

    def is_needed(self):
        return self.filename in uos.listdir()

    def backing_up(self, process_info):
        logger.debug('Backing up current progress for crash recovery.')
        with open(self.filename, 'w') as f:
            ujson.dump(process_info, f)

    def remove_backup(self):
        if self.is_needed():
            uos.remove(self.filename)
            logger.debug('The Crash recovery backup has been removed.')

    def retrieve_backup(self):
        with open(self.filename, 'r') as f:
            backup = ujson.load(f)
        logger.debug('The interrupted progress has been recovered.')
        return backup
