import _thread

import esp
import machine
import uos
import ujson
import utime


# disable os debug info
esp.osdebug(None)

# initialize and mount SD card, the front end GUI is stored in SD card
try:
    # try to mount SD card using MMC interface
    # for TTGO T8 some external 10K resistors are needed
    # see: https://github.com/micropython/micropython/issues/4722
    sd = machine.SDCard()
    uos.mount(sd, '/sd')
except Exception as e:
    # otherwise mount SD card using SPI
    print('Failed to mount the SD card using MMC, now attempting to mount with SPI.')
    try:
        sd = machine.SDCard(slot=2, mosi=15, miso=2, sck=14, cs=13)
        uos.mount(sd, '/sd')
    except Exception as e:
        print('Failed to mount the SD with SPI.')
        print('--------------------')
else:
    print('SD Card initialized and mounted')
    print('--------------------')


# import below modules after the SD card has been mounted
# in order to allow the log file to be created in the SD card.
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


# initialize logger for this module
logger = init_logger(__name__)

# get settings from JSON file
logger.debug('Loading hardware configurations...')
with open('hardware_config.json', 'r') as f:
    json = f.read()
config = ujson.loads(json)

logger.debug('Loading user settings...')
with open('user_settings.json', 'r') as f:
    json = f.read()
settings = ujson.loads(json)

OW_PIN = config['onewire_pin']
COOLER_PIN = config['cooler_pin']
HEATER_PIN = config['heater_pin']
LED_R_PIN = config['rgb_pins']['r_pin']
LED_G_PIN = config['rgb_pins']['g_pin']
LED_B_PIN = config['rgb_pins']['b_pin']
SSD1306_SCL_PIN = config['ssd1306_pins']['scl_pin']
SSD1306_SDA_PIN = config['ssd1306_pins']['sda_pin']
COOLER_INTERVAL = config['cooler_interval']
HEATER_INTERVAL = config['heater_interval']

# initialize the LED
logger.debug('Initializing RgbLED...')
led = RgbLed(r_pin=LED_R_PIN, g_pin=LED_G_PIN, b_pin=LED_B_PIN)
led.set_color('magenta')  # LED初始化后设置为粉色

# initialize onewire devices
logger.debug('Initializing DS18B20 sensors...')
temp_sensors = Ds18Sensors(pin=OW_PIN)
utime.sleep(1)
# initialize ds18 sensors
wort_sensor = SingleTempSensor(temp_sensors, settings['wortSensorDev'])
utime.sleep(1)
chamber_sensor = SingleTempSensor(temp_sensors, settings['chamberSensorDev'])

# initialize the actuators
logger.debug('Initializing Cooler...')
cooler = Actuator(pin=COOLER_PIN,
                  interval=COOLER_INTERVAL)  # the compressor of the fridge needs at least 5min between on & off
logger.debug('Initializing Heater...')
heater = Actuator(pin=HEATER_PIN,
                  interval=HEATER_INTERVAL)  # the heater doesn't need an interval between on & off

# create a PID instance
logger.debug('Initializing PID controller...')
pid = FermenterPID(kp=settings['pid']['kp'], ki=settings['pid']['ki'], kd=settings['pid']['kd'])

# create a fermenter temp control instance
logger.debug('Initializing temperature control logic...')
fermenter_temp_ctrl = FermenterTempControl(cooler, heater, wort_sensor, chamber_sensor, pid, led)

# create a timer for fermentation process
process_tim = machine.Timer(1)

# initialize the crash recovery
logger.debug('Initializing crash recovery mechanism...')
recovery = CrashRecovery()


def measure_realtime_temps():
    """
    Measure wort temp & chamber temp in realtime
    This is a callback function which is called by a timer
    """
    while True:
        # get realtime temperature from sensors
        temp_sensors.get_realtime_temp()
        # update temperature readings every 2s
        utime.sleep_ms(2000)


# run measure temp function in a new thread
logger.debug('Allocating stack for thread task...')
_thread.stack_size(7 * 1024)
temp_th = _thread.start_new_thread(measure_realtime_temps, ())

logger.debug('Initializing RTC...')
rtc = RealTimeClock(tz=8, update_period=86400)

# Connect to WiFi (scan AP, and connect with password)
logger.debug('Initializing WiFi...')
wifi = WiFi(rtc_obj=rtc)
wifi.ap_start(settings['apSsid'])
# get the AP IP of ESP32 itself, usually it's 192.168.4.1  
ap_ip_addr = wifi.get_ap_ip_addr()
logger.debug('AP IP address: ' + ap_ip_addr)
# get the Station IP of ESP32 in the WLAN which ESP32 connects to
if settings['wifi'].get('ssid'):
    sta_ip_addr = wifi.sta_connect(settings['wifi']['ssid'], settings['wifi']['pass'], verify_ap=True)
    if sta_ip_addr:
        logger.debug('STA IP address: ' + sta_ip_addr)
# print current local date & time
logger.debug('Date: ' + rtc.get_localdate())
logger.debug('Time: ' + rtc.get_localtime())

# initialize the MQTT module
logger.debug('Initializing MQTT...')
mqtt = MQTT(settings)

# initialize the fermentation process
logger.debug('Initializing main process logic...')
main_process = Process(fermenter_temp_ctrl, process_tim, recovery, wifi, mqtt)

# Set up HTTP server
logger.debug('Initializing Web server...')
web = HttpServer(main_process, wifi, rtc, settings)
web.start()
utime.sleep(3)
if web.is_started():
    logger.debug('HTTP service has started.')
led.set_color('green')  # 初始化全部完成后设置为绿色，表示处于待机状态

# Set up DNS Server
logger.debug('Initializing DNS...')
if MicroDNSSrv.Create({'*': '192.168.4.1'}):
    logger.debug("DNS service has started.")
else:
    logger.debug("Failed to start DNS service...")

# Check if the crash recovery is needed
if recovery.is_needed():
    logger.debug('Recovering the fermentation process...')
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
