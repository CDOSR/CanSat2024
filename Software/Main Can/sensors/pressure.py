# Imports
from micropython import const
from machine import I2C, Pin
import time
import utime
import struct
import math
from utils.logger import Logger

log = Logger()

def read24(arr: ReadableBuffer) -> float:
    """Parse an unsigned 24-bit value as a floating point and return it."""
    ret = 0.0
    # print([hex(i) for i in arr])
    for b in arr:
        ret *= 256.0
        ret += float(b & 0xFF)
    return ret

def delay_microseconds(nusec):
    """HELP must be same as dev->delay_us"""
    time.sleep(nusec / 1000000.0)
    
def bme_set_bits(reg_data, bitname_msk, bitname_pos, data):
    """
    Macro to set bits
    data2 = data << bitname_pos
    set masked bits from data2 in reg_data
    """
    return (reg_data & ~bitname_msk) | ((data << bitname_pos) & bitname_msk)

def bme_set_bits_pos_0(reg_data, bitname_msk, data):
    """
    Macro to set bits starting from position 0
    set masked bits from data in reg_data
    """
    return (reg_data & ~bitname_msk) | (data & bitname_msk)

class LPS25H(object):
    
    # device I2C address
    LPS25H_ADDR           = const(0x5D)

    # Register addresses
    #  ([+] = used in the code, [-] = not used or useful, [ ] = TBD)
    LPS25H_REF_P_XL       = const(0x08) # [ ] Reference pressure, lowest byte
    LPS25H_REF_P_L        = const(0x09) # [ ] Reference pressure, low byte
    LPS25H_REF_P_H        = const(0x0A) # [ ] Reference pressure, high byte

    LPS25H_WHO_AM_I       = const(0x0F) # [+] Returns 0xbd (read only)

    LPS25H_RES_CONF       = const(0x10) # [ ] Set pressure and temperature resolution

    LPS25H_CTRL_REG1      = const(0x20) # [+] Set device power mode / ODR / BDU
    LPS25H_CTRL_REG2      = const(0x21) # [-] FIFO / I2C configuration
    LPS25H_CTRL_REG3      = const(0x22) # [-] Interrupt configuration
    LPS25H_CTRL_REG4      = const(0x23) # [-] Interrupt configuration

    LPS25H_INT_CFG        = const(0x24) # [-] Interrupt configuration
    LPS25H_INT_SOURCE     = const(0x25) # [-] Interrupt source configuration

    LPS25H_STATUS_REG     = const(0x27) # [ ] Status (new pressure/temperature data
                                        #     available)

    LPS25H_PRESS_OUT_XL   = const(0x28) # [+] Pressure output, loweste byte
    LPS25H_PRESS_OUT_L    = const(0x29) # [+] Pressure output, low byte
    LPS25H_PRESS_OUT_H    = const(0x2A) # [+] Pressure output, high byte

    LPS25H_TEMP_OUT_L     = const(0x2B) # [+] Temperature output, low byte
    LPS25H_TEMP_OUT_H     = const(0x2C) # [+] Temperature output, high byte

    LPS25H_FIFO_CTRL      = const(0x2E) # [ ] FIFO control / mode selection
    LPS25H_FIFO_STATUS    = const(0x2F) # [-] FIFO status

    LPS25H_THS_P_L        = const(0x30) # [-] Pressure interrupt threshold, low byte
    LPS25H_THS_P_H        = const(0x31) # [-] Pressure interrupt threshold, high byte

    # The next two registers need special soldering and are not
    # available on the AltIMU
    LPS25H_RPDS_L         = const(0x39)
    LPS25H_RPDS_H         = const(0x3A)

    # Registers used for reference pressure
    refRegisters = [
        LPS25H_REF_P_XL, # lowest byte of reference pressure value
        LPS25H_REF_P_L,  # low byte of reference pressure value
        LPS25H_REF_P_H,  # high byte of reference pressure value
    ]

    # Output registers used by the pressure sensor
    lpsPressRegisters = [
        LPS25H_PRESS_OUT_XL, # lowest byte of pressure value
        LPS25H_PRESS_OUT_L,  # low byte of pressure value
        LPS25H_PRESS_OUT_H,  # high byte of pressure value
    ]

    # Output registers used by the temperature sensor
    lpsTempRegisters = [
        LPS25H_TEMP_OUT_L, # low byte of temperature value
        LPS25H_TEMP_OUT_H, # high byte of temperature value
    ]

    
    def __init__(self, i2c_channel=0, scl_pin=7, sda_pin=15, freq=400000, address = LPS25H_ADDR, SA0 = 1):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.channel= i2c_channel
        self.address = address | SA0
        self.pressEnabled = False
        self.initialize_sensor()
        

    def __del__(self):
        """ Clean up routines. """
        try:
            # Power down device
            valueOld = self._ReadRegister(self.address, LPS25H_CTRL_REG1)
            self._WriteRegister(self.address, LPS25H_CTRL_REG1, 0x00)
            print("valueOld = {}".format(valueOld))
        except:
            pass
        
    
    def initialize_sensor(self):
        # Start by resetting the sensor to ensure a clean state
        self.reset()
        # Check WhoAmI register
        if self.WhoAmI() != b'\xbd':
            raise OSError(f"LPS25H not found at address {hex(self.address)}")

        # Configure sensor as needed, for example, setting output data rate
        self._WriteRegister(LPS25H_CTRL_REG1, 0xC0)  # Example setting #0xC4
        
    
    def reset(self):
        # Reset the device
        self._WriteRegister(LPS25H_CTRL_REG2, 0x84)


    def _ReadRegister(self, reg):
        # Read a single byte from a given register
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]


    def _WriteRegister(self, reg, dat):
        # Write a single byte to a given register
        self.i2c.writeto_mem(self.address, reg, bytes([dat]))


    def ReadRegister2(self, reg):
        a = self._ReadRegister(reg)
        b = self._ReadRegister(reg + 1)
        return a + b * 256


    def _getSensorRawLoHi1(self, address, outRegs):
        """ Return a scalar representing the combined raw signed 16 bit
        value of the output registers of a one-dimensional sensor,
        e.g. temperature.
        """
        # Read register outputs and combine low and high byte values
        tl = self._ReadRegister(outRegs[0])
        th = self._ReadRegister(outRegs[1])
        
        tVal = self._combineSignedLoHi(tl, th)

        # Return the scalar
        return tVal if tVal < 32768 else (tVal - 65536)


    def _getSensorRawXLoLoHi1(self, address, outRegs):
        """ Return a scalar representing the combined raw signed 24 bit
        value of the output registers of a one-dimensional sensor,
        e.g. temperature.
        """
        # Read register outputs and combine low and high byte values
        pxl = self._ReadRegister(outRegs[0])
        pl = self._ReadRegister(outRegs[1])
        ph = self._ReadRegister(outRegs[2])

        pVal = self._combineSignedXLoLoHi(pxl, pl, ph)
        # Return the scalar
        return pVal if pVal < 8388608 else (pVal - 16777216)


    def _combineLoHi(self, loByte, hiByte):
        """ Combine low and high bytes to an unsigned 16 bit value. """
        return (loByte | hiByte << 8)


    def _combineSignedLoHi(self, loByte, hiByte):
        """ Combine low and high bytes to a signed 16 bit value. """
        combined = self._combineLoHi (loByte, hiByte)
        return combined if combined < 32768 else (combined - 65536)


    def _combineXLoLoHi(self, xloByte, loByte, hiByte):
        """ Combine extra low, low, and high bytes to an unsigned 24 bit
            value.
        """
        return (xloByte | loByte << 8 | hiByte << 16)


    def _combineSignedXLoLoHi(self, xloByte, loByte, hiByte):
        """ Combine extra low, low, and high bytes to a signed 24 bit
            value.
        """
        combined = self._combineXLoLoHi(xloByte, loByte, hiByte)
        return combined if combined < 8388608 else (combined - 16777216)


    def getLPSTemperatureRaw(self):
        """ Return the raw temperature value. """
        # Check if device has been set up        
        if not self.pressEnabled:
            raise(Exception('Temperature sensor has to be enabled first'))

        return self._getSensorRawLoHi1(self.address, LPS25H.lpsTempRegisters)


    def getBarometerRaw(self):
        """ Return the raw pressure sensor data. """
        # Check if device has been set up
        if not self.pressEnabled:
            raise(Exception('Barometer has to be enabled first'))

        # Return sensor data as signed 24 bit value
        return self._getSensorRawXLoLoHi1(self.address, LPS25H.lpsPressRegisters)


    def getBarometerMillibars(self, rounded = True):
        """ Return the barometric pressure in millibars (mbar)
            (same as hectopascals (hPa)).
        """
        if rounded:
            return round(self.getBarometerRaw() / 4096.0, 3)
        return self.getBarometerRaw() / 4096.0


    def getLPSTemperatureCelsius(self, rounded = True):
        """ Return the temperature sensor reading in C as a floating
            point number rounded to one decimal place.
        """
        # According to the datasheet, the raw temperature value is 0
        # @ 42.5 degrees Celsius and the resolution of the sensor is 480
        # steps per degree Celsius.
        # Thus, the following statement should return the temperature in
        # degrees Celsius.
        if rounded:
            return round(42.5 + self.getLPSTemperatureRaw() / 480.0, 3)
        return 42.5 + self.getLPSTemperatureRaw() / 480.0


    def getAltitude(self, altimeterMbar = 1013.25, rounded = True):
        """ Return the altitude in meters above the standard pressure
            level of 1013.25 hPa, calculated using the 1976 US Standard
            Atmosphere model.
            altimeterMbar can be adjusted to the actual pressure
            "adjusted to sea level" (QNH) to compensate for regional
            and/or weather-based variations.
        """
        altitude = (1 - pow(self.getBarometerMillibars(rounded = False) / altimeterMbar, 0.190263)) * 44330.8
        if rounded:
            return round(altitude, 2)
        return altitude


    def poweroff(self):
        t = self._ReadRegister(LPS25H_CTRL_REG1) & 0x7F
        self._WriteRegister(LPS25H_CTRL_REG1, t)

    def poweron(self):
        t = self._ReadRegister(LPS25H_CTRL_REG1) | 0xC0
        self._WriteRegister(LPS25H_CTRL_REG1, t)


    def enableLPS(self):
        """ Enable and set up the given sensors in the IMU device. """
        # Power down device first
        self.poweroff()
        #self._WriteRegister(self.address, LPS25H_CTRL_REG1, 0x00)

        # Barometer and temperature sensor
        # (Both sensors are enabled together on the LPS25H)
        # CTRL_REG1
        # Power up
        # Output data rate for both sensors 
        # 10110000 = 0xb0 - 12.5Hz
        # 11000000 = 0xc0 - 25.0Hz
        self.poweron()
        #self._WriteRegister(self.address, LPS25H_CTRL_REG1, 0xb0)

        self.pressEnabled = True
        
        
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

    def read_altitude(self):
        """
        Reads the altitude in meters from the LPS25H sensor and validates it.
        """
        try:
            alt_data = self.getAltitude()
            if self.validate_altitude(alt_data):
                return alt_data
            else:
                return None  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read altitude from LPS25H: {e}")
            return {}  # Return an empty dictionary in case of error

    def read_pressure(self):
        """
        Reads the pressure in mBars from the LPS25H sensor and validates it.
        """
        try:
            pres_data = self.getBarometerMillibars()
            if self.validate_pressure(pres_data):
                return pres_data
            else:
                return None  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read pressure from LPS25H: {e}")
            return {}  # Return an empty dictionary in case of error

    def read_temperature(self):
        """
        Reads the temperature in Celsius degrees from the LPS25H sensor and validates it.
        """
        try:
            temp_data = self.getLPSTemperatureCelsius()
            if self.validate_temperature(temp_data):
                return temp_data
            else:
                return None  # Or handle as needed
        except Exception as e:
            print(f"ERROR - Failed to read temperatture from LPS25H: {e}")
            return {}  # Return an empty dictionary in case of error


    # get/set Reference pressure
    def REF_PRESS(self, ref=''):
        if ref=='':
            return self.ReadRegister2(LPS25H_REF_P_L)
        else:
            self._WriteRegister(self.address, LPS25H_REF_P_L, ref%256)
            self._WriteRegister(self.address, LPS25H_REF_P_H, ref//256)


    # Device identification
    def WhoAmI(self):
        return bytes([self._ReadRegister(LPS25H_WHO_AM_I)])


    # get/set Pressure and temperature resolution
    def RES_CONF(self, res=''):
        if res=='':
            return self._ReadRegister(self.address, LPS25H_RES_CONF)
        else:
            self._WriteRegister(self.address, LPS25H_RES_CONF, res)


    # get/set Control register 1
    def CTRL_REG1(self, reg=''):
        if reg=='':
            return self._ReadRegister(self.address, LPS25H_CTRL_REG1)
        else:
            self._WriteRegister(self.address, LPS25H_CTRL_REG1, reg)


    # get/set Control register 2
    def CTRL_REG2(self, reg=''):
        if reg=='':
            return self._ReadRegister(self.address, LPS25H_CTRL_REG2)
        else:
            self._WriteRegister(self.address, LPS25H_CTRL_REG2, reg)


    # get/set Control register 3
    def CTRL_REG3(self, reg=''):
        if reg=='':
            return self._ReadRegister(self.address, LPS25H_CTRL_REG3)
        else:
            self._WriteRegister(self.address, LPS25H_CTRL_REG3, reg)


    # get/set Control register 4
    def CTRL_REG4(self, reg=''):
        if reg=='':
            return self._ReadRegister(self.address, LPS25H_CTRL_REG4)
        else:
            self._WriteRegister(self.address, LPS25H_CTRL_REG4, reg)


    # get/set Interrupt configuration
    def INTERRUPT_CFG(self, cfg=''):
        if cfg=='':
            return self._ReadRegister(self.address, LPS25H_INT_CFG)
        else:
            self._WriteRegister(self.address, LPS25H_INT_CFG, cfg)


    # get/set Interrupt source
    def INT_SOURCE(self, src=''):
        if src=='':
            return self._ReadRegister(self.address, LPS25H_INT_SOURCE)
        else:
            self._WriteRegister(self.address, LPS25H_INT_SOURCE, src)


    # get Status register
    def STATUS(self):
        return self._ReadRegister(self.address, LPS25H_STATUS_REG)


    # get/set FIFO control
    def FIFO_CTRL(self, fifo=''):
        if fifo=='':
            return self._ReadRegister(self.address, LPS25H_FIFO_CTRL)
        else:
            self._WriteRegister(self.address, LPS25H_FIFO_CTRL, fifo)


    # get FIFO_STATUS
    def FIFI_STATUS(self):
        return self._ReadRegister(self.address, LPS25H_FIFO_STATUS)


    # get/set Threshold pressure
    def THS_PRESS(self, ths=''):
        if ths=='':
            return self.ReadRegister2(LPS25H_THS_P_L)
        else:
            self._WriteRegister(self.address, LPS25H_THS_P_L, ths%256)
            self._WriteRegister(self.address, LPS25H_THS_P_H, ths//256)

    
    # get/set Pressure offset
    def RPDS(self, rpds=''):
        if rpds=='':
            return self.ReadRegister2(LPS25H_RPDS_L)
        else:
            self._WriteRegister(self.address, LPS25H_RPDS_L, rpds%256)
            self._WriteRegister(self.address, LPS25H_RPDS_H, rpds//256)
            
    # Read pressure in hPa
    def read_pres(self):
        xl = _ReadRegister(LPS25H_ADDR, PRESS_OUT_XL)
        l = _ReadRegister(LPS25H_ADDR, PRESS_OUT_L)
        h = _ReadRegister(LPS25H_ADDR, PRESS_OUT_H)
        # Combine bytes to form the raw pressure value
        pressure_raw = xl + (l << 8) + (h << 16)
        # Convert to hPa
        return pressure_raw / 4096.0

    # Read temperature in degrees Celsius
    def read_temp(self):
        l = _ReadRegister(LPS25H_ADDR, TEMP_OUT_L)
        h = _ReadRegister(LPS25H_ADDR, TEMP_OUT_H)
        # Combine bytes to form the raw temperature value
        temp_raw = (l + (h << 8))
        # Handle sign (16-bit signed)
        if temp_raw > 32767:
            temp_raw -= 65536
        # Calculate actual temperature
        return 42.5 + temp_raw / 480.0
            
            
class BME688:
    BME68X_ENABLE_HEATER = const(0x00)
    BME68X_DISABLE_HEATER = const(0x08) # const(0x01)
    BME68X_DISABLE_GAS_MEAS = const(0x00)
    BME68X_ENABLE_GAS_MEAS_L = const(0x01)
    BME68X_ENABLE_GAS_MEAS_H = const(0x02)
    BME68X_SLEEP_MODE = const(0)
    BME68X_FORCED_MODE = const(1)
    BME68X_VARIANT_GAS_LOW = const(0x00)
    BME68X_VARIANT_GAS_HIGH = const(0x01)
    BME68X_HCTRL_MSK = const(0x08)
    BME68X_HCTRL_POS = const(3)
    BME68X_NBCONV_MSK = const(0x0F)
    BME68X_RUN_GAS_MSK = const(0x30)
    BME68X_RUN_GAS_POS = const(4)
    BME68X_MODE_MSK = const(0x03)
    BME68X_PERIOD_POLL = const(10000)
    BME68X_REG_CTRL_GAS_0 = const(0x70)
    BME68X_REG_CTRL_GAS_1 = const(0x71)
    
    BME680_CHIPID = const(0x61)

    BME680_REG_CHIPID = const(0xD0)
    BME68X_REG_VARIANT = const(0xF0)
    BME680_BME680_COEFF_ADDR1 = const(0x89)
    BME680_BME680_COEFF_ADDR2 = const(0xE1)
    BME680_BME680_RES_HEAT_0 = const(0x5A)
    BME680_BME680_GAS_WAIT_0 = const(0x64)

    BME680_REG_SOFTRESET = const(0xE0)
    BME680_REG_CTRL_GAS = const(0x71)
    BME680_REG_CTRL_HUM = const(0x72)
    BME680_REG_STATUS = const(0xF3) #const(0x73)
    BME680_REG_CTRL_MEAS = const(0x74)
    BME680_REG_CONFIG = const(0x75)
    BME680_REG_PAGE_SELECT = const(0x73)

    BME680_REG_MEAS_STATUS = const(0x1D)
    BME680_REG_PDATA = const(0x1F)
    BME680_REG_TDATA = const(0x22)
    BME680_REG_HDATA = const(0x25)

    BME680_SAMPLERATES = (0, 1, 2, 4, 8, 16)
    BME680_FILTERSIZES = (0, 1, 3, 7, 15, 31, 63, 127)

    BME680_RUNGAS = const(0x10)
    
    LOOKUP_TABLE_1 = (2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0,
  2126008810.0, 2147483647.0, 2130303777.0, 2147483647.0, 2147483647.0,
  2143188679.0, 2136746228.0, 2147483647.0, 2126008810.0, 2147483647.0,
  2147483647.0)
    LOOKUP_TABLE_2 = (
        4096000000.0,
        2048000000.0,
        1024000000.0,
        512000000.0,
        255744255.0,
        127110228.0,
        64000000.0,
        32258064.0,
        16016016.0,
        8000000.0,
        4000000.0,
        2000000.0,
        1000000.0,
        500000.0,
        250000.0,
        125000.0,
    )

    
    
    def __init__(self, i2c_channel=0, scl_pin=7, sda_pin=15, address=0x77, refresh_rate=10):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        # self.pressEnabled = False
        self.channel = i2c_channel
        self.init_sensor()
        
        # Get variant
        #self.chip_variant = self.read_register(BME68X_REG_VARIANT, 1)[0]
        
        self.read_calibration()
        
        # set up heater
        self.write_register(BME680_BME680_RES_HEAT_0, [0x73])
        self.write_register(BME680_BME680_GAS_WAIT_0, [0x65])

        self.sea_level_pressure = 1013.25
        """Pressure in hectoPascals at sea level. Used to calibrate :attr:`altitude`."""
        
        # Default oversampling and filter register values.
        self._humidity_oversample = 0b010 # 0b010 was for 2x
        self._temp_oversample = 0b100 # 0b100 was for 16x
        self._pressure_oversample = 0b011 # 0b011 was for 8x, then 0b100 for 8x

        self.filter = 0b010
        
        # Gas measurements, as a mask applied to _BME680_RUNGAS
        #self.run_gas = 0xFF

        self.adc_pres = None
        self.adc_temp = None
        self.adc_hum = None
        self.adc_gas = None
        self.gas_range = None
        self.t_fine = None

        self.last_reading = 0
        self.min_refresh_time = 1000 / refresh_rate

        #self.amb_temp = 25  # Copy required parameters from reference bme68x_dev struct
        #self.set_gas_heater(320, 150)  # heater 320 deg C for 150 msec
        

    def init_sensor(self):
        # Initialize the sensor with the necessary setup values
        # Example: reset command, setting up oversampling, filter settings, etc.
        self.write_register(BME680_REG_SOFTRESET, [0xb6])  # Soft reset command
        time.sleep(0.005)  # Wait for the reset to complete
        
#         # Check device ID.
#         try:
#             # Assuming read_register returns a list of bytes, we take the first byte.
#             chip_id_bytes = self.read_register(BME680_REG_CHIPID, 1)
#             chip_id = chip_id_bytes[0] if isinstance(chip_id_bytes, list) else chip_id_bytes
#             if ord(chip_id) != BME680_CHIPID:
#                 raise RuntimeError(f"Failed to find BME680! Chip ID {hex(ord(chip_id))}")
#         except Exception as e:
#             log.log_event("ERROR", f"Error during sensor initialization: {str(e)}")
#             raise
        
        try:
            chip_id = self.read_byte(BME680_REG_CHIPID)
            if chip_id != BME680_CHIPID:
                raise RuntimeError('Failed 0x%x' % chip_id)
        except Exception as e:
            log.log_event("ERROR", f"Error during sensor initialization: {str(e)}")
            raise
        
        
        
    def read_calibration(self) -> None:
        """Read & save the calibration coefficients"""
        coeff = self.read(BME680_BME680_COEFF_ADDR1, 25)
        coeff += self.read(BME680_BME680_COEFF_ADDR2, 16)

        coeff = list(struct.unpack('<hbBHhbBhhbbHhhBBBHbbbBbHhbb', bytes(coeff[1:39])))
        # print("\n\n",coeff)
        coeff = [float(i) for i in coeff]
        self.temp_calibration = [coeff[x] for x in [23, 0, 1]]
        self.pressure_calibration = [coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
        self.humidity_calibration = [coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]]
        self.gas_calibration = [coeff[x] for x in [25, 24, 26]]
        # flip around H1 & H2
        self.humidity_calibration[1] *= 16
        self.humidity_calibration[1] += self.humidity_calibration[0] % 16
        self.humidity_calibration[0] /= 16

        #byte_data = self.read_register(0x02, 1)[0]  # Extract the integer value from the bytes
        self.heat_range = (self.read_byte(0x02) & 0x30) / 16
        self.heat_val = self.read_byte(0x00)
        self.sw_err = (self.read_byte(0x04) & 0xF0) / 16
    
#         self.heat_val = self.read_register(0x00, 1)[0]
#         byte_data = self.read_register(0x04, 1)[0]  # Extract the integer value from the bytes
#         self.sw_err = (byte_data & 0xF0) / 16

    def write_register(self, register, values):
        self.i2c.writeto_mem(self.address, register, bytes(values))
        
    def write(self, register, values):
        for value in values:
          self.i2c.writeto_mem(self.address, register, bytearray([value & 0xFF]))
          register += 1
          
    def read(self, register, length):
        result = bytearray(length)
        self.i2c.readfrom_mem_into(self.address, register & 0xff, result)
        return result
    
    def read_byte(self, register):
        return self.read(register, 1)[0]

    def read_register(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)
    
    def perform_reading(self) -> None:
        """Perform a single-shot reading from the sensor and fill internal data structure for
        calculations"""
#         if time.monotonic() - self.last_reading < self.min_refresh_time:
#             return
#         current_ticks = utime.ticks_ms()
#         if utime.ticks_diff(current_ticks, self.last_reading) < self.min_refresh_time:
#             return
        if (time.ticks_diff(self.last_reading, time.ticks_ms()) * time.ticks_diff(0, 1) < self.min_refresh_time):
          return

        # set filter
        self.write(BME680_REG_CONFIG, [self.filter << 2])
        # turn on temp oversample & pressure oversample
        self.write(
            BME680_REG_CTRL_MEAS,
            [(self._temp_oversample << 5)|(self._pressure_oversample << 2)])
        # turn on humidity oversample
        self.write(BME680_REG_CTRL_HUM, [self._humidity_oversample])
        # gas measurements enabled
        self.write(BME680_REG_CTRL_GAS, [BME680_RUNGAS << 1])
        
        ctrl = self.read_byte(BME680_REG_CTRL_MEAS)
        ctrl = (ctrl & 0xFC) | 0x01  # enable single shot!
        self.write(BME680_REG_CTRL_MEAS, [ctrl])
        new_data = False
        while not new_data:
            data = self.read(BME680_REG_MEAS_STATUS, 17)
            #print(f"   Data from reg: {data}")
            new_data = data[0] & 0x80 != 0
            time.sleep(0.005)
        # self.last_reading = time.monotonic()
        self.last_reading = time.ticks_ms()

        self.adc_pres = read24(data[2:5]) / 16
        self.adc_temp = read24(data[5:8]) / 16
        #print(f"   ADC from pres: {self.adc_pres}, temp: {self.adc_temp}")
        self.adc_hum = struct.unpack(">H", bytes(data[8:10]))[0]
        self.adc_gas = int(struct.unpack(">H", bytes(data[15:17]))[0] / 64)
        self.gas_range = data[16] & 0x0F

        var1 = (self.adc_temp / 8) - (self.temp_calibration[0] * 2)
        var2 = (var1 * self.temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self.temp_calibration[2] * 16) / 16384
        self.t_fine = int(var2 + var3)
    
    @property
    def temperature(self) -> float:
        """The compensated temperature in degrees Celsius."""
        self.perform_reading()
        calc_temp = ((self.t_fine * 5) + 128) / 256
        return calc_temp / 100
        
    
    @property
    def relative_humidity(self) -> float:
        """The relative humidity in RH %"""
        return self.humidity
    
    @property
    def pressure(self) -> float:
        """The barometric pressure in hectoPascals"""
        self.perform_reading()
        #print(f"Perform reading value: {self.perform_reading()}")
        var1 = (self.t_fine / 2) - 64000
        var2 = ((var1 / 4) * (var1 / 4)) / 2048
        var2 = (var2 * self.pressure_calibration[5]) / 4
        var2 = var2 + (var1 * self.pressure_calibration[4] * 2)
        var2 = (var2 / 4) + (self.pressure_calibration[3] * 65536)
        var1 = ((((var1/4)*(var1/4))/8192)*(self.pressure_calibration[2]*32)/8)+((self.pressure_calibration[1]*var1)/2)
        var1 = var1 / 262144
        var1 = ((32768 + var1) * self.pressure_calibration[0]) / 32768
        calc_pres = 1048576 - self.adc_pres
        calc_pres = (calc_pres - (var2 / 4096)) * 3125
        calc_pres = (calc_pres / var1) * 2
        var1 = (self.pressure_calibration[8]*(((calc_pres/8)*(calc_pres/8))/8192)) / 4096
        var2 = ((calc_pres / 4) * self.pressure_calibration[7]) / 8192
        var3 = (((calc_pres / 256) ** 3) * self.pressure_calibration[9]) / 131072
        calc_pres += (var1 + var2 + var3 + (self.pressure_calibration[6] * 128)) / 16
        return calc_pres / 100
    
    @property
    def humidity(self) -> float:
        """The relative humidity in RH %"""
        self.perform_reading()
        temp_scaled = ((self.t_fine * 5) + 128) / 256
        var1 = (self.adc_hum - (self.humidity_calibration[0] * 16)) - (
            (temp_scaled * self.humidity_calibration[2]) / 200
        )
        var2 = (
            self.humidity_calibration[1]
            * (
                ((temp_scaled * self.humidity_calibration[3]) / 100)
                + (
                    (
                        (
                            temp_scaled
                            * ((temp_scaled * self.humidity_calibration[4]) / 100)
                        )
                        / 64
                    )
                    / 100
                )
                + 16384
            )
        ) / 1024
        var3 = var1 * var2
        var4 = self.humidity_calibration[5] * 128
        var4 = (var4 + ((temp_scaled * self.humidity_calibration[6]) / 100)) / 16
        var5 = ((var3 / 16384) * (var3 / 16384)) / 1024
        var6 = (var4 * var5) / 2
        calc_hum = (((var3 + var6) / 1024) * 1000) / 4096
        calc_hum /= 1000  # get back to RH

        calc_hum = min(calc_hum, 100)
        calc_hum = max(calc_hum, 0)
        return calc_hum
    
    @property
    def altitude(self) -> float:
        """The altitude based on current :attr:`pressure` vs the sea level pressure
        (:attr:`sea_level_pressure`) - which you must enter ahead of time)"""
        pressure = self.pressure  # in Si units for hPascal
        return 44330 * (1.0 - math.pow(pressure / self.sea_level_pressure, 0.1903))
    
    @property
    def gas(self) -> int:
        """The gas resistance in ohms"""
        self.perform_reading()
#         if self.chip_variant == 0x01:
#             # taken from https://github.com/BoschSensortec/BME68x-Sensor-API
        var1 = 262144 >> self.gas_range
        var2 = self.adc_gas - 512
        var2 *= 3
        var2 = 4096 + var2
        calc_gas_res = (10000 * var1) / var2
        calc_gas_res = calc_gas_res * 100
#         else:
#             var1 = (
#                 (1340 + (5 * self._sw_err)) * (LOOKUP_TABLE_1[self.gas_range])
#             ) / 65536
#             var2 = ((self._adc_gas * 32768) - 16777216) + var1
#             var3 = (LOOKUP_TABLE_2[self.gas_range] * var1) / 512
#             calc_gas_res = (var3 + (var2 / 2)) / var2
        return int(calc_gas_res)
    

    def read_temperature(self):
        # Read the raw temperature data from the sensor
        data = self.read_register(0xFA, 3)  # Temperature data register
        raw_temp = (data[0] << 16 | data[1] << 8 | data[2]) >> 4
        # Convert the raw value to actual temperature
        temperature = (raw_temp / 8192.0) - 40
        return temperature

    def read_pressure(self):
        # Read the raw pressure data
        data = self.read_register(0xF7, 3)
        #print(f"Data Read: {data}") 
        raw_pres = (data[0] << 16 | data[1] << 8 | data[2]) >> 4
        # Convert the raw value to actual pressure
        pressure = raw_pres / 256.0
        print(f"rau pres: {raw_pres} => pres: {pressure}")
        return pressure

    def read_humidity(self):
        # Read the raw humidity data
        data = self.read_register(0xFD, 2)
        raw_hum = (data[0] << 8 | data[1])
        # Convert the raw value to actual humidity
        humidity = raw_hum / 1024.0
        return humidity
    
    @property
    def pressure_oversample(self) -> int:
        """The oversampling for pressure sensor"""
        return BME688.BME680_SAMPLERATES[self._pressure_oversample]
    
    @pressure_oversample.setter
    def pressure_oversample(self, sample_rate):
        if sample_rate in BME680_SAMPLERATES:
              self._pressure_oversample = BME680_SAMPLERATES.index(sample_rate)
        else:
          raise RuntimeError("Invalid")
    
    @property
    def humidity_oversample(self) -> int:
        """The oversampling for humidity sensor"""
        return BME688.BME680_SAMPLERATES[self._humidity_oversample]
    
    @property
    def temperature_oversample(self) -> int:
        """The oversampling for temperature sensor"""
        return BME688.BME680_SAMPLERATES[self._temp_oversample]
    
    @property
    def filter_size(self) -> int:
        """The filter size for the built in IIR filter"""
        return BME680_FILTERSIZES[self.filter]
    
    def set_gas_heater(self, heater_temp: int, heater_time: int) -> bool:
        """
        Enable and configure gas reading + heater (None disables)
        :param  heater_temp: Desired temperature in degrees Centigrade
        :param  heater_time: Time to keep heater on in milliseconds
        :return: True on success, False on failure
        """
        try:
            if (heater_temp is None) or (heater_time is None):
                self.set_heatr_conf(heater_temp or 0, heater_time or 0, enable=False)
            else:
                self.set_heatr_conf(heater_temp, heater_time)
        except OSError:
            return False
        return True
    
    def set_heatr_conf(
        self, heater_temp: int, heater_time: int, enable: bool = True
    ) -> None:
        # restrict to BME68X_FORCED_MODE
        op_mode: int = BME68X_FORCED_MODE
        nb_conv: int = 0
        hctrl: int = BME68X_ENABLE_HEATER
        run_gas: int = 0
        ctrl_gas_data_0: int = 0
        ctrl_gas_data_1: int = 0
        try:
            self.set_op_mode(BME68X_SLEEP_MODE)
            self.set_conf(heater_temp, heater_time, op_mode)
            ctrl_gas_data_0 = self.read_register(BME68X_REG_CTRL_GAS_0, 1)[0]
            ctrl_gas_data_1 = self.read_register(BME68X_REG_CTRL_GAS_1, 1)[0]
            if enable:
                hctrl = BME68X_ENABLE_HEATER
                if self.chip_variant == BME68X_VARIANT_GAS_HIGH:
                    run_gas = BME68X_ENABLE_GAS_MEAS_H
                else:
                    run_gas = BME68X_ENABLE_GAS_MEAS_L
            else:
                hctrl = BME68X_DISABLE_HEATER
                run_gas = BME68X_DISABLE_GAS_MEAS
            self.run_gas = ~(run_gas - 1)

            ctrl_gas_data_0 = bme_set_bits(
                ctrl_gas_data_0, BME68X_HCTRL_MSK, BME68X_HCTRL_POS, hctrl
            )
            ctrl_gas_data_1 = bme_set_bits_pos_0(
                ctrl_gas_data_1, BME68X_NBCONV_MSK, nb_conv
            )
            ctrl_gas_data_1 = bme_set_bits(
                ctrl_gas_data_1, BME68X_RUN_GAS_MSK, BME68X_RUN_GAS_POS, run_gas
            )
            self.write_register(BME68X_REG_CTRL_GAS_0, [ctrl_gas_data_0])
            self.write_register(BME68X_REG_CTRL_GAS_1, [ctrl_gas_data_1])
            # HELP check this
        finally:
            self.set_op_mode(BME68X_FORCED_MODE)
            
    def set_op_mode(self, op_mode: int) -> None:
        """
        * @brief This API is used to set the operation mode of the sensor
        """
        tmp_pow_mode: int = 0
        pow_mode: int = BME68X_FORCED_MODE
        # Call until in sleep

        # was a do {} while() loop
        while pow_mode != BME68X_SLEEP_MODE:
            tmp_pow_mode = self.read_register(BME680_REG_CTRL_MEAS, 1)[0]
            # Put to sleep before changing mode
            pow_mode = tmp_pow_mode & BME68X_MODE_MSK
            if pow_mode != BME68X_SLEEP_MODE:
                tmp_pow_mode &= ~BME68X_MODE_MSK  # Set to sleep
                self.write_register(BME680_REG_CTRL_MEAS, [tmp_pow_mode])
                # dev->delay_us(_BME68X_PERIOD_POLL, dev->intf_ptr)  # HELP
                delay_microseconds(BME68X_PERIOD_POLL)
        # Already in sleep
        if op_mode != BME68X_SLEEP_MODE:
            tmp_pow_mode = (tmp_pow_mode & ~BME68X_MODE_MSK) | (
                op_mode & BME68X_MODE_MSK
            )
            self.write_register(BME680_REG_CTRL_MEAS, [tmp_pow_mode])
            
    def set_conf(self, heater_temp: int, heater_time: int, op_mode: int) -> None:
        """
        This internal API is used to set heater configurations
        """

        if op_mode != BME68X_FORCED_MODE:
            raise OSError("GasHeaterException: _set_conf not forced mode")
        rh_reg_data: int = self.calc_res_heat(heater_temp)
        gw_reg_data: int = self.calc_gas_wait(heater_time)
        self.write_register(BME680_BME680_RES_HEAT_0, [rh_reg_data])
        self.write_register(BME680_BME680_GAS_WAIT_0, [gw_reg_data])
        
    def calc_res_heat(self, temp: int) -> int:
        """
        This internal API is used to calculate the heater resistance value using float
        """
        gh1: int = self.gas_calibration[0]
        gh2: int = self.gas_calibration[1]
        gh3: int = self.gas_calibration[2]
        htr: int = self.heat_range
        htv: int = self.heat_val
        amb: int = self.amb_temp

        temp = min(temp, 400)  # Cap temperature

        var1: int = ((int(amb) * gh3) / 1000) * 256
        var2: int = (gh1 + 784) * (((((gh2 + 154009) * temp * 5) / 100) + 3276800) / 10)
        var3: int = var1 + (var2 / 2)
        var4: int = var3 / (htr + 4)
        var5: int = (131 * htv) + 65536
        heatr_res_x100: int = int(((var4 / var5) - 250) * 34)
        heatr_res: int = int((heatr_res_x100 + 50) / 100)

        return heatr_res

    def calc_res_heat(self, temp: int) -> int:
        """
        This internal API is used to calculate the heater resistance value
        """
        gh1: float = float(self.gas_calibration[0])
        gh2: float = float(self.gas_calibration[1])
        gh3: float = float(self.gas_calibration[2])
        htr: float = float(self.heat_range)
        htv: float = float(self.heat_val)
        amb: float = float(self.amb_temp)

        temp = min(temp, 400)  # Cap temperature

        var1: float = (gh1 / (16.0)) + 49.0
        var2: float = ((gh2 / (32768.0)) * (0.0005)) + 0.00235
        var3: float = gh3 / (1024.0)
        var4: float = var1 * (1.0 + (var2 * float(temp)))
        var5: float = var4 + (var3 * amb)
        res_heat: int = int(
            3.4 * ((var5 * (4 / (4 + htr)) * (1 / (1 + (htv * 0.002)))) - 25)
        )
        return res_heat
    
    def calc_gas_wait(self, dur: int) -> int:
        """
        This internal API is used to calculate the gas wait
        """
        factor: int = 0
        durval: int = 0xFF  # Max duration

        if dur >= 0xFC0:
            return durval
        while dur > 0x3F:
            dur = dur / 4
            factor += 1
        durval = int(dur + (factor * 64))
        return durval
    
