import machine
import utime


class Actuator:
    def __init__(self, pin, interval=None):
        """
        pin: int; GPIO pin number
        interval: int; time in seconds between turning on & off, eg. fridge compressor
        """
        self.actuator = machine.Pin(pin, machine.Pin.OUT)
        self.interval = interval
        self.last_time = None  # last time when the actuator is turned on or off
        self.status = False  # the default status is 'off'

    def action(self, val):
        """
        val: int; 0 or 1, control the pin output
        """
        if val == 0 or val == 1:
            self.actuator.value(val)
            self.last_time = utime.time()
        else:
            print('Invalid action!')
            return

    def check_interval(self, val):
        """
        val: int; 0 or 1, control the pin output
        """
        if self.interval:
            if self.last_time:
                if (utime.time() - self.last_time) >= self.interval:
                    self.action(val)
            else:
                self.action(val)
        else:
            self.action(val)
    
    def on(self):
        """
        turn on the actuator
        """
        self.check_interval(1)
        self.status = True  # set status to 'on'
    
    def off(self):
        """
        turn off the actuator
        """
        self.check_interval(0)
        self.status = False  # set status to 'off'
    
    def is_on(self):
        """
        return: boolean; the on/off status of the actuator
        """
        return self.status

