import machine


class OneWireDevice:
    def __init__(self, pin):
        self._ow = machine.Onewire(pin)
        self._device_list = self._ow.scan()
        self._device_qty = len(self._device_list)
    
    def get_device_qty(self):
        """
        return: int; the qty of the detected devices
        """
        return self._device_qty

    def get_device_list(self):
        """
        return: tuple; the detected device list
        """
        return self._device_list

class Ds18Sensor:
    def __init__(self, onewire_object, device_num):
        """
        Initialize the DS18 sensor
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
        return: float; the measured temperature in Celsius
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
        return last measured temp, not realtime
        """
        return round(self._ds.read_temp(), 1)

