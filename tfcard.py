import machine
import uos


"""
https://github.com/micropython/micropython/issues/4722

    If you want to get back to the current, main-line Micropython instead of the LoBoris fork
    you should try recompiling from the current master branch. Since the merger of #4772 into
    these is support for the built-in SD card driver hardware, which is much faster than
    using an SPI interface and the Python sdcard module. 
    On the TTGO T8 all you should need is:
"""
sd = machine.SDCard(slot=2, mosi=15, miso=2, sck=14, cs=13)
uos.mount(sd, '/sd')

# uos.mount(machine.SDCard(), "/sd")

# Below code works for Loboris fork for TTGO ESP32
# uos.sdconfig(uos.SDMODE_1LINE)
# uos.mountsd()

# https://github.com/micropython/micropython/issues/4848
# The m5stack has the SD card wired to non-standard pins. See the documentation for details.
# For the TL;DR, try using:
# machine.SDCard(slot=2, mosi=23, miso=19, sck=18, cs=4)
