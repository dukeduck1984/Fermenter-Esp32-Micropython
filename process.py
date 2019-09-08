import utime
import machine
import ujson


class Process:
    """
    Process.stage_run() -> start timer -> control temp & check progress -> start next stage -> end of final stage
    """
    def __init__(self, fermenter_temp_ctrl_obj, control_timer_obj, crash_recovery_obj, wifi_obj, mqtt_obj):
        """
        Initialize the fermenter process
        :param fermenter_temp_ctrl_obj: Class; the instance of FermenterTempControl class
        :param control_timer_obj: Class; the instance of the Timer class
        """
        self.beer_name = None
        self.fermentation_steps = None
        self.fermenter_temp_ctrl = fermenter_temp_ctrl_obj
        self.tim = control_timer_obj
        self.recovery = crash_recovery_obj
        self.wifi = wifi_obj
        self.backup_interval = 300000  # 每5分钟备份一次
        self.last_backup = None
        self.mqtt = mqtt_obj
        self.last_publish = None
        self.total_steps = len(self.fermentation_steps) if self.fermentation_steps is not None else 0
        self.start_time = None
        self.elapsed_time = None
        self.elapsed_before_recovery = 0
        self.is_completed = False
        self.current_step_index = None
        self.step_hours = None
        self.step_target_temp = None
        self.hydrometer_data = {
            'originalGravity': None,
            'currentGravity': None,
            'batteryLevel': None
        }
        self.hydrometer_status = {
            'is_online': False,
            'update_interval_ms': None,
            'last_time': None,
        }

    def set_beer_name(self, beer_name):
        self.beer_name = beer_name

    def save_hydrometer_data(self, hydrometer_dict_data):
        # 传入数据有updateIntervalSec代表数据来自比重计
        if hydrometer_dict_data.get('updateIntervalMs'):
            self.hydrometer_status['is_online'] = True
            self.hydrometer_status['update_interval_ms'] = hydrometer_dict_data.get('updateIntervalMs')
            self.hydrometer_status['last_time'] = utime.ticks_ms()
            self.hydrometer_data['currentGravity'] = hydrometer_dict_data.get('currentGravity')
            self.hydrometer_data['batteryLevel'] = hydrometer_dict_data.get('batteryLevel')
            if not self.hydrometer_data.get('originalGravity'):
                self.hydrometer_data['originalGravity'] = hydrometer_dict_data.get('currentGravity')
        # 否则代表传入数据来自于意外重启的恢复数据
        else:
            if hydrometer_dict_data.get('originalGravity'):
                self.hydrometer_data['originalGravity'] = hydrometer_dict_data.get('originalGravity')

    def _step_progress_check(self):
        """
        check the stage progress
        """
        now = utime.time()
        self.elapsed_time = now - self.start_time + self.elapsed_before_recovery
        # keep the PID temp control logic going even after all steps have been completed
        self.fermenter_temp_ctrl.run(self.step_target_temp)
        # if stage time is up
        if self.elapsed_time >= (self.step_hours * 3600):
            # if this is not the final stage
            if self.current_step_index < (self.total_steps - 1):
                # then proceed to next stage
                new_step_index = self.current_step_index + 1
                self.start(step_index=new_step_index)
            # if this is the end of the final stage
            else:
                self.is_completed = True
                self.fermenter_temp_ctrl.job_done = True
                self.fermenter_temp_ctrl.led.set_color('orange')
                print('All fermentation stages have completed.')

    def _check_hydrometer_status(self):
        """
        check the status of the hydrometer
        """
        if self.hydrometer_status.get('is_online'):
            timeout = self.hydrometer_status.get('update_interval_ms') * 2
            last_time = self.hydrometer_status.get('last_time')
            if utime.ticks_diff(utime.ticks_ms(), last_time) > timeout:
                self.hydrometer_status['is_online'] = False
                self.hydrometer_data['currentGravity'] = None
                self.hydrometer_data['batteryLevel'] = None

    def _process_backup(self):
        recovery_obj = self.recovery
        get_process_info = self.get_process_info
        this = self

        def do_backup():
            if this.has_started() and not this.has_completed():
                recovery_obj.backing_up(get_process_info())
                this.last_backup = utime.ticks_ms()
            elif this.has_completed():
                recovery_obj.remove_backup()
        if not self.last_backup:
            do_backup()
        else:
            if utime.ticks_diff(utime.ticks_ms(), self.last_backup) >= self.backup_interval:
                do_backup()

    def _publish_mqtt(self):
        if self.has_started() and not self.has_completed() and self.mqtt.is_enabled() and self.wifi.is_connected():
            process_info = self.get_process_info()
            set_temp = process_info.get('setTemp')
            wort_temp = process_info.get('wortTemp')
            chamber_temp = process_info.get('chamberTemp')
            step_percentage = process_info.get('currentFermentationStepPercentage')
            total_percentage = process_info.get('totalFermentationStepPercentage')
            og = process_info.get('hydrometerData').get('originalGravity')
            sg = process_info.get('hydrometerData').get('currentGravity')
            battery = process_info.get('hydrometerData').get('batteryLevel')
            basic_msg = {
                "set_temp": set_temp,
                "wort_temp": wort_temp,
                "chamber_temp": chamber_temp,
                "step_percentage": step_percentage,
                "total_percentage": total_percentage
            }
            if sg:
                combined_msg = basic_msg.copy()
                combined_msg.update({
                    "original_gravity": round(og, 3),
                    "specific_gravity": round(sg, 3),
                    "battery_percentage": battery
                })
                mqtt_msg = ujson.dumps(combined_msg)
            else:
                mqtt_msg = ujson.dumps(basic_msg)
            if not self.last_publish:
                self.mqtt.publish(mqtt_msg)
                self.last_publish = utime.ticks_ms()
            else:
                if utime.ticks_diff(utime.ticks_ms(), self.last_publish) >= self.mqtt.get_update_interval_ms():
                    self.mqtt.publish(mqtt_msg)
                    self.last_publish = utime.ticks_ms()

    def job_queue(self, t):
        # 1. 发酵温度控制（每5秒）
        self._step_progress_check()
        # 2. 检查比重计状态
        self._check_hydrometer_status()
        # 3. 发酵过程备份（每5分钟）
        self._process_backup()
        # 4. 发送数据至MQTT（每15分钟：用户可设置）
        try:
            self._publish_mqtt()
        except:
            pass

    def load_steps(self, fermentation_steps):
        """
        fermentation_stages: nested list; eg.[{'days': 2, 'temp': 18.6}, {'days': 14, 'temp': 21.5}, ..., {'days': 5, 'temp': 23.0}]
        """
        self.fermentation_steps = fermentation_steps
        self.total_steps = len(self.fermentation_steps)

    def start(self, step_index=0, step_hours_left=None):
        """
        pass stage index to get stage settings and start the timer
        the timer calls temperature control & stage check function

        stage_index: int;
        """
        if self.fermentation_steps:
            self.current_step_index = step_index
            step_settings = self.fermentation_steps[step_index]
            self.step_hours = float(step_settings['days'] * 24)
            self.step_target_temp = float(step_settings['temp'])
            if step_hours_left:
                self.elapsed_before_recovery = int((self.step_hours - float(step_hours_left)) * 3600)
            else:
                self.elapsed_before_recovery = 0
            self.start_time = utime.time()
            self.tim.deinit()
            utime.sleep_ms(100)
            self.tim.init(period=5000, mode=machine.Timer.PERIODIC, callback=self.job_queue)
        else:
            print('Load fermentation steps first!')

    def abort(self):
        self.tim.deinit()
        self.start_time = None
        self.is_completed = False
        self.elapsed_time = None
        self.fermenter_temp_ctrl.reset()
        self.recovery.remove_backup()
        print('Fermentation process has been terminated.')

    def has_started(self):
        """Check whether fermentation process is started or not
        
        Returns:
            [bool] -- [whether fermentation process is started or not]
        """
        if self.start_time:
            return True
        else:
            return False

    def has_loaded(self):
        """Check whether fermentation stages is loaded or not
        
        Returns:
            [bool] -- [whether fermentation stages is loaded or not]
        """

        if self.fermentation_steps:
            return True
        else:
            return False

    def has_completed(self):
        """Check whether fermentation has finished or not

        Returns:
            [bool] -- [whether fermentation has finished or not]
        """
        return self.is_completed

    def get_process_info(self):
        """
        get fermentation stage info, for API
        """
        is_heating = self.fermenter_temp_ctrl.heater.is_on()
        is_cooling = self.fermenter_temp_ctrl.cooler.is_on()
        wort_temp = self.fermenter_temp_ctrl.wort_sensor.read_temp()
        chamber_temp = self.fermenter_temp_ctrl.chamber_sensor.read_temp()
        # if fermentation in progress
        if self.has_started():
            machine_status = 'done' if self.is_completed else 'running'
            target_temp = round(self.step_target_temp, 1)
            total_steps = self.total_steps
            current_step = self.current_step_index + 1
            step_percentage = int((self.elapsed_time / (self.step_hours * 3600)) * 100)
            total_percentage = int((sum([step['days'] for step in self.fermentation_steps[:self.current_step_index]]) * 24 * 3600 + self.elapsed_time) / (sum([step['days'] for step in self.fermentation_steps]) * 24 * 3600) * 100)
            step_hours_left = round((self.step_hours * 3600 - self.elapsed_time) / 3600, 2)
            total_hours_left = round((sum([step['days'] for step in self.fermentation_steps[self.current_step_index:]]) * 24 * 3600 - self.elapsed_time) / 3600, 2)
            if step_percentage > 100:
                step_percentage = 100
            if total_percentage > 100:
                total_percentage = 100
            return {
                'machineStatus': machine_status,  # str
                'setTemp': target_temp,  # float
                'wortTemp': wort_temp,  # float
                'chamberTemp': chamber_temp,  # float
                'isHeating': is_heating,  # bool
                'isCooling': is_cooling,  # bool
                'beerName': self.beer_name,
                'fermentationSteps': self.fermentation_steps,
                'currentFermentationStepIndex': self.current_step_index,  # int
                'currentFermentationStep': current_step,  # int
                'totalFermentationStep': total_steps,  # int
                'stepHoursLeft': step_hours_left,  # float
                'totalHoursLeft': total_hours_left,  # float
                'currentFermentationStepPercentage': step_percentage,  # int
                'totalFermentationStepPercentage': total_percentage,  # int
                'hydrometerData': self.hydrometer_data
            }
        else:
            machine_status = 'standby'
            return {
                'machineStatus': machine_status,  # str
                'setTemp': 20.0,
                'wortTemp': wort_temp,
                'chamberTemp': chamber_temp,
                'isHeating': is_heating,  # bool
                'isCooling': is_cooling,  # bool
                'beerName': self.beer_name,
                'fermentationSteps': self.fermentation_steps,
                'currentFermentationStepIndex': None,
                'currentFermentationStep': None,
                'totalFermentationStep': None,
                'stepHoursLeft': None,
                'totalHoursLeft': None,
                'currentFermentationStepPercentage': None,
                'totalFermentationStepPercentage': None,
                'hydrometerData': self.hydrometer_data
            }
