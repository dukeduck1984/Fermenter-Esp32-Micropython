import ds18x20
import machine
import onewire

from logger import init_logger

logger = init_logger(__name__)


class RomCodeConvert:
    @staticmethod
    def from_romcode_to_hex_string(romcode_bytearray):
        """
        把bytearray格式的rom code转换为字符串格式
        如：romcode_bytearray = bytearray(b'(\xaa\xec\x01\x19\x13\x028')
        转换后为：'0x28aaec0119130238'
        :param romcode_bytearray: bytearray
        :return: str
        """
        romcode_int = int.from_bytes(romcode_bytearray, 'big')
        return hex(romcode_int)

    @staticmethod
    def from_hex_string_to_romcode(hex_string):
        """
        把字符串格式的rom code转换为bytearray格式
        如：hex_string = '0x28aaec0119130238'
        转换后为：bytearray(b'(\xaa\xec\x01\x19\x13\x028')
        :param hex_string: str
        :return: bytearray
        """
        romcode_int = int(hex_string, 0)
        return bytearray(romcode_int.to_bytes(8, 'big'))


class Ds18Sensors(RomCodeConvert):
    def __init__(self, pin):
        """
        Initialize the DS18 temperature sensor
        :param pin: int; GPIO for OneWire
        """
        self.ow = onewire.OneWire(machine.Pin(pin))
        self.ds = ds18x20.DS18X20(self.ow)
        self.device_list = None
        self.last_reading_available = False

    def get_device_list(self):
        self.device_list = self.ds.scan()
        return [
            {'value': self.from_romcode_to_hex_string(bytearray_romcode),
             'label': self.from_romcode_to_hex_string(bytearray_romcode)}
            for bytearray_romcode in self.device_list
        ]

    def get_device_qty(self):
        if not self.device_list:
            self.device_list = self.ds.scan()
        return len(self.device_list)
    
    def get_realtime_temp(self):
        """
        Perform a measurement of the temperature and return the temperature
        :return: float; realtime temperature in Celsius measured by the DS18 sensor
        """
        try:
            self.ds.convert_temp()
        except Exception as e:
            logger.exception(e, 'Failed to read temp from DS18B20 sensors.')
            self.last_reading_available = False
        else:
            self.last_reading_available = True


class SingleTempSensor(RomCodeConvert):
    def __init__(self, ds_obj, romcode_hex_string):
        self.romcode_hex_string = romcode_hex_string
        self.ds_obj = ds_obj
        self.is_connected = False
        self.bytearray_romcode = self.update_romcode(romcode_hex_string)

    def read_temp(self):
        if not self.ds_obj.last_reading_available:
            self.ds_obj.get_realtime_temp()
        try:
            temp = round(self.ds_obj.ds.read_temp(self.bytearray_romcode), 1)
        except Exception as e:
            if self.is_connected:
                logger.warning('DS18B20 ' + str(self.romcode_hex_string) + ' was disconnected.  Check the wire.')
            self.is_connected = False
            self.ds_obj.device_list = None
            return None
        else:
            self.is_connected = True
            return temp

    def update_romcode(self, new_romcode_hex_string):
        self.romcode_hex_string = new_romcode_hex_string
        self.ds_obj.last_reading_available = False
        try:
            new_romcode_bytearray = self.from_hex_string_to_romcode(new_romcode_hex_string)
        except Exception as e:
            logger.error('Invalid Romcode.')
            new_romcode_bytearray = None
        if new_romcode_bytearray and new_romcode_bytearray in self.ds_obj.ds.scan():
            self.is_connected = True
        else:
            self.is_connected = False
            logger.warning('DS18B20 ' + str(new_romcode_hex_string) + ' is not connected.')
        self.bytearray_romcode = new_romcode_bytearray
        return new_romcode_bytearray

    def isconnected(self):
        return self.is_connected
