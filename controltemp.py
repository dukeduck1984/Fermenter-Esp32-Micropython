class FermenterTempControl:
    """Fermenter Temperature Control Logic
       Cooler and heater are controlled by PID aim to keep the wort to the target temperature,
       and the working status of the cooler and heater are indicated by the RGB LED.

       Note that the temperature readings here are not realtime measured.
       The realtime temp measurements are done in the main logic at a higher frequency.
    """

    def __init__(self, cooler_obj, heater_obj, wort_sensor_obj, chamber_sensor_obj, pid_obj, led_obj):
        self.set_temp = None
        self.cooler = cooler_obj
        self.heater = heater_obj
        self.wort_sensor = wort_sensor_obj
        self.chamber_sensor = chamber_sensor_obj
        self.pid = pid_obj
        self.led = led_obj
        self.job_done = False
        # self.led.set_color('green')  # set led to green when machine is on while actuators are not working
    
    def get_wort_temp(self):
        return self.wort_sensor.read_temp()
    
    def get_chamber_temp(self):
        return self.chamber_sensor.read_temp()

    def run(self, set_temp):
        self.set_temp = set_temp
        chamber_temp = self.get_chamber_temp()
        if self.wort_sensor.is_connected():
            wort_temp = self.get_wort_temp()

            pid_output = round(self.pid.update(wort_temp, self.set_temp), 1)
            target_chamber_temp = self.set_temp + pid_output

            if chamber_temp is None:
                self.heater.off()
            elif wort_temp < self.set_temp and chamber_temp < target_chamber_temp:
                self.heater.on()
            elif wort_temp >= self.set_temp or chamber_temp >= target_chamber_temp:
                self.heater.off()
            else:
                self.heater.off()

            if chamber_temp is None:
                self.cooler.off()
            elif wort_temp > self.set_temp and chamber_temp > target_chamber_temp:
                self.cooler.on()
            elif wort_temp <= self.set_temp or chamber_temp <= target_chamber_temp:
                self.cooler.off()
            else:
                self.cooler.off()
        else:
            temp_delta = chamber_temp - self.set_temp
            # temp_delta 大于 3.0 需要快速降温
            # temp_delta 在1.0-3.0之间 需要缓慢降温
            # temp_delta 小于 -0.3 则需要升温
            if temp_delta > 3.0:
                self.cooler.on()
                self.heater.off()
            elif 1.0 < temp_delta <= 3.0:
                self.cooler.on()
                self.heater.on()
            elif temp_delta < -0.3:
                self.heater.on()
                self.cooler.off()
            else:
                self.heater.off()
                self.cooler.off()

        # Set LED color according to actuator status
        if self.heater.is_on() and not self.cooler.is_on():
            # LED为红色表示发酵箱正在制热
            self.led.set_color('red')
        elif self.cooler.is_on():
            # LED为蓝色表示发酵箱正在制冷
            self.led.set_color('blue')
        else:
            # LED为绿色表示发酵箱处于待机状态（制热制冷均不工作）
            self.led.set_color('green')

    def accomplished(self):
        self.job_done = True

    def reset(self):
        self.heater.force_off()
        self.cooler.force_off()
        self.led.set_color('green')
        self.job_done = False
