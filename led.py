#
# This code works for ESP32 psRAM LoBo port of the micropython
# The code is not compatible with ESP8266 or the official port of the ESP32
# See: https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo
#
import machine
import utime


class RgbLed:
    def __init__(self, r_pin, g_pin, b_pin):
        """
        initialize the rgb led
        :param r_pin: int; pin for red color
        :param g_pin: int; pin for green color
        :param b_pin: int; pin for blue color
        """
        self.led_red = machine.PWM(machine.Pin(r_pin), duty=0, freq=500)
        self.led_green = machine.PWM(machine.Pin(g_pin), duty=0, freq=500)
        self.led_blue = machine.PWM(machine.Pin(b_pin), duty=0, freq=500)
        self.color = {
            # https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
            'off': [0, 0, 0],
            'white': [255, 255, 255],
            'red': [255, 0, 0],
            'green': [0, 255, 0],
            'blue': [0, 0, 255],
            'yellow': [255, 225, 25],
            'orange': [245, 130, 48],
            'purple': [145, 30, 180],
            'cyan': [70, 240, 240],
            'magenta': [240, 50, 230],
            'lime': [210, 245, 60],
            'pink': [250, 190, 190],
            'grey': [128, 128, 128],
        }

    @staticmethod
    def _rgb_decimal_duty(r, g, b):
        """
        convert rgb decimal to pwm duty cycle %
        :param r: int; red decimal
        :param g: int; green decimal
        :param b: int; blue decimal
        :return: tuple; red duty%, green duty%, blue duty%
        """
        n = 100 / 255
        r_duty = r * n
        g_duty = g * n
        b_duty = b * n
        return r_duty, g_duty, b_duty

    def set_color(self, color_name):
        """
        set rgb led to color per color table
        :param color_name: string; see dict self.color
        :return: None
        """
        if self.color.get(color_name):  # set led to given color name
            r_decimal, g_decimal, b_decimal = self.color.get(color_name)
            r_duty, g_duty, b_duty = self._rgb_decimal_duty(r_decimal, g_decimal, b_decimal)
            self.led_red.duty(r_duty)
            self.led_green.duty(g_duty)
            self.led_blue.duty(b_duty)
        else:
            # set led to green
            self.led_red.duty(0)
            self.led_green.duty(100)
            self.led_blue.duty(0)

    def turn_off(self):
        """
        turn off the led, and set the status to off
        :return: None
        """
        self.set_color('off')  # turn of the led light

