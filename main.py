import _thread

import esp
import logging
import machine
import uos
import ujson
import utime

from actuator import Actuator
from controltemp import FermenterTempControl
from crash_recovery import CrashRecovery
from fermenterpid import FermenterPID
from httpserver import HttpServer
from led import RgbLed
from logger import init_logger
from microDNSSrv import MicroDNSSrv
from mqtt_client import MQTT
from process import Process
from rtc import RealTimeClock
from tempsensor import Ds18Sensors, SingleTempSensor
from wifi import WiFi


logging.basicConfig(level=logging.INFO)
logger = init_logger(__name__)

# disable os debug info
esp.osdebug(None)

# get settings from JSON file
print('--------------------')
print('Loading settings and configurations...')

with open('hardware_config.json', 'r') as f:
    json = f.read()
config = ujson.loads(json)
print('File hardware_config.json has been loaded!')

with open('user_settings.json', 'r') as f:
    json = f.read()
settings = ujson.loads(json)
print('File user_settings.json has been loaded!')
print('--------------------')

# initialize and mount SD card, the front end GUI is stored in SD card
try:
    # try to mount SD card using MMC interface
    # for TTGO T8 some external 10K resistors are needed
    # see: https://github.com/micropython/micropython/issues/4722
    sd = machine.SDCard()
    uos.mount(sd, '/sd')
except Exception:
    # otherwise mount SD card using SPI
    print('Failed to mount the SD card using MMC, now attempting to mount with SPI.')
    sd = machine.SDCard(slot=2, mosi=15, miso=2, sck=14, cs=13)
    uos.mount(sd, '/sd')
    print('--------------------')
else:
    print('SD Card initialized and mounted')
    print('--------------------')

# initialize onewire devices
temp_sensors = Ds18Sensors(pin=config['onewire_pin'])
utime.sleep(1)
# initialize ds18 sensors
wort_sensor = SingleTempSensor(temp_sensors, device_number=settings['wortSensorDev'])  # the temp sensor measures wort temperature
utime.sleep(1)
chamber_sensor = SingleTempSensor(temp_sensors, device_number=settings['chamberSensorDev'])  # the temp sensor measures chamber temperature
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
led.set_color('magenta')  # LED初始化后设置为粉色
print('LED initialized')
print('--------------------')

# create a PID instance
pid = FermenterPID(kp=settings['pid']['kp'], ki=settings['pid']['ki'], kd=settings['pid']['kd'])
print('PID logic initialized')
print('--------------------')

# create a fermenter temp control instance
fermenter_temp_ctrl = FermenterTempControl(cooler, heater, wort_sensor, chamber_sensor, pid, led)
print('Temperature control logic initialized')
print('--------------------')

# create a timer for fermentation process
process_tim = machine.Timer(1)

# initialize the crash recovery
recovery = CrashRecovery()
print('Crash recovery initialized')
print('--------------------')


def measure_realtime_temps():
    """
    Measure wort temp & chamber temp in realtime
    This is a callback function which is called by a timer
    """
    while True:
        # get realtime temperature from sensors
        try:
            temp_sensors.get_realtime_temp()
        except:
            print('Error occurs when reading temperature')

        # update temperature readings every 2s
        utime.sleep_ms(2000)


# run measure temp function in a new thread
_thread.stack_size(7 * 1024)
print('Stack allocated')
temp_th = _thread.start_new_thread(measure_realtime_temps, ())
print('Thread task initialized')

rtc = RealTimeClock(tz=8, update_period=86400)
print('--------------------')
print('RTC initialized')

# Connect to WiFi (scan AP, and connect with password)
wifi = WiFi(rtc_obj=rtc)
print('--------------------')
print('WiFi initialized')
wifi.ap_start(settings['apSsid'])
print('AP started')
# get the AP IP of ESP32 itself, usually it's 192.168.4.1  
ap_ip_addr = wifi.get_ap_ip_addr()
print('AP IP: ' + ap_ip_addr)
# get the Station IP of ESP32 in the WLAN which ESP32 connects to
if settings['wifi'].get('ssid'):
    sta_ip_addr = wifi.sta_connect(settings['wifi']['ssid'], settings['wifi']['pass'], verify_ap=True)
    if sta_ip_addr:
        print('STA IP: ' + sta_ip_addr)
print('--------------------')
# print current local date & time
print(rtc.get_localdate())
print(rtc.get_localtime())
print('--------------------')

# initialize the MQTT module
mqtt = MQTT(settings)
print('MQTT initialized')
print('--------------------')

# initialize the fermentation process
main_process = Process(fermenter_temp_ctrl, process_tim, recovery, wifi, mqtt)
print('Main process logic initialized')
print('--------------------')

# Set up HTTP server
web = HttpServer(main_process, wifi, rtc, settings)
print('HTTP server initialized')
web.start()
utime.sleep(3)
if web.is_started():
    print('HTTP service started')
print('--------------------')
led.set_color('green')  # 初始化全部完成后设置为绿色，表示处于待机状态

# Set up DNS Server
if MicroDNSSrv.Create({'*': '192.168.4.1'}):
    print("DNS service started.")
else:
    print("Error to start MicroDNSSrv...")
print('--------------------')

# Check if the crash recovery is needed
if recovery.is_needed():
    print('Recovering the fermentation process...')
    print('--------------------')
    recovered_process_info = recovery.retrieve_backup()
    beer_name = recovered_process_info['beerName']
    fermentation_steps = recovered_process_info['fermentationSteps']
    current_step_index = recovered_process_info['currentFermentationStepIndex']
    step_hours_left = recovered_process_info['stepHoursLeft']
    hydrometer_data = recovered_process_info['hydrometerData']
    main_process.set_beer_name(beer_name)
    main_process.save_hydrometer_data(hydrometer_data)
    main_process.load_steps(fermentation_steps)
    main_process.start(step_index=current_step_index, step_hours_left=step_hours_left)
