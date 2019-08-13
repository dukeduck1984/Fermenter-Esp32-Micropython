import uos
import ujson


class CrashRecovery:
    def __init__(self):
        self.filename = 'recovery.json'

    def is_needed(self):
        return self.filename in uos.listdir()

    def backing_up(self, process_info):
        with open(self.filename, 'w') as f:
            ujson.dump(process_info, f)

    def remove_backup(self):
        if self.is_needed():
            uos.remove(self.filename)

    def retrieve_backup(self):
        with open(self.filename, 'r') as f:
            backup = ujson.load(f)
        return backup