import machine
import onewire
import ds18x20


# class RomCodeConvert:
#     @staticmethod
#     def _to_romcode_string(bytearray_romcode):
#         """
#         把bytearray格式的rom code转换为字符串格式
#         如：bytearray_romcode = bytearray(b'(\xaa4\xe4\x18\x13\x02;')
#         转换后为：'28 aa 34 e4 18 13 02 3b'
#         :param bytearray_romcode: bytearray
#         :return: str
#         """
#         import ubinascii
#         string_hex_list = [str(ubinascii.hexlify(bytes([el])), 'utf8') for el in bytearray_romcode]
#         romcode_str = ' '.join(string_hex_list)
#         return romcode_str
#
#     @staticmethod
#     def _to_romcode_bytearray(string_romcode):
#         """
#         把字符串格式的rom code转换为bytearray格式
#         如：string_romcode = '28 aa 34 e4 18 13 02 3b'
#         转换后为：bytearray(b'(\xaa4\xe4\x18\x13\x02;')
#         :param string_romcode: str
#         :return: bytearray
#         """
#         import ubinascii
#         string_hex_list = string_romcode.split()
#         bytes_list = [int.from_bytes(bytes(ubinascii.unhexlify(el)), 'big') for el in string_hex_list]
#         romcode_bytearray = bytearray(bytes_list)
#         return romcode_bytearray


class Ds18Sensors:
    def __init__(self, pin):
        """
        Initialize the DS18 temperature sensor
        :param onewire_object: Class; the OneWireDevice instance
        """
        self.ow = onewire.OneWire(machine.Pin(pin))
        self.ds = ds18x20.DS18X20(self.ow)
        self.device_list = None
        self.last_reading_available = False

    def get_device_list(self):
        self.device_list = self.ds.scan()
        return [
            {'value': device_number, 'label': hex(int.from_bytes(bytearray_romcode, ''))}
            for device_number, bytearray_romcode in enumerate(self.device_list)
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
        except:
            self.last_reading_available = False
        else:
            self.last_reading_available = True


class SingleTempSensor:
    def __init__(self, ds_obj, device_number):
        self.ds_obj = ds_obj
        self.update_device_num(device_number)

    def read_temp(self):
        if not self.ds_obj.last_reading_available:
            self.ds_obj.get_realtime_temp()
        if self.bytearray_romcode:
            try:
                temp = round(self.ds_obj.ds.read_temp(self.bytearray_romcode), 1)
            except Exception as e:
                print('The DS18 sensor was disconnected.  Check the wire.')
                return -99.9
            else:
                return temp
        else:
            return -99.9

    def update_device_num(self, new_device_number):
        if new_device_number + 1 <= self.ds_obj.get_device_qty():
            self.bytearray_romcode = self.ds_obj.device_list[new_device_number]
        else:
            self.bytearray_romcode = None
            print('Invalid Device Number!')

        self.ds_obj.last_reading_available = False
