import network
import utime


class WiFi:
    def __init__(self):
        self.ap_ip_addr = None
        self.sta_ip_addr = None
        self.ap = network.WLAN(network.AP_IF)  # Start AP mode
        self.sta = network.WLAN(network.STA_IF)  # Start STA mode
        utime.sleep_ms(200)
        self.sta.active(True)

    def ap_start(self, ssid):
        """
        :param ssid: str; ESSID for the AP
        :return: str; IP address of the ESP32 AP
        """
        # Initialize the network
        self.ap.active(True)  # activate the AP interface
        utime.sleep_ms(200)
        self.ap.config(essid=ssid)
        #self.ap.config(essid=ssid + self.machine_id)  # set ssid
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

    def scan_wifi_list(self):
        """
        Scan and return a list of available Access Points
        return: list;
        """
        scanned_wifi = self.sta.scan()
        wifi_list = [str(wifi[0], 'utf8') for wifi in scanned_wifi]
        return wifi_list

    def sta_connect(self, ap_ssid, ap_pass):
        """
        Connect to an Access Point by its SSID and Password
        return: string; the IP of the STA
        """
        # TODO: 一旦密码输错，会无线循环尝试重新连接，需要修正
        try:
            self.sta.connect(ap_ssid, ap_pass)
        except:
            pass
        else:
            utime.sleep(2)
            return self.get_sta_ip_addr()

    def is_connected(self):
        return self.sta.isconnected()
