import _thread

import machine
import network
import ujson
import utime

from actuator import Actuator
from controltemp import FermenterTempControl
from fermenterpid import FermenterPID
from httpserver import HttpServer
from led import RgbLed
from process import Process
from rtc import RealTimeClock
from tempsensor import OneWireDevice, Ds18Sensor
from wifi import WiFi

##################################   MACHINE HARDWARE CONFIG   #################################
# config = {
#     # GPio pin numbers
#     'onewire_pin': 25,
#     'cooler_pin': 18,
#     'heater_pin': 23,
#     'rgb_pins': {'r_pin': 2, 'g_pin': 0, 'b_pin': 4},
#     # Cooler on/off interval in seconds
#     'cooler_interval': 300,
#     # Heater on/off interval in seconds
#     'heater_interval': 0,
#     }
#################################################################################################


#######################################   USER SETTINGS   #######################################
# settings = {
#     'breweryName': '豚鼠精酿',
#     # Sensor device num
#     'wortSensorDev': 0,
#     'chamberSensorDev': 1,
#     # SSID for AP mode
#     'apSsid': 'Fermenter',
#     # ssid & password of AP (eg. a wireless router)
#     'wifi': {'ssid': '28#301', 'pass': '1318028301'},
#     }
#################################################################################################

# get settings from JSON file

with open('hardware_config.json', 'r') as f:
    json = f.read()
config = ujson.loads(json)
print('File hardware_config.json loaded!')

with open('user_settings.json', 'r') as f:
    json = f.read()
settings = ujson.loads(json)
print('File user_settings.json loaded!')
print('--------------------')

# change and save settings will overwrite the hardware_config.json file and reset the machine (machine.reset())
# only change and save the fermenting stages setting will NOT reset the machine, and will take effect immediately


# initialize onewire devices
ow = OneWireDevice(pin=config['onewire_pin'])
utime.sleep(1)
# initialize ds18 sensors
wort_sensor = Ds18Sensor(ow, device_num=settings['wortSensorDev'])  # the temp sensor measures wort temperature
utime.sleep(1)
chamber_sensor = Ds18Sensor(ow, device_num=settings['chamberSensorDev'])  # the temp sensor measures chamber temperature
utime.sleep(1)
print('DS18B20 sensors initialized')
print('--------------------')

# initialize the actuators
cooler = Actuator(pin=config['cooler_pin'], interval=config[
    'cooler_interval'])  # the compressor of the fridge needs at least 5min between on & off
print('Cooler initialized')
heater = Actuator(pin=config['heater_pin'],
                  interval=config['heater_interval'])  # the heater doesn't need an interval between on & off
print('Heater initialized')
print('--------------------')

# initialize the LED
led = RgbLed(r_pin=config['rgb_pins']['r_pin'], g_pin=config['rgb_pins']['g_pin'], b_pin=config['rgb_pins']['b_pin'])
led.set_color('pink')  # LED初始化后设置为粉色
print('LED initialized')
print('--------------------')

# create a PID instance
pid = FermenterPID()
print('PID logic initialized')
print('--------------------')

# create a fermenter temp control instance
fermenter_temp_ctrl = FermenterTempControl(cooler, heater, wort_sensor, chamber_sensor, pid, led)
print('Temperature control logic initialized')
print('--------------------')

# create a timer for fermentation process
process_tim = machine.Timer(1)

# initialize the fermentation process
main_process = Process(fermenter_temp_ctrl, process_tim)
print('Main process logic initialized')
print('--------------------')


def measure_realtime_temps():
    """
    Measure wort temp & chamber temp in realtime
    This is a callback function which is called by a timer
    """
    while True:
        # get realtime temperature from sensors
        try:
            wort_sensor.get_realtime_temp()
            chamber_sensor.get_realtime_temp()
        except:
            print('Error occurs when reading temperature')

        # update temperature readings every 2s
        utime.sleep_ms(2000)


# run measure temp function in a new thread
_thread.stack_size(7 * 1024)
print('Stack allocated')
temp_th = _thread.start_new_thread("temp", measure_realtime_temps, ())
print('Thread task initialized')

# 1. Connect to WiFi (scan AP, and connect with password)
wifi = WiFi()
print('--------------------')
print('WiFi initialized')
wifi.ap_start(settings['apSsid'])
print('AP started')
# get the AP IP of ESP32 itself, usually it's 192.168.4.1  
ap_ip_addr = wifi.get_ap_ip_addr()
print('AP IP: ' + ap_ip_addr)
# get the Station IP of ESP32 in the WLAN which ESP32 connects to
sta_ip_addr = wifi.sta_connect(settings['wifi']['ssid'], settings['wifi']['pass'])
if sta_ip_addr:
    print('STA IP: ' + sta_ip_addr)
print('--------------------')

rtc = RealTimeClock()
print('RTC initialized')
utime.sleep(5)
if wifi.is_connected():
    rtc.sync()
    print('RTC synced')
print('--------------------')

# Set up HTTP server
web = HttpServer(main_process, wifi, rtc, settings)
print('HTTP server initialized')
web.start()
print('HTTP service started')
print('--------------------')
led.set_color('green')  # 初始化全部完成后设置为绿色，表示处于待机状态

network.ftp.start(user="micro", password="python", buffsize=1024, timeout=300)
network.telnet.start(user="micro", password="python", timeout=300)
