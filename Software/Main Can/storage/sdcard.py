import os
import machine

class SDCard:
    def __init__(self, spi_bus, cs_pin):
        print("a1")
        self.cs = machine.Pin(cs_pin, machine.Pin.OUT)
        print("a2")
        self.spi = machine.SPI(spi_bus, baudrate=1000000, polarity=0, phase=0, sck=machine.Pin(36), mosi=machine.Pin(35), miso=machine.Pin(37))
        print("a3")
        # Ensure the SPI pins (SCK, MOSI, MISO) are defined according to your board's pinout.
        print("a4")
        self.sd = machine.SDCard(self.cs)
        print("a5")
        self.vfs = os.VfsFat(self.sd)
        print("a6")
        os.mount(self.vfs, "/sd")

    def write_file(self, filename, data):
        """Write data to a file on the SD card."""
        path = '/sd/' + filename
        with open(path, 'w') as file:
            file.write(data)

    def read_file(self, filename):
        """Read data from a file on the SD card."""
        path = '/sd/' + filename
        with open(path, 'r') as file:
            return file.read()

    def list_files(self):
        """List all files in the root directory of the SD card."""
        return os.listdir('/sd')