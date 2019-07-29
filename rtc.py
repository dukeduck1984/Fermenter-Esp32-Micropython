import machine
import utime


class RealTimeClock:
    def __init__(self, ntp_server='1.cn.pool.ntp.org',tz='HKT-8'):
        """
        初始化时钟
        :param ntp_server: str; 时钟服务器地址
        :param tz: str； 时区
        """
        self.server = ntp_server
        self.tz = tz
        self.rtc = machine.RTC()
        self.retry_counter = 0

    def sync(self):
        """
        与时钟服务器进行同步，并且每1820秒重复一次同步
        :return: None
        """
        self.rtc.ntp_sync(server=self.server, tz=self.tz)
        utime.sleep(1)
        if self.is_synced():
            self.retry_counter = 0
        else:
            while self.retry_counter < 5:
                self.retry_counter += 1
                self.sync()


    def is_synced(self):
        """
        检查是否成功与时钟服务器同步
        :return: bool
        """
        return self.rtc.synced()

    def get_localdate(self):
        """
        返回同步后的本地日期
        :return: str; "2019/7/25"
        """
        year, month, day, _, _, _, _, _ = self.rtc.now()
        return str(year) + '/' + str(month) + '/' + str(day)

    def get_localtime(self):
        """
        返回同步后的本地时间
        :return: str; "19:30"
        """
        _, _, _, hour, min, _, _, _ = self.rtc.now()
        return str(hour) + ':' + str(min)
