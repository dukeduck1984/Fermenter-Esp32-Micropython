import utime
import machine


class Process:
    """
    Process.stage_run() -> start timer -> control temp & check progress -> start next stage -> end of final stage
    """
    def __init__(self, fermenter_temp_ctrl_obj, control_timer_obj):
        """
        Initialize the fermenter process
        :param fermenter_temp_ctrl_obj: Class; the instance of FermenterTempControl class
        :param control_timer_obj: Class; the instance of the Timer class
        """
        self.fermentation_stages = None
        self.fermenter_temp_ctrl = fermenter_temp_ctrl_obj
        self.tim = control_timer_obj
        self.total_stages = len(self.fermentation_stages) if self.fermentation_stages is not None else 0
        self.start_time = None
        self.elapsed_time = None


    def load_stages(self, fermentation_stages):
        """
        fermentation_stages: nested list; eg.[[stage0_hours, target temp], [stage1_hours, target temp], ...]
        """
        self.fermentation_stages = fermentation_stages


    def _fermenter_ctrl(self, t):
        """
        start fermenter temp control.
        This is a callback function run by a periodic timer
        """
        self.fermenter_temp_ctrl.run(self.stage_target_temp)
        self._stage_progress_check()


    def _stage_progress_check(self):
        """
        check the stage progress
        """
        now = utime.time()
        self.elapsed_time = now - self.start_time
        
        # if stage time is up
        if self.elapsed_time >= (self.stage_hours * 3600):
            # if this is not the final stage
            if self.current_stage_index < (self.total_stages - 1):
                # then proceed to next stage
                new_stage_index = self.current_stage_index + 1
                self.start(new_stage_index)
            # if this is the end of the final stage
            else:
                # maybe do something later...
                # TODO
                # send a message or email
                pass


    def start(self, stage_index=0):
        """
        pass stage index to get stage settings and start the timer
        the timer calls temperature control & stage check function

        stage_index: int;
        """
        if self.fermentation_stages:
            self.current_stage_index = stage_index
            stage_settings = self.fermentation_stages[stage_index]
            self.stage_hours = float(stage_settings[0])
            self.stage_target_temp = float(stage_settings[1])

            self.start_time = utime.time()

            self.tim.deinit()
            utime.sleep_ms(100)
            self.tim.init(period=5000, mode=machine.Timer.PERIODIC, callback=self._fermenter_ctrl)
        else:
            print('Load fermentation stages first!')


    def is_started(self):
        """Check whether fermentation process is started or not
        
        Returns:
            [bool] -- [whether fermentation process is started or not]
        """
        if self.start_time:
            return True
        else:
            return False


    def is_loaded(self):
        """Check whether fermentation stages is loaded or not
        
        Returns:
            [bool] -- [whether fermentation stages is loaded or not]
        """

        if self.fermentation_stages:
            return True
        else:
            return False

    def get_stage_info(self):
        """
        get fermentation stage info, for API or OLED
            target temperature: str; (eg. 19.6C')
            stage status: str; (eg. 1/3)
            complete percentage: str; (eg. 85%)
        return: tuple;(str, str, str)
        """
        # if fermentation in progress
        if self.start_time:
            target_temp = str(round(self.stage_target_temp, 1))
            stage_status = str(self.current_stage_index + 1) + '/' + str(self.total_stages)
            stage_percentage = int((self.elapsed_time / (self.stage_hours * 3600)) * 100)
            if stage_percentage > 100:
                stage_percentage = 100
            stage_percentage = str(stage_percentage) + '%'
        else:
            target_temp = "--.-"
            stage_status = 'N/A'
            stage_percentage = '---%'

        return target_temp, stage_status, stage_percentage

