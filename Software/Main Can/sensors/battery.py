from machine import I2C, Pin
import time

class MAX17048:
    # I2C address of the MAX17048
    ADDRESS = 0x36
    
    # Register addresses
    VCELL_REGISTER = 0x02
    SOC_REGISTER = 0x04
    MODE_REGISTER = 0x06
    VERSION_REGISTER = 0x08
    CONFIG_REGISTER = 0x0C
    COMMAND_REGISTER = 0xFE

    def __init__(self, i2c_channel=0, scl_pin=7, sda_pin=15, address = ADDRESS):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        self.channel = i2c_channel

    def read_voltage(self):
        """Reads the battery voltage from the MAX17048."""
        raw = self._read_register(self.VCELL_REGISTER, 2)
        # Convert the raw value to voltage: 78.125 uV per LSB
        voltage = (raw[0] << 8 | raw[1]) * 0.078125 / 1000
        return voltage

    def read_soc(self):
        """Reads the state of charge (SOC) from the MAX17048."""
        raw = self._read_register(self.SOC_REGISTER, 2)
        # Convert the raw value to SOC: 1/256% per LSB
        soc = (raw[0] + raw[1] / 256) * 100
        return soc/100

    def reset(self):
        """Resets the MAX17048 to its default configuration."""
        self._write_register(self.COMMAND_REGISTER, [0x54, 0x00])

    def quick_start(self):
        """Performs a quick start to re-calculate SOC based on current voltage."""
        self._write_register(self.MODE_REGISTER, [0x40, 0x00])

    def _read_register(self, register, length):
        """Read a number of bytes from a specific register."""
        return self.i2c.readfrom_mem(self.address, register, length)

    def _write_register(self, register, values):
        """Write bytes to a specific register."""
        self.i2c.writeto_mem(self.address, register, bytes(values))