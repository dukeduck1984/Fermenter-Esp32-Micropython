import machine
import usocket
import ustruct
import utime


class RealTimeClock:
    # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
    NTP_DELTA = 3155673600
    hosts = [
        'ntp.aliyun.com',
        'ntp.ntsc.ac.cn',
        'time1.cloud.tencent.com',
        'pool.ntp.org',
    ]
    def __init__(self, tz=8):
        """
        初始化时钟
        :param tz: int； 与UTC的时差，如：北京时间为UTC+8
        """
        self.tz = int(tz)
        self.rtc = machine.RTC()
        self.is_updated = False
        self.retry_counter = 0

    def _time(self):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1b
        s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        s.settimeout(1)
        for host in RealTimeClock.hosts:
            try:
                addr = usocket.getaddrinfo(host, 123)[0][-1]
                res = s.sendto(NTP_QUERY, addr)
                msg = s.recv(48)
            except:
                pass
            else:
                s.close()
                val = ustruct.unpack("!I", msg[40:44])[0]
                return val - RealTimeClock.NTP_DELTA

    def _settime(self):
        t = self._time()
        if t:
            tm = utime.localtime(t)
            tm = tm[0:3] + (0,) + tm[3:6] + (0,)
            self.rtc.datetime(tm)
        else:
            raise Exception('Error: failed to connect to ntp servers.')

    def sync(self):
        """
        与时钟服务器进行同步
        :return: None
        """
        try:
            self._settime()
        except:
            if self.retry_counter < 1:
                self.retry_counter += 1
                print('Retrying...')
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
