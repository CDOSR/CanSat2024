from machine import I2C, Pin
import time

class VEML6075:
    def __init__(self, i2c_channel=1, scl_pin=48, sda_pin=47, address = 0x10):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        self.channel = i2c_channel
        self.setup()

    def setup(self):
        # Initialize VEML6075
        self.i2c.writeto_mem(self.address, 0x00, bytearray([0x10]))  # Set UV configuration register
        # Enable the sensor (power on) and set active mode
        self.i2c.writeto_mem(self.address, 0x01, bytearray([0x06]))

    def read_uva(self):
        # Read UVA data
        data = self.i2c.readfrom_mem(self.address, 0x07, 2)
        uva = data[0] | data[1] << 8
        return uva

    def read_uvb(self):
        # Read UVB data
        data = self.i2c.readfrom_mem(self.address, 0x09, 2)
        uvb = data[0] | data[1] << 8
        return uvb

    def read_uv_index(self):
        # Calculate the UV Index using the UVA and UVB readings
        uva = self.read_uva()
        uvb = self.read_uvb()
        # Constants for UV Index calculation (may need calibration depending on environmental factors)
        uva_response = 1.0
        uvb_response = 1.0
        uv_index = (uva * uva_response + uvb * uvb_response) / 2.0
        return uv_index

# Example of initializing and reading from the sensor
# i2c_channel = 0
# scl_pin = 22
# sda_pin = 21
# sensor = VEML6075(i2c_channel, scl_pin, sda_pin)
# uva = sensor.read_uva()
# uvb = sensor.read_uvb()
# uv_index = sensor.read_uv_index()
# print("UVA:", uva, "UVB:", uvb, "UV Index:", uv_index)
