import machine


class OneWireDevice:
    def __init__(self, pin):
        """
        Initialize the OW module
        :param pin: int; the pin number for OW devices
        """
        self._ow = machine.Onewire(pin)
        self._device_list = self._ow.scan()
        self._device_qty = len(self._device_list)
    
    def get_device_qty(self):
        """
        Return the qty of OW devices connecting to the OW pin
        return: int; the qty of the detected devices
        """
        return self._device_qty

    def get_device_list(self):
        """
        Return the list of the OW devices connected
        return: tuple; the detected device list
        """
        return self._device_list

class Ds18Sensor:
    def __init__(self, onewire_object, device_num):
        """
        Initialize the DS18 temperature sensor
        :param onewire_object: Class; the OneWireDevice instance
        :param device_num: int; Device Num of the DS18
        """
        self._ow = onewire_object
        if device_num + 1 > self._ow._device_qty:
            print('Device number not existed.')
            return
        else:
            self._ds = machine.Onewire.ds18x20(self._ow, device_num)
            self._device_num = device_num
    
    def get_realtime_temp(self):
        """
        Perform a measurement of the temperature and return the temperature
        :return: float; realtime temperature in Celsius measured by the DS18 sensor
        """
        temp = round(self._ds.convert_read(), 1)
        if isinstance(temp, float):
            return temp
        else:
            # in case of reading failure
            # deinit and re-init the ds18
            self._ds.deinit()
            self._ds = machine.Onewire.ds18x20(self._ow, self._device_num)
            return round(self._ds.convert_read(), 1)

    def read_temp(self):
        """
        Return the last measurement value of the temperature.  It's NOT a realtime measurement.
        :return: float;
        """
        return round(self._ds.read_temp(), 1)
