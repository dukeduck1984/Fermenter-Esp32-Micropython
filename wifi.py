import network
import utime

from logger import init_logger

logger = init_logger(__name__)


class WiFi:
    def __init__(self, rtc_obj=None):
        self.ap_ip_addr = None
        self.sta_ip_addr = None
        self.ap = network.WLAN(network.AP_IF)  # Start AP mode
        self.sta = network.WLAN(network.STA_IF)  # Start STA mode
        utime.sleep_ms(200)
        self.sta.active(True)
        self.ssid = None
        self.pwd = None
        self.rtc = rtc_obj

    def ap_start(self, ssid):
        """
        :param ssid: str; ESSID for the AP
        :return: str; IP address of the ESP32 AP
        """
        # Initialize the network
        self.ap.active(True)  # activate the AP interface
        utime.sleep_ms(200)
        self.ap.config(essid=ssid)
        # self.ap.config(essid=ssid + self.machine_id)  # set ssid
        utime.sleep_ms(200)
        return self.get_ap_ip_addr()

    def get_ap_ip_addr(self):
        """
        Return IP address in AP mode
        """
        if self.ap.active():
            self.ap_ip_addr = self.ap.ifconfig()[0]  # get AP (ESP32 itself) IP address
            return self.ap_ip_addr
        else:
            return None

    def get_sta_ip_addr(self):
        """
        Return IP address in STA mode if connected to an AP
        """
        if self.sta.isconnected():
            self.sta_ip_addr = self.sta.ifconfig()[0]
            return self.sta_ip_addr
        else:
            return None

    def get_sta_ssid(self):
        if self.sta.isconnected():
            return self.sta.config('essid')
        else:
            return None

    def scan_wifi_list(self):
        """
        Scan and return a list of available Access Points
        return: list;
        """
        scanned_wifi = self.sta.scan()
        wifi_list = [str(wifi[0], 'utf8') for wifi in scanned_wifi]
        return list(set(wifi_list))

    def verify_ap(self, ap_ssid):
        return ap_ssid in self.scan_wifi_list()

    def sync_rtc(self):
        if self.rtc:
            self.rtc.sync()

    def sta_connect(self, ap_ssid, ap_pass, verify_ap=False):
        """
        Connect to an Access Point by its SSID and Password
        return: string; the IP of the STA
        """
        # Attempt connection only if SSID can be found
        if verify_ap:
            if not self.verify_ap(ap_ssid):
                logger.debug('Network "' + ap_ssid + '" does not present')
                return None
        # Disconnect current wifi network
        if self.sta.isconnected():
            logger.debug('Disconnecting from current network...')
            self.sta.disconnect()
            utime.sleep(1)
            self.sta.active(False)
            utime.sleep_ms(200)
            self.sta.active(True)
            utime.sleep_ms(100)
        start = utime.ticks_ms()
        timeout = 12000  # set timeout to 12s
        while not self.sta.isconnected():
            if utime.ticks_diff(utime.ticks_ms(), start) > timeout:
                logger.debug('Connecting to "' + ap_ssid + '" Timeout')
                if self.ssid and self.pwd:
                    logger.debug('Restore the connection with "' + self.ssid + '"')
                    try:
                        self.sta_connect(self.ssid, self.pwd)
                    except:
                        pass
                else:
                    return None
                break
            logger.debug('Connecting to "' + ap_ssid + '"...')
            self.sta.connect(ap_ssid, ap_pass)
            while not self.sta.isconnected() and utime.ticks_diff(utime.ticks_ms(), start) < timeout:
                logger.debug('Connecting...')
                utime.sleep_ms(2000)
        else:
            logger.debug('Network "' + ap_ssid + '" Connected!')
            # if successfully connected, store the SSID & Password
            self.ssid = ap_ssid
            self.pwd = ap_pass
            # sync RTC with NTP servers
            self.sync_rtc()
            return self.get_sta_ip_addr()

    def is_connected(self):
        return self.sta.isconnected()
