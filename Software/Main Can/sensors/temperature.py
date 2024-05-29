from machine import I2C, Pin
import time

# Default I2C address for device.
MCP9808_I2CADDR_DEFAULT        = const(0x18)

# Register addresses.
MCP9808_REG_CONFIG             = const(0x01)
MCP9808_REG_UPPER_TEMP         = const(0x02)
MCP9808_REG_LOWER_TEMP         = const(0x03)
MCP9808_REG_CRIT_TEMP          = const(0x04)
MCP9808_REG_AMBIENT_TEMP       = const(0x05)
MCP9808_REG_MANUF_ID           = const(0x06)
MCP9808_REG_DEVICE_ID          = const(0x07)
MCP9808_REG_RESOLUTION         = const(0x08)

# Configuration register values.
MCP9808_REG_CONFIG_SHUTDOWN    = const(0x0100)
MCP9808_REG_CONFIG_CRITLOCKED  = const(0x0080)
MCP9808_REG_CONFIG_WINLOCKED   = const(0x0040)
MCP9808_REG_CONFIG_INTCLR      = const(0x0020)
MCP9808_REG_CONFIG_ALERTSTAT   = const(0x0010)
MCP9808_REG_CONFIG_ALERTCTRL   = const(0x0008)
MCP9808_REG_CONFIG_ALERTSEL    = const(0x0004)
MCP9808_REG_CONFIG_ALERTPOL    = const(0x0002)
MCP9808_REG_CONFIG_ALERTMODE   = const(0x0001)

T_RES_MIN = const(0x00)
T_RES_LOW = const(0x01)
T_RES_AVG = const(0x02)
T_RES_MAX = const(0x03)

class TemperatureSensor:
    def __init__(self, i2c_channel=1, scl_pin=48, sda_pin=47, freq=400000, address=0x18):
        # Initialize temperature sensor
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        
    def read_temperature(self):
        # MCP9808 temperature register address
        temp_register = 0x05
        data = self.i2c.readfrom_mem(self.address, temp_register, 2)
        
        # Convert the data to 13-bits and maintain sign
        temp = (data[0] & 0x1F) * 256 + data[1]
        if temp > 4095:
            temp -= 8192
        temperature = temp * 0.0625  # Convert to Celsius
        return temperature
    
    
class MCP9808:
    """
    This class implements an interface to the MCP9808 temprature sensor from
    Microchip.
    """
    
    def __init__(self, i2c_channel=1, scl_pin=48, sda_pin=47, address=0x18): # freq=400000
        """
        Initialize a sensor object on the given I2C bus and accessed by the
        given address.
        """
#         if i2c_channel == None or i2c.__class__ != I2C:
#             raise ValueError('I2C object needed as argument!')
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.channel = i2c_channel
        self.address = address
        self.check_device()
        
    def send(self, buf):
        """
        Sends the given buffer object over I2C to the sensor.
        """
        if isinstance(buf, int):
            data_byte = bytes([buf])
        elif isinstance(buf, bytearray) or isinstance(buf, bytes):
            data_byte = buf
        else:
            raise TypeError("Buffer must be an int, bytes, or bytearray")
        self.i2c.writeto(self.address, data_byte)
        
    def recv(self, n):
        """
        Read bytes from the sensor using I2C. The byte count must be specified
        as an argument.
        Returns a bytearray containing the result.
        """
        return self.i2c.readfrom(self.address, n)
    
    def read_register(self, reg_addr, length):
        return self.i2c.readfrom_mem(MCP9808_I2CADDR_DEFAULT, reg_addr, length)
    
    def check_device(self):
        """
        Checks the manufacturer and device identifiers.
        """
        # Reading Manufacturer ID
        m_id = self.read_register(MCP9808_REG_MANUF_ID, 2)
        if m_id != b'\x00\x54':
            raise Exception(f"Invalid manufacturer ID: {m_id}!")

        # Reading Device ID
        d_id = self.read_register(MCP9808_REG_DEVICE_ID, 2)
        if d_id != b'\x04\x00':
            raise Exception(f"Invalid device or revision ID: {d_id}!")
        
    def set_shutdown_mode(self, shdn=True):
        """
        Set sensor into shutdown mode to draw less than 1 uA and disable
        continuous temperature conversion.
        """
        config = int.from_bytes(self.i2c.readfrom_mem(self.address, MCP9808_REG_CONFIG, 2), 'little')
        if shdn:
            config |= MCP9808_REG_CONFIG_SHUTDOWN
        else:
            config &= ~MCP9808_REG_CONFIG_SHUTDOWN
        config_bytes = config.to_bytes(2, 'little')
        self.i2c.writeto_mem(self.address, MCP9808_REG_CONFIG, config_bytes)
        
    def getTemp(self):
        """
        Read temperature in degree Celsius and return float value.
        """
        try:
            self.send(MCP9808_REG_AMBIENT_TEMP)
            # Write to TA Register Address
            self.i2c.writeto(MCP9808_I2CADDR_DEFAULT, bytearray([MCP9808_REG_AMBIENT_TEMP]))
            data = self.i2c.readfrom(MCP9808_I2CADDR_DEFAULT, 2)
            upper_byte = data[0]
            lower_byte = data[1]
            
            # Masking the upper byte to remove flag bits and get only temperature bits
            temp_msb = upper_byte & 0x1F
            
            # Checking if the temperature is negative
            if temp_msb & 0x10:  # if the sign bit is set
                temp_msb = temp_msb & 0x0F  # Clear the sign bit
                temperature = 256 - (temp_msb * 16 + lower_byte / 16.0)
            else:
                temperature = (temp_msb * 16 + lower_byte / 16.0)
            
            return temperature -70
        except Exception as e:
            print(f"Error in getTemp(): {e}")
            raise

#  def read_temperature(self):
#         # MCP9808 temperature register address
#         temp_register = 0x05
#         data = self.i2c.readfrom_mem(self.address, temp_register, 2)
#         
#         # Convert the data to 13-bits and maintain sign
#         temp = (data[0] & 0x1F) * 256 + data[1]
#         if temp > 4095:
#             temp -= 8192
#         temperature = temp * 0.0625  # Convert to Celsius
#         return temperature

        
    def getTempInt(self):
        """
        Read a temperature in degree celsius and return a tuple of two parts.
        The first part is the decimal patr and the second the fractional part
        of the value.
        This method does avoid floating point arithmetic completely to support
        plattforms missing float support.
        """
        self.send(MCP9808_REG_AMBIENT_TEMP)
        raw = self.recv(2)
        u = (raw[0] & 0xf) << 4
        l = raw[1] >> 4
        if raw[0] & 0x10 == 0x10:
            temp = 256 - (u + l)
            frac = 256 - (raw[1] & 0x0f) * 100 >> 4
        else:
            temp = u + l
            frac = (raw[1] & 0x0f) * 100 >> 4
        return temp, frac
    
    def setResolution(self, r):
        """
        Sets the temperature resolution.
        """
        if r not in [T_RES_MIN, T_RES_LOW, T_RES_AVG, T_RES_MAX]:
            raise ValueError('Invalid temperature resolution requested!')
        b = bytearray()
        b.append(MCP9808_REG_RESOLUTION)
        b.append(r)
        self.send(b)
        
    def hysteresis(self, tHyst):
        """
        A function to set the hysteresis. 0 = 0°C (default), 1 = +1.5°C, 2 = +3°C,
        3 = +6°C. Cannot be set when Crit Lock or Win Lock are 1, can be
        programmed in shutdown mode. Applies to tUpper, tLower and tCrit, only as
        temperature drops. In effect this setting tells the sensor to assume that
        the real ambient temperature is the sensor temperature minus the hysteresis
        value, to compensate for temperature dropping faster than the sensor detects.
        """
        if isinstance(tHyst, int) and (tHyst >= 0) and (tHyst <= 3):
            # Get the config register bytes
            data = self.getConfigReg()
            # Clear the tHyst bits of the MSB.
            data[0] = data[0] & 0b00000001
            # Merge the MSB with the new tHyst bits
            data[0] = data[0] | (tHyst << 1)
            # Write the new values back to the register
            self.i2c.writeto(MCP9808_REG_CONFIG, data)
        else:
            print("ERROR: tHyst must be an int of 0-3 inclusive.  Value\
                given was " + str(tHyst) + ".")
            
    def getConfigReg(self):
        """
        Returns the Config register value
        """
        # Read Config Register value
        result = int.from_bytes(self.i2c.readfrom_mem(self.address, MCP9808_REG_CONFIG, 2),'little') & 0xFFFF
        result = ((result << 8) & 0xFF00) + (result >> 8)
        return result


    def clearConfigReg(self):
        """
        Clear the Config Register value
        """
        self.i2c.writeto_mem(self.address, MCP9808_REG_CONFIG, 0x0000)
        
    def validate_temperature(self, temp):
        """
        Validates the temperature is within the expected range (-40 to 85).
        """
        if not (-40 <= temp <= 85):
            print(f"Critical error: Temperature {temp} out of expected range.")
            return False
        return True
        
    def read_temperature(self):
        """
        Reads the temperature from the MCP9808 sensor and validates it.
        """
        try:
            temp_data = self.getTemp()
            if self.validate_temperature(temp_data):
                return {'temp': temp_data}
            else:
                return {'temp': None}  # Or handle as needed
        except Exception as e:
            print(f"Failed to read temperature from MCP9808: {e}")
            return {}  # Return an empty dictionary in case of error

 
########################

class BME280:
    """Class for communicating with an I2C device.

    Allows reading and writing 8-bit, 16-bit, and byte array values to
    registers on the device.
    """    
    
    # BME280 default address.
    BME280_I2CADDR = const(0x77)

    # Operating Modes
    BME280_OSAMPLE_1 = const(1)
    BME280_OSAMPLE_2 = const(2)
    BME280_OSAMPLE_4 = const(3)
    BME280_OSAMPLE_8 = const(4)
    BME280_OSAMPLE_16 = const(5)

    # BME280 Registers
    BME280_REGISTER_DIG_T1        = const(0x88)  # Trimming parameter registers
    BME280_REGISTER_DIG_T2        = const(0x8A)
    BME280_REGISTER_DIG_T3        = const(0x8C)

    BME280_REGISTER_DIG_P1        = const(0x8E)
    BME280_REGISTER_DIG_P2        = const(0x90)
    BME280_REGISTER_DIG_P3        = const(0x92)
    BME280_REGISTER_DIG_P4        = const(0x94)
    BME280_REGISTER_DIG_P5        = const(0x96)
    BME280_REGISTER_DIG_P6        = const(0x98)
    BME280_REGISTER_DIG_P7        = const(0x9A)
    BME280_REGISTER_DIG_P8        = const(0x9C)
    BME280_REGISTER_DIG_P9        = const(0x9E)

    BME280_REGISTER_DIG_H1        = const(0xA1)
    BME280_REGISTER_DIG_H2        = const(0xE1)
    BME280_REGISTER_DIG_H3        = const(0xE3)
    BME280_REGISTER_DIG_H4        = const(0xE4)
    BME280_REGISTER_DIG_H5        = const(0xE5)
    BME280_REGISTER_DIG_H6        = const(0xE6)
    BME280_REGISTER_DIG_H7        = const(0xE7)

    BME280_REGISTER_CHIPID        = const(0xD0)
    BME280_REGISTER_VERSION       = const(0xD1)
    BME280_REGISTER_SOFTRESET     = const(0xE0)

    BME280_REGISTER_CONTROL_HUM   = const(0xF2)
    BME280_REGISTER_CONTROL       = const(0xF4)
    BME280_REGISTER_CONFIG        = const(0xF5)
    BME280_REGISTER_PRESSURE_DATA = const(0xF7)
    BME280_REGISTER_TEMP_DATA     = const(0xFA)
    BME280_REGISTER_HUMIDITY_DATA = const(0xFD)


    def __init__(self, i2c_channel=1, scl_pin=48, sda_pin=47, freq=400000, address=BME280_I2CADDR, mode=BME280_OSAMPLE_8):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        self.channel = i2c_channel
        # Check that mode is valid.
        if mode not in [BME280_OSAMPLE_1, BME280_OSAMPLE_2, BME280_OSAMPLE_4,
                    BME280_OSAMPLE_8, BME280_OSAMPLE_16]:
            raise ValueError(
                'Unexpected mode value {0}. Set mode to one of '
                'BME280_ULTRALOWPOWER, BME280_STANDARD, BME280_HIGHRES, or '
                'BME280_ULTRAHIGHRES'.format(mode))
        self.mode = mode
        self.overscan_temperature = BME280_OSAMPLE_16
        self.overscan_pressure = BME280_OSAMPLE_16
        self.overscan_humidity = BME280_OSAMPLE_2
        self.__sealevel = 102000
        self.load_calibration()
        self.write8(BME280_REGISTER_CONTROL, 0x3F)
        self.t_fine = 0
        time.sleep(0.2)

    def writeRaw8(self, value):
        """Write an 8-bit value on the bus (without register)."""
        value = value & 0xFF
        self.i2c.writeto(self.address, value)


    def write8(self, register, value):
        """Write an 8-bit value to the specified register."""
        b=bytearray(1)
        b[0]=value & 0xFF
        self.i2c.writeto_mem(self.address, register, b)


    def write16(self, register, value):
        """Write a 16-bit value to the specified register."""
        value = value & 0xFFFF
        b=bytearray(2)
        b[0]= value & 0xFF
        b[1]= (value>>8) & 0xFF
        self.i2c.writeto_mem(self.address, register, value)


    def readRaw8(self):
        """Read an 8-bit value on the bus (without register)."""
        return int.from_bytes(self.i2c.readfrom(self.address, 1),'little') & 0xFF


    def readU8(self, register):
        """Read an unsigned byte from the specified register."""
        return int.from_bytes(
            self.i2c.readfrom_mem(self.address, register, 1),'little') & 0xFF


    def readS8(self, register):
        """Read a signed byte from the specified register."""
        result = self.readU8(register)
        if result > 127:
            result -= 256
        return result


    def readU16(self, register, little_endian=True):
        """Read an unsigned 16-bit value from the specified register, with the
        specified endianness (default little endian, or least significant byte
        first)."""
        result = int.from_bytes(
            self.i2c.readfrom_mem(self.address, register, 2),'little') & 0xFFFF
        if not little_endian:
            result = ((result << 8) & 0xFF00) + (result >> 8)
        return result


    def readS16(self, register, little_endian=True):
        """Read a signed 16-bit value from the specified register, with the
        specified endianness (default little endian, or least significant byte
        first)."""
        result = self.readU16(register, little_endian)
        if result > 32767:
            result -= 65536
        return result

    def readU16LE(self, register):
        """Read an unsigned 16-bit value from the specified register, in little
        endian byte order."""
        return self.readU16(register, little_endian=True)


    def readU16BE(self, register):
        """Read an unsigned 16-bit value from the specified register, in big
        endian byte order."""
        return self.readU16(register, little_endian=False)


    def readS16LE(self, register):
        """Read a signed 16-bit value from the specified register, in little
        endian byte order."""
        return self.readS16(register, little_endian=True)


    def readS16BE(self, register):
        """Read a signed 16-bit value from the specified register, in big
        endian byte order."""
        return self.readS16(register, little_endian=False)
    
    def load_calibration(self):
        self.dig_T1 = self.readU16LE(BME280_REGISTER_DIG_T1)
        self.dig_T2 = self.readS16LE(BME280_REGISTER_DIG_T2)
        self.dig_T1 = self.readU16LE(BME280_REGISTER_DIG_T1)
        self.dig_T2 = self.readS16LE(BME280_REGISTER_DIG_T2)
        self.dig_T3 = self.readS16LE(BME280_REGISTER_DIG_T3)

        self.dig_P1 = self.readU16LE(BME280_REGISTER_DIG_P1)
        self.dig_P2 = self.readS16LE(BME280_REGISTER_DIG_P2)
        self.dig_P3 = self.readS16LE(BME280_REGISTER_DIG_P3)
        self.dig_P4 = self.readS16LE(BME280_REGISTER_DIG_P4)
        self.dig_P5 = self.readS16LE(BME280_REGISTER_DIG_P5)
        self.dig_P6 = self.readS16LE(BME280_REGISTER_DIG_P6)
        self.dig_P7 = self.readS16LE(BME280_REGISTER_DIG_P7)
        self.dig_P8 = self.readS16LE(BME280_REGISTER_DIG_P8)
        self.dig_P9 = self.readS16LE(BME280_REGISTER_DIG_P9)

        self.dig_H1 = self.readU8(BME280_REGISTER_DIG_H1)
        self.dig_H2 = self.readS16LE(BME280_REGISTER_DIG_H2)
        self.dig_H3 = self.readU8(BME280_REGISTER_DIG_H3)
        self.dig_H6 = self.readS8(BME280_REGISTER_DIG_H7)

        h4 = self.readS8(BME280_REGISTER_DIG_H4)
        h4 = (h4 << 24) >> 20
        self.dig_H4 = h4 | (self.readU8(BME280_REGISTER_DIG_H5) & 0x0F)

        h5 = self.readS8(BME280_REGISTER_DIG_H6)
        h5 = (h5 << 24) >> 20
        self.dig_H5 = h5 | (
            self.readU8(BME280_REGISTER_DIG_H5) >> 4 & 0x0F)

    def read_raw_temp(self):
        """Reads the raw (uncompensated) temperature from the sensor."""
        meas = self.mode
        self.write8(BME280_REGISTER_CONTROL_HUM, meas)
        meas = self.mode << 5 | self.mode << 2 | 1
        self.write8(BME280_REGISTER_CONTROL, meas)

        sleep_time = 1250 + 2300 * (1 << (self.overscan_temperature - 1))
        sleep_time = sleep_time + 2300 * (1 << (self.overscan_pressure - 1)) + 575
        sleep_time = sleep_time + 2300 * (1 << (self.overscan_humidity - 1)) + 575
        time.sleep(sleep_time / 1000000)  # Wait the required time

        msb = self.readU8(BME280_REGISTER_TEMP_DATA)
        lsb = self.readU8(BME280_REGISTER_TEMP_DATA + 1)
        xlsb = self.readU8(BME280_REGISTER_TEMP_DATA + 2)
        raw = ((msb << 16) | (lsb << 8) | xlsb) >> 4
        return raw


    def read_raw_pressure(self):
        """Reads the raw (uncompensated) pressure level from the sensor.
        Assumes that the temperature has already been read
        i.e. that enough delay has been provided
        """
        msb = self.readU8(BME280_REGISTER_PRESSURE_DATA)
        lsb = self.readU8(BME280_REGISTER_PRESSURE_DATA + 1)
        xlsb = self.readU8(BME280_REGISTER_PRESSURE_DATA + 2)
        raw = ((msb << 16) | (lsb << 8) | xlsb) >> 4
        return raw


    def read_raw_humidity(self):
        """Assumes that the temperature has already been read
        i.e. that enough delay has been provided
        """
        msb = self.readU8(BME280_REGISTER_HUMIDITY_DATA)
        lsb = self.readU8(BME280_REGISTER_HUMIDITY_DATA + 1)
        raw = (msb << 8) | lsb
        return raw


    def read_temperature(self):
        """Get the compensated temperature in 0.01 of a degree celsius."""
        adc = self.read_raw_temp()
        var1 = ((adc >> 3) - (self.dig_T1 << 1)) * (self.dig_T2 >> 11)
        var2 = ((
            (((adc >> 4) - self.dig_T1) * ((adc >> 4) - self.dig_T1)) >> 12) *
            self.dig_T3) >> 14
        self.t_fine = var1 + var2
        temp = ((self.t_fine * 5 + 128) >> 8)
        return temp


    def read_pressure(self):
        """Gets the compensated pressure in Pascals."""
        adc = self.read_raw_pressure()
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = (((var1 * var1 * self.dig_P3) >> 8) +
                ((var1 * self.dig_P2) >> 12))
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            return 0
        p = 1048576 - adc
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        pressure = (((p + var1 + var2) >> 8) + (self.dig_P7 << 4))
        return pressure


    def read_humidity(self):
        adc = self.read_raw_humidity()
        # print 'Raw humidity = {0:d}'.format (adc)
        h = self.t_fine - 76800
        h = (((((adc << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) +
             16384) >> 15) * (((((((h * self.dig_H6) >> 10) * (((h *
                              self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) *
                              self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = 0 if h < 0 else h
        h = 419430400 if h > 419430400 else h
        return h >> 12

    @property
    def temperature(self):
        """Return the temperature in degrees."""
        t = self.read_temperature()
        # ti = t // 100
        # td = t - ti * 100
        # print("{}.{:02d}C".format(ti, td))
        return round (t/100,2)

    @property
    def pressure(self):
        """Return the temperature in hPa."""
        p = self.read_pressure() // 256
        # pi = p // 100
        # pd = p - pi * 100
        # print("{}.{:02d}hPa".format(pi, pd))
        return round (p/100, 2)

    @property
    def humidity(self):
        """Return the humidity in percent."""
        h = self.read_humidity()
        # hi = h // 1024
        # hd = h * 100 // 1024 - hi * 100
        # print("{}.{:02d}%".format(hi, hd))
        return round(h/1024, 2)

    @property
    def sealevel(self):
        return self.__sealevel

    @sealevel.setter
    def sealevel(self, value):
        if 30000 < value < 120000:  # just ensure some reasonable value
            self.__sealevel = value

    @property
    def altitude(self):
        """ Altitude in meters """
        p = self.read_pressure() // 256
        from math import pow
        try:
            p = 44330 * (1.0 - pow(p / self.__sealevel, 0.1903))
        except:
            p = 0.0
        return p
    
    def validate_temperature(self, temp):
        """
        Validates the temperature is within the expected range (-40 to 85).
        """
        if not (-40 <= temp <= 85):
            print(f"Critical error: Temperature {temp} out of expected range.")
            return False
        return True
    
    def validate_pressure(self, pres):
        """
        Validates the temperature is within the expected range (260 to 1260) mbars.
        """
        if not (260 <= pres <= 1260):
            print(f"Critical error: Pressure {pres} out of expected range.")
            return False
        return True

    def validate_altitude(self, alt):
        """
        Validates the altitude is within the expected range (-500 to 10000) mbars.
        """
        if not (-500 <= alt <= 10000):
            print(f"Critical error: Altitude {alt} out of expected range.")
            return False
        return True
        
    def validate_humidity(self, hum):
        """
        Validates the altitude is within the expected range (0 to 100) %.
        """
        if not (0 <= hum <= 100):
            print(f"Critical error: Humidity {hum} out of expected range.")
            return False
        return True

    def get_temperature(self):
        """
        Reads the temperature from the MCP9808 sensor and validates it.
        """
        try:
            temp_data = self.temperature
            if self.validate_temperature(temp_data):
                return temp_data
            else:
                return None  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read temperature from BMP280: {e}")
            return {}  # Return an empty dictionary in case of error
        
    def get_altitude(self):
        """
        Reads the altitude in meters from the BMP280 sensor and validates it.
        """
        try:
            alt_data = self.altitude
            if self.validate_altitude(alt_data):
                return alt_data
            else:
                return None  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read altitude from BMP280: {e}")
            return {}  # Return an empty dictionary in case of error

    def get_pressure(self):
        """
        Reads the pressure in mBars from the BMP280 sensor and validates it.
        """
        try:
            pres_data = self.pressure
            if self.validate_pressure(pres_data):
                return pres_data
            else:
                return None  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read pressure from BMP280: {e}")
            return {}  # Return an empty dictionary in case of error
        
    def get_humidity(self):
        """
        Reads the humidity in mBars from the BMP280 sensor and validates it.
        """
        try:
            hum_data = self.humidity
            if self.validate_humidity(hum_data):
                return hum_data
            else:
                return None  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read humidity from BMP280: {e}")
            return {}  # Return an empty dictionary in case of error
        

from machine import I2C, Pin
import time

class BMP280:
    def __init__(self, i2c_channel=1, scl_pin=48, sda_pin=47, address=0x77):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        self.channel = i2c_channel
        self.calibration_params = self.read_calibration_params()
        self.setup()

    def read_calibration_params(self):
        # Registers containing calibration data are read and stored
        regs = self.i2c.readfrom_mem(self.address, 0x88, 24)
        return {
            'dig_T1': self.u16_le(regs, 0),
            'dig_T2': self.s16_le(regs, 2),
            'dig_T3': self.s16_le(regs, 4),
            'dig_P1': self.u16_le(regs, 6),
            'dig_P2': self.s16_le(regs, 8),
            'dig_P3': self.s16_le(regs, 10),
            'dig_P4': self.s16_le(regs, 12),
            'dig_P5': self.s16_le(regs, 14),
            'dig_P6': self.s16_le(regs, 16),
            'dig_P7': self.s16_le(regs, 18),
            'dig_P8': self.s16_le(regs, 20),
            'dig_P9': self.s16_le(regs, 22),
        }

    def s16_le(self, b, offset):
        return (b[offset] | (b[offset+1] << 8)) - ((b[offset+1] & 0x80) << 1)

    def u16_le(self, b, offset):
        return b[offset] | (b[offset+1] << 8)

    def setup(self):
        self.i2c.writeto_mem(self.address, 0xF4, b'\x2F')
        self.i2c.writeto_mem(self.address, 0xF5, b'\x0C')

    def read_data(self):
        data = self.i2c.readfrom_mem(self.address, 0xF7, 6)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return self.compensate(temp_raw, pres_raw)

    def compensate(self, temp_raw, pres_raw):
        # Compensation algorithms from the BMP280 datasheet
        # Calculate temperature
        t_fine = self.calculate_t_fine(temp_raw)
        temperature = (t_fine * 5 + 128) >> 8

        # Calculate pressure
        pressure = self.calculate_pressure(pres_raw, t_fine)
        return temperature / 100.0, pressure  # Return temperature in °C and pressure in hPa

    def calculate_t_fine(self, temp_raw):
        # Calculates t_fine value needed for temperature and pressure compensation
        var1 = ((((temp_raw >> 3) - (self.calibration_params['dig_T1'] << 1))) * (self.calibration_params['dig_T2'])) >> 11
        var2 = (((((temp_raw >> 4) - (self.calibration_params['dig_T1'])) * ((temp_raw >> 4) - (self.calibration_params['dig_T1']))) >> 12) * (self.calibration_params['dig_T3'])) >> 14
        return var1 + var2

    def calculate_pressure(self, pres_raw, t_fine):
        var1 = (t_fine / 2) - 64000
        var2 = var1 * var1 * self.calibration_params['dig_P6'] / 32768
        var2 = var2 + var1 * self.calibration_params['dig_P5'] * 2
        var2 = (var2 / 4) + (self.calibration_params['dig_P4'] * 65536)
        var1 = (self.calibration_params['dig_P3'] * var1 * var1 / 524288 + self.calibration_params['dig_P2'] * var1) / 524288
        var1 = (1 + var1 / 32768) * self.calibration_params['dig_P1']
        if var1 == 0:
            return 0  # Prevent division by zero
        p = 1048576 - pres_raw
        p = ((p - (var2 / 4096)) * 6250) / var1
        var1 = self.calibration_params['dig_P9'] * p * p / 2147483648
        var2 = p * self.calibration_params['dig_P8'] / 32768
        return (p + (var1 + var2 + self.calibration_params['dig_P7']) / 16) / 100

    def get_temperature(self):
        temp, _ = self.read_data()
        return temp

    def get_pressure(self):
        _, pressure = self.read_data()
        return pressure


    
