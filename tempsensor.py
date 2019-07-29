import machine


class OneWireDevice:
    def __init__(self, pin):
        """
        Initialize the OW module
        :param pin: int; the pin number for OW devices
        """
        self.onewire_bus = machine.Onewire(pin)
        self._device_list = None
        self._device_qty = None

    def get_onewire_bus(self):
        return self.onewire_bus
    
    def get_device_qty(self):
        """
        Return the qty of OW devices connecting to the OW pin
        return: int; the qty of the detected devices
        """
        self._device_qty = len(self.onewire_bus.scan())
        return self._device_qty

    def get_device_list(self):
        """
        Return the list of the OW devices connected
        return: list; the detected device list
                eg.[
                {'value': 0, 'label': '6e000000c86a8e28'},
                {'value': 1, 'label': '02000000c82a8928'}
                ]
        """
        self._device_list = self.onewire_bus.scan()
        return [
            {'value': device_number, 'label': rom_code}
            for device_number, rom_code in enumerate(self._device_list)
        ]

class Ds18Sensor:
    def __init__(self, onewire_object, device_num):
        """
        Initialize the DS18 temperature sensor
        :param onewire_object: Class; the OneWireDevice instance
        :param device_num: int; Device Num of the DS18
        """
        self.ow = onewire_object
        self.is_ready = False
        self.last_reading_available = False
        try:
            self._ds = machine.Onewire.ds18x20(self.ow.get_onewire_bus(), device_num)
        except:
            print('Invalid Device Number.')
        else:
            self._device_num = device_num
            self.is_ready = True

    def get_rom_code(self):
        """
        :return: str; the Rom Code in Hex string of the DS18 device
        """
        if self.is_ready:
            return self._ds.rom_code()
        else:
            return 'Sensor Error.'
    
    def get_realtime_temp(self):
        """
        Perform a measurement of the temperature and return the temperature
        :return: float; realtime temperature in Celsius measured by the DS18 sensor
        """

        if self.is_ready:
            temp = round(self._ds.convert_read(), 1)
            if isinstance(temp, float):
                self.last_reading_available = True
                return temp
            else:
                # in case of reading failure
                # deinit and re-init the ds18
                self._ds.deinit()
                self._ds = machine.Onewire.ds18x20(self.ow.get_onewire_bus(), self._device_num)
                self.last_reading_available = True
                return round(self._ds.convert_read(), 1)
        else:
            return -99.9

    def read_temp(self):
        """
        Return the last measurement value of the temperature.  It's NOT a realtime measurement.
        :return: float;
        """
        if self.last_reading_available:
            return round(self._ds.read_temp(), 1)
        else:
            return self.get_realtime_temp()

    def update_device_num(self, new_device_num):
        """
        Update sensor device number
        :param new_device_num: int; device number
        :return: None
        """
        self._ds.deinit()
        try:
            self._ds = machine.Onewire.ds18x20(self.ow.get_onewire_bus(), new_device_num)
        except:
            print('Invalid Device Number.')
        else:
            self._device_num = new_device_num
            self.last_reading_available = False
            self.is_ready = True
