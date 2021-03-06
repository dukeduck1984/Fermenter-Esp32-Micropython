import machine
import usocket
import ustruct
import utime

from logger import init_logger

logger = init_logger(__name__)


class RealTimeClock:
    # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
    NTP_DELTA = 3155673600
    hosts = [
        'ntp.aliyun.com',
        'ntp.ntsc.ac.cn',
        'time1.cloud.tencent.com',
        'pool.ntp.org',
    ]

    def __init__(self, tz=8, update_period=0):
        """
        初始化时钟
        :param tz: int； 与UTC的时差，如：北京时间为UTC+8
        :param update_period: int； 与ntp服务器同步的频率，以秒计，如period=86400为每24小时同步一次
                                    小于300秒只同步一次
        """
        self.tz = int(tz)
        self.rtc = machine.RTC()
        self.retry_counter = 0
        self.period_ms = update_period * 1000
        self.last_time = None
        self.rtc_tim = None

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

    def _ntp_sync(self):
        """
        与时钟服务器进行同步
        :return: None
        """
        try:
            self._settime()
        except Exception as e:
            if self.retry_counter < 1:
                self.retry_counter += 1
                logger.debug('Retrying to connect to the ntp server...')
                utime.sleep(1)
                self.sync()
            else:
                logger.debug('Failed to sync RTC')
                self.retry_counter = 0
        else:
            self.last_time = utime.ticks_ms()
            self.retry_counter = 0
            utc = self.rtc.datetime()
            self.rtc.datetime((utc[0], utc[1], utc[2], utc[3], utc[4] + self.tz, utc[5], utc[6], utc[7]))
            logger.debug('RTC Synced')

    def sync(self):
        self._ntp_sync()
        if self.period_ms >= 300000 and not self.rtc_tim:
            this = self
            def rtc_tim_cb(t):
                import _thread
                rtc_th = _thread.start_new_thread(this._ntp_sync, ())
            self.rtc_tim = machine.Timer(-1)
            self.rtc_tim.init(period=self.period_ms, mode=machine.Timer.PERIODIC, callback=rtc_tim_cb)

    def is_synced(self):
        return self.last_time is not None

    def get_localdate(self):
        """
        返回同步后的本地日期
        :return: str; "2019/7/25"
        """
        year, month, day, _, _, _, _, _ = self.rtc.datetime()
        return str(year) + '/' + str(month) + '/' + str(day)

    def get_localtime(self):
        """
        返回同步后的本地时间
        :return: str; "19:30"
        """
        _, _, _, _, hour, minute, _, _ = self.rtc.datetime()
        if minute < 10:
            minute = '0' + str(minute)
        return str(hour) + ':' + str(minute)
