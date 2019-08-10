import machine
import utime


class RealTimeClock:
    def __init__(self, tz=8):
        """
        初始化时钟
        :param tz: int； 与UTC的时差，如：北京时间为UTC+8
        """
        self.tz = int(tz)
        self.rtc = machine.RTC()
        self.is_updated = False
        self.retry_counter = 0

    def sync(self):
        """
        与时钟服务器进行同步
        :return: None
        """
        import ntptime
        try:
            ntptime.settime()
        except:
            if self.retry_counter < 5:
                self.retry_counter += 1
                print('Retrying #' + str(self.retry_counter))
                utime.sleep(1)
                self.sync()
            else:
                print('Failed to sync RTC')
                self.retry_counter = 0
        else:
            self.is_updated = True
            self.retry_counter = 0
            utc = self.rtc.datetime()
            self.rtc.datetime((utc[0], utc[1], utc[2], utc[3], utc[4] + self.tz, utc[5], utc[6], utc[7]))
            print('RTC Synced')

    def is_synced(self):
        return self.is_updated

    def get_localdate(self):
        """
        返回同步后的本地日期
        :return: str; "2019/7/25"
        """
        if not self.is_updated:
            self.sync()
        year, month, day, _, _, _, _, _ = self.rtc.datetime()
        return str(year) + '/' + str(month) + '/' + str(day)

    def get_localtime(self):
        """
        返回同步后的本地时间
        :return: str; "19:30"
        """
        if not self.is_updated:
            self.sync()
        _, _, _, _, hour, minute, _, _ = self.rtc.datetime()
        if minute < 10:
            minute = '0' + str(minute)
        return str(hour) + ':' + str(minute)
