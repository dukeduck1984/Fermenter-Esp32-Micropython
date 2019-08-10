import utime
import machine


class Process:
    """
    Process.stage_run() -> start timer -> control temp & check progress -> start next stage -> end of final stage
    """
    def __init__(self, fermenter_temp_ctrl_obj, control_timer_obj, crash_recovery_obj):
        """
        Initialize the fermenter process
        :param fermenter_temp_ctrl_obj: Class; the instance of FermenterTempControl class
        :param control_timer_obj: Class; the instance of the Timer class
        """
        self.beer_name = None
        self.fermentation_steps = None
        self.fermenter_temp_ctrl = fermenter_temp_ctrl_obj
        self.tim = control_timer_obj
        self.backup_tim = machine.Timer(2)
        self.recovery = crash_recovery_obj
        self.total_steps = len(self.fermentation_steps) if self.fermentation_steps is not None else 0
        self.start_time = None
        self.elapsed_time = None
        self.is_completed = False
        self.current_step_index = None
        self.step_hours = None
        self.step_target_temp = None

    def set_beer_name(self, beer_name):
        self.beer_name = beer_name

    def load_steps(self, fermentation_steps):
        """
        fermentation_stages: nested list; eg.[{'days': 2, 'temp': 18.6}, {'days': 14, 'temp': 21.5}, ..., {'days': 5, 'temp': 23.0}]
        """
        self.fermentation_steps = fermentation_steps
        self.total_steps = len(self.fermentation_steps)

    def _fermenter_ctrl(self, t):
        """
        start fermenter temp control.
        This is a callback function run by a periodic timer
        """
        self.fermenter_temp_ctrl.run(self.step_target_temp)
        self._step_progress_check()

    def _step_progress_check(self):
        """
        check the stage progress
        """
        now = utime.time()
        self.elapsed_time = now - self.start_time
        
        # if stage time is up
        if self.elapsed_time >= (self.step_hours * 3600):
            # if this is not the final stage
            if self.current_step_index < (self.total_steps - 1):
                # then proceed to next stage
                new_step_index = self.current_step_index + 1
                self.start(step_index=new_step_index)
            # if this is the end of the final stage
            else:
                self.start_time = None
                self.is_completed = True
                self.fermenter_temp_ctrl.job_done = True
                self.fermenter_temp_ctrl.led.set_color('orange')
                self.backup_tim.deinit()
                self.recovery.remove_backup()
                print('All fermentation stages have completed.')
                # the periodic timer is still running to maintain the temperature control

    def _process_backup(self):
        self.backup_tim.deinit()
        recovery = self.recovery
        get_process_info = self.get_process_info
        def backup_cb(t):
            recovery.backing_up(get_process_info())
        self.backup_tim.init(period=297000, mode=machine.Timer.PERIODIC, callback=backup_cb)

    def start(self, step_index=0, recovered_hours_to_go=None):
        """
        pass stage index to get stage settings and start the timer
        the timer calls temperature control & stage check function

        stage_index: int;
        """
        if self.fermentation_steps:
            self.current_step_index = step_index
            step_settings = self.fermentation_steps[step_index]
            if recovered_hours_to_go:
                self.step_hours = float(recovered_hours_to_go)
            else:
                self.step_hours = float(step_settings['days'] * 24)
            self.step_target_temp = float(step_settings['temp'])

            self.start_time = utime.time()

            self.tim.deinit()
            utime.sleep_ms(100)
            self.tim.init(period=5000, mode=machine.Timer.PERIODIC, callback=self._fermenter_ctrl)
            # begin the process backup
            self._process_backup()
        else:
            print('Load fermentation steps first!')

    def abort(self):
        self.tim.deinit()
        self.backup_tim.deinit()
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
                'setTemp': target_temp, # float
                'wortTemp': wort_temp, # float
                'chamberTemp': chamber_temp, # float
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
            }
        else:
            machine_status = 'standby'
            return {
                'machineStatus': machine_status,  # str
                'setTemp': None,
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
            }
