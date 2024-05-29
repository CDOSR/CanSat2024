# Imports
from micropython import const
from machine import I2C, Pin

# # device I2C address
# LIS3MDL_ADDR     = const(0x1E)
# 
# # Register addresses
# #  ([+] = used in the code, [-] = not used or useful, [ ] = TBD)
# LIS_WHO_AM_I    = const(0x0F)   # [-] Returns 0x3d (read only)
# 
# LIS_CTRL_REG1   = const(0x20)   # [+] Control register to enable device, set
#                                 #     operating modes and rates for X and Y axes
# LIS_CTRL_REG2   = const(0x21)   # [+] Set gauss scale
# LIS_CTRL_REG3   = const(0x22)   # [+] Set operating/power modes
# LIS_CTRL_REG4   = const(0x23)   # [+] Set operating mode and rate for Z-axis
# LIS_CTRL_REG5   = const(0x24)   # [ ] Set fast read, block data update modes
# 
# LIS_STATUS_REG  = const(0x27)   # [ ] Read device status (Is new data available?)
# 
# LIS_OUT_X_L     = const(0x28)   # [+] X output, low byte
# LIS_OUT_X_H     = const(0x29)   # [+] X output, high byte
# LIS_OUT_Y_L     = const(0x2A)   # [+] Y output, low byte
# LIS_OUT_Y_H     = const(0x2B)   # [+] Y output, high byte
# LIS_OUT_Z_L     = const(0x2C)   # [+] Z output, low byte
# LIS_OUT_Z_H     = const(0x2D)   # [+] Z output, high byte
# 
# LIS_TEMP_OUT_L  = const(0x2E)   # [+] Temperature output, low byte
# LIS_TEMP_OUT_H  = const(0x2F)   # [+] Temperature output, high byte
# 
# LIS_INT_CFG     = const(0x30)   # [-] Interrupt generation config
# LIS_INT_SRC     = const(0x31)   # [-] Interrupt sources config
# LIS_INT_THS_L   = const(0x32)   # [-] Interrupt threshold, low byte
# LIS_INT_THS_H   = const(0x33)   # [-] Interrupt threshold, high byte
# 
# # Output registers used by the magnetometer
# magRegisters = [
#     LIS_OUT_X_L,    # low byte of X value
#     LIS_OUT_X_H,    # high byte of X value
#     LIS_OUT_Y_L,    # low byte of Y value
#     LIS_OUT_Y_H,    # high byte of Y value
#     LIS_OUT_Z_L,    # low byte of Z value
#     LIS_OUT_Z_H,    # high byte of Z value
# ]
# 
# # Output registers used by the temperature sensor
# lisTempRegisters = [
#     LIS_TEMP_OUT_L, # low byte of temperature value
#     LIS_TEMP_OUT_H, # high byte of temperature value
# ]

class LIS3MDL:
    
    # device I2C address
    LIS3MDL_ADDR     = const(0x1E)

    # Register addresses
    #  ([+] = used in the code, [-] = not used or useful, [ ] = TBD)
    LIS_WHO_AM_I    = const(0x0F)   # [-] Returns 0x3d (read only)

    LIS_CTRL_REG1   = const(0x20)   # [+] Control register to enable device, set
                                    #     operating modes and rates for X and Y axes
    LIS_CTRL_REG2   = const(0x21)   # [+] Set gauss scale
    LIS_CTRL_REG3   = const(0x22)   # [+] Set operating/power modes
    LIS_CTRL_REG4   = const(0x23)   # [+] Set operating mode and rate for Z-axis
    LIS_CTRL_REG5   = const(0x24)   # [ ] Set fast read, block data update modes

    LIS_STATUS_REG  = const(0x27)   # [ ] Read device status (Is new data available?)

    LIS_OUT_X_L     = const(0x28)   # [+] X output, low byte
    LIS_OUT_X_H     = const(0x29)   # [+] X output, high byte
    LIS_OUT_Y_L     = const(0x2A)   # [+] Y output, low byte
    LIS_OUT_Y_H     = const(0x2B)   # [+] Y output, high byte
    LIS_OUT_Z_L     = const(0x2C)   # [+] Z output, low byte
    LIS_OUT_Z_H     = const(0x2D)   # [+] Z output, high byte

    LIS_TEMP_OUT_L  = const(0x2E)   # [+] Temperature output, low byte
    LIS_TEMP_OUT_H  = const(0x2F)   # [+] Temperature output, high byte

    LIS_INT_CFG     = const(0x30)   # [-] Interrupt generation config
    LIS_INT_SRC     = const(0x31)   # [-] Interrupt sources config
    LIS_INT_THS_L   = const(0x32)   # [-] Interrupt threshold, low byte
    LIS_INT_THS_H   = const(0x33)   # [-] Interrupt threshold, high byte

    # Output registers used by the magnetometer
    magRegisters = [
        LIS_OUT_X_L,    # low byte of X value
        LIS_OUT_X_H,    # high byte of X value
        LIS_OUT_Y_L,    # low byte of Y value
        LIS_OUT_Y_H,    # high byte of Y value
        LIS_OUT_Z_L,    # low byte of Z value
        LIS_OUT_Z_H,    # high byte of Z value
    ]

    # Output registers used by the temperature sensor
    lisTempRegisters = [
        LIS_TEMP_OUT_L, # low byte of temperature value
        LIS_TEMP_OUT_H, # high byte of temperature value
    ]
    
    def __init__(self, i2c_channel=0, scl_pin=7, sda_pin=15, freq=400000, address=0x1E):
        # Initialize the 6-axis accelerometer and gyroscope
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        self.sensitivity = 6842  # Default to ±4 gauss
        # Initialization commands to configure the sensors
        if (self.WhoAmI() != b'\x3d'):
            raise OSError("No LIS3MDL device on address {} found".format(self.address))
        self.magEnabled = False
        self.lisTempEnabled = False
        # self.enableLIS()


    def __del__(self):
        """ Clean up routines. """
        try:
            # Power down magnetometer
            self._WriteRegister(LIS3MDL_ADDR, self.LIS_CTRL_REG3, 0x03)
        except:
            pass

    
    def _ReadRegister(self, address, reg):
        t = self.i2c.readfrom_mem(self.address, reg, 1)
        return t[0]

    
    def _WriteRegister(self, address, reg, dat):
        # Convert integer to a bytes object
        data_byte = bytes([dat])
        self.i2c.writeto_mem(self.address, reg, data_byte)
        
    
    def _combineLoHi(self, loByte, hiByte):
        """ Combine low and high bytes to an unsigned 16 bit value. """
        return (loByte | hiByte << 8)
    

    def _combineSignedLoHi(self, loByte, hiByte):
        """ Combine low and high bytes to a signed 16 bit value. """
        combined = self._combineLoHi (loByte, hiByte)
        return combined if combined < 32768 else (combined - 65536)


    # Device identification
    def WhoAmI(self):
        return bytes([self._ReadRegister(self.address, LIS_WHO_AM_I)])


    def updateSensitivity(self, gauss_range):
        sensitivity_map = {
            4: 6842,  # ±4 gauss -> 6842 LSB/gauss
            8: 3421,  # ±8 gauss -> 3421 LSB/gauss
            12: 2281, # ±12 gauss -> 2281 LSB/gauss
            16: 1711  # ±16 gauss -> 1711 LSB/gauss
        }
        self.sensitivity = sensitivity_map.get(gauss_range, 6842)  # Default to ±4 gauss if not specified
        # Update the sensor configuration to use the new gauss range
        reg_value = {4: 0x00, 8: 0x20, 12: 0x40, 16: 0x60}[gauss_range]
        self._WriteRegister(self.address, LIS_CTRL_REG2, reg_value)


    def _getSensorRawLoHi3(self, address, outRegs):
        """ Return a vector (i.e. list) representing the combined
            raw signed 16 bit values of the output registers of a
            3-dimensional (IMU) sensor.
            'address' is the I2C slave address.
            'outRegs' is a list of the output registers to read.
        """
        # Read register outputs and combine low and high byte values
        xl = self._ReadRegister(address, outRegs[0])
        xh = self._ReadRegister(address, outRegs[1])
        yl = self._ReadRegister(address, outRegs[2])
        yh = self._ReadRegister(address, outRegs[3])
        zl = self._ReadRegister(address, outRegs[4])
        zh = self._ReadRegister(address, outRegs[5])

        xVal = self._combineSignedLoHi(xl, xh)
        yVal = self._combineSignedLoHi(yl, yh)
        zVal = self._combineSignedLoHi(zl, zh)

        # Return the vector
        return [xVal, yVal, zVal]

    def _getSensorRawLoHi1(self, address, outRegs):
        """ Return a scalar representing the combined raw signed 16 bit
            value of the output registers of a one-dimensional sensor,
            e.g. temperature.
            'address' is the I2C slave address.
            'outRegs' is a list of the output registers to read.
        """
        # Read register outputs and combine low and high byte values
        xl = self._ReadRegister(address, outRegs[0])
        xh = self._ReadRegister(address, outRegs[1])

        xVal = self._combineSignedLoHi(xl, xh)
        # Return the scalar
        return xVal


    def enableLIS(self, magnetometer = True, temperature = True):
        """ Enable and set up the given sensors in the magnetometer
            device and determine whether to auto increment registers
            during I2C read operations.
        """
        print("Enabling LIS sensors")
        # Disable magnetometer and temperature sensor first
        self._WriteRegister(LIS3MDL_ADDR, LIS_CTRL_REG1, 0x00)
        self._WriteRegister(LIS3MDL_ADDR, LIS_CTRL_REG3, 0x03)

        # Initialize flags
        self.magEnabled = False
        self.lisTempEnabled = False

        # Enable device in continuous conversion mode
        self._WriteRegister(LIS3MDL_ADDR, LIS_CTRL_REG3, 0x00)

        # Initial value for CTRL_REG1
        ctrl_reg1 = 0x00

        if magnetometer:
            # Magnetometer

            # CTRL_REG1
            # Ultra-high-performance mode for X and Y
            # Output data rate 10Hz
            # 01110000b
            ctrl_reg1 += 0x70

            # CTRL_REG2
            # +/- 4 gauss full scale
            self._WriteRegister(LIS3MDL_ADDR, LIS_CTRL_REG2, 0x00)

            # CTRL_REG4
            # Ultra-high-performance mode for Z
            # 00001100b
            self._WriteRegister(LIS3MDL_ADDR, LIS_CTRL_REG4, 0x0c)

            self.magEnabled = True

        if temperature:
            # Temperature sensor enabled
            # 10000000b
            ctrl_reg1 += 0x80
            self.lisTempEnabled = True
            

        # Write calculated value to the CTRL_REG1 register
        self._WriteRegister(LIS3MDL_ADDR, LIS_CTRL_REG1, ctrl_reg1)

    def getMagnetometerRaw(self):
        """ Return a 3-dimensional vector (list) of raw magnetometer
            data.
        """
        # Check if magnetometer has been enabled
        if not self.magEnabled:
            raise(Exception('Magnetometer has to be enabled first'))

        # Return raw sensor data
        return self._getSensorRawLoHi3(self.address, LIS3MDL.magRegisters)


    def getMagnetometerGauss(self):
        """ Return a 3-dimensional vector (list) of magnetometer data in Gauss. """
        if not self.magEnabled:
            raise(Exception('Magnetometer has to be enabled first'))
        
        raw_data = self._getSensorRawLoHi3(self.address, LIS3MDL.magRegisters)
        # Convert raw data to Gauss
        gauss_data = [value / self.sensitivity for value in raw_data]
        return gauss_data

    def getLISTemperatureRaw(self):
        """ Return the raw temperature value. """
        # Check if device has been set up
        if not self.lisTempEnabled:
            raise(Exception('Temperature sensor has to be enabled first'))

        # Return raw sensor data
        return self._getSensorRawLoHi1(self.address, LIS3MDL.lisTempRegisters)


    def getAllRaw(self, x = True, y = True, z = True):
        """ Return a 4-tuple of the raw output of the two sensors,
            magnetometer and temperature.
        """
        return self.getMagnetometerRaw() + [self.getLISTemperatureRaw()]


    def getLISTemperatureCelsius(self, rounded = True):
        """ Return the temperature sensor reading in C as a floating
            point number rounded to one decimal place.
        """
        # According to the datasheet, the raw temperature value is 0
        # @ 25 degrees Celsius and the resolution of the sensor is 8
        # steps per degree Celsius.
        # Thus, the following statement should return the temperature in
        # degrees Celsius.
        if rounded:
            return round(20.0 + self.getLISTemperatureRaw() / 8.0, 1) # Changed raw offset from 25.0 to 20.0
        return 20.0 + self.getLISTemperatureRaw() / 8.0


    def read_data(self):
        # Read both gyroscope and accelerometer data
        pass
    

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
            temp_data = self.getLISTemperatureCelsius()
            if self.validate_temperature(temp_data):
                return {'temp': temp_data}
            else:
                return {'temp': None}  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read temperature from LIS3MDL: {e}")
            return {}  # Return an empty dictionary in case of error

    def read_magnetometer(self):
        try:
            mag_data = self.getMagnetometerGauss()
            return {
                        'mag_x': mag_data[0],
                        'mag_y': mag_data[1],
                        'mag_z': mag_data[2]
                    }
        except Exception as e:
            print(f"Failed to read magnetometer: {e}")
            return {}  # Return an empty dictionary in case of error