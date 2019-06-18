from actuator import Actuator
from fermenterpid import FermenterPID
from led import RgbLed
from oled import OLED
from tempsensor import OneWireDevice, Ds18Sensor
from controltemp import FermenterTempControl
from httpserver import HttpServer
from process import Process
from wifi import WiFi
import gc
import machine
import network
import utime
import ujson
import _thread



##################################   MACHINE SETTINGS   ########################################
# 
settings = {
    # GPio pin numbers
    'onewire_pin': 25,
    'cooler_pin': 20,
    'heater_pin': 23,
    'rgb_pins': {'r_pin': 13, 'g_pin': 14, 'b_pin': 15},
    'oled_i2c_pins': {'scl': 22, 'sda': 21},
    # Sensor device num
    'wort_sensor_dev': 0,
    'chamber_sensor_dev': 1,
    # Cooler on/off interval in seconds
    'cooler_interval': 300,
    # Heater on/off interval in seconds
    'heater_interval': 0,
    # SSID for AP mode
    'ap_ssid': 'Fermenter', 
    # ssid & password of AP (eg. a wireless router)
    'wifi': {'ssid': '28#301', 'pass': '50047501'},
    # Fermenting Stages, eg. [[stage0_hours, target temp], [stage1_hours, target temp], ...]
    'fermenting_stages': [[24, 18.5], [288, 19.6], [48, 20.5]],
    }
#
#################################################################################################

# TODO
# get settings from JSON file
#
# with open('config.json', 'r') as f:
#     json = f.read()
# settings = ujson.loads(json)
#
# change and save settings will overwrite the config.json file and reset the machine (machine.reset())
# only change and save the fermenting stages setting will NOT reset the machine, and will take effect immediately
#



# initialize onewire devices
ow = OneWireDevice(pin=settings['onewire_pin'])

# initialize ds18 sensors
wort_sensor = Ds18Sensor(ow, device_num=settings['wort_sensor_dev'])  # the temp sensor measures wort temperature
chamber_sensor = Ds18Sensor(ow, device_num=settings['chamber_sensor_dev'])  # the temp sensor measures chamber temperature

# initialize the actuators
cooler = Actuator(pin=settings['cooler_pin'], interval=settings['cooler_interval'])  # the compressor of the fridge needs at least 5min between on & off
heater = Actuator(pin=settings['heater_pin'], interval=settings['heater_interval'])  # the heater doesn't need an interval between on & off

# initialize the LED
led = RgbLed(r_pin=settings['rgb_pins']['r_pin'], g_pin=settings['rgb_pins']['g_pin'], b_pin=settings['rgb_pins']['b_pin'])

# initialize the OLED sceen
oled = OLED(scl_pin=settings['oled_i2c_pins']['scl'], sda_pin=settings['oled_i2c_pins']['sda'])

# create a PID instance
pid = FermenterPID()

# create a fermenter temp control instance
fermenter_temp_ctrl = FermenterTempControl(cooler, heater, wort_sensor, chamber_sensor, pid, led)

# create a timer for fermentation process
process_tim = machine.Timer(1)

# initialize the fermentation process
main_process = Process(fermenter_temp_ctrl, process_tim)

# connect wifi
wifi = WiFi()
wifi.ap_start(settings['ap_ssid'])
ap_ip_addr = wifi.get_ap_ip_addr()  # get IP address for AP mode



# wort and chamber temps for API and OLED
wort_realtime_temp = 0
chamber_realtime_temp = 0


def measure_show_temps():
    """
    Measure wort temp & chamber temp in realtime, and update global temp variables
    Show info on the OLED screen

    This is a callback function which is called by a timer
    """
    while True:
        gc.collect()

        global wort_realtime_temp
        global chamber_realtime_temp

        # get realtime temperature from sensors and pass to global variables
        wort_realtime_temp = wort_sensor.get_realtime_temp()
        chamber_realtime_temp = chamber_sensor.get_realtime_temp()
        
        # get fermentation stage info from process module
        target_temp, stage_status, stage_percentage = main_process.get_stage_info()

        # format the text to be displayed on OLED screen
        text = {
            'line1': 'Wort: ' + str(wort_realtime_temp) + 'c              ',
            'line2': 'Chamb: ' + str(chamber_realtime_temp) + 'c             ',
            'line3': target_temp + 'c' + '|' + stage_status + '|' + stage_percentage + '             ',
        }
        oled.show(text)
        
        # update temperature readings every 2s
        utime.sleep_ms(2000)


# run measure temp & OLED display function in a new thread
_thread.stack_size(7*1024)
oled_th = _thread.start_new_thread("OLED", measure_show_temps, ())




# load the fermentation stages
#main_process.load_stages(settings['fermenting_stages'])

# start the fermenting process
#main_process.start()



# 1. Connect to WiFi (scan AP, and connect with password)
wifi = WiFi()
wifi.ap_start(settings['ap_ssid'])
# get the AP IP of ESP32 itself, usually it's 192.168.4.1  
ap_ip_addr = wifi.get_ap_ip_addr()
# get the Station IP of ESP32 in the WLAN which ESP32 connects to
sta_ip_addr = wifi.sta_connect(settings['wifi']['ssid'], settings['wifi']['pass'])

# TODO
# 2. Set up the MQTT client
# 3. Publish fermentation data: 
#        wort_realtime_temp, chamber_realtime_temp, 
#        target wort temp, stage status, complete percentage
#        specific gravity


# Set up HTTP server
web = HttpServer(main_process)
web.start()

# TODO
# Build the control UI


