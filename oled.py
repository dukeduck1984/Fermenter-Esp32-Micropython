import machine

class OLED:
    def __init__(self, scl_pin, sda_pin):
        from ssd1306 import SSD1306_I2C
        import freesans20
        from writer import Writer

        WIDTH = const(128)
        HEIGHT = const(64)

        i2c = machine.I2C(scl=scl_pin, sda=sda_pin, speed=400000)
        ssd = SSD1306_I2C(WIDTH, HEIGHT, i2c)

        wri = Writer(ssd, freesans20, verbose=True)
        Writer.set_clip(True, True)

        self.Writer = Writer
        self.wri = wri
        self.ssd = ssd

    def show(self, text_dict):
        line1 = str(text_dict.get('line1'))
        line2 = str(text_dict.get('line2'))
        line3 = str(text_dict.get('line3'))

        self.Writer.set_textpos(3, 0)
        self.wri.printstring(line1)
        self.Writer.set_textpos(23, 0)
        self.wri.printstring(line2)
        self.Writer.set_textpos(43, 0)
        self.wri.printstring(line3)

        self.ssd.fill(0) # clear the screen
        self.ssd.show()
