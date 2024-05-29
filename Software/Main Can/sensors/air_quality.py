from machine import I2C, Pin

# default address
CCS811_ADDR = const(0x5B) # or 0x5A

# Commands
CCS811_STATUS = const(0x00)
CCS811_MEAS_MODE = const(0x01)
CCS811_ALG_RESULT_DATA = const(0x02)
CCS811_RAW_DATA = const(0x03)
CCS811_ENV_DATA = const(0x05)
CCS811_NTC = const(0x06)
CCS811_THRESHOLDS = const(0x10)
CCS811_BASELINE = const(0x11)
CCS811_HW_ID = const(0x20)
CCS811_HW_VERSION = const(0x21)
CCS811_FW_BOOT_VERSION = const(0x23)
CCS811_FW_APP_VERSION = const(0x24)
CCS811_ERROR_ID = const(0xE0)
CCS811_APP_START = const(0xF4)
CCS811_SW_RESET = const(0xFF)

# CCS811_REF_RESISTOR = const(100000)

class AirQualitySensor:
    def __init__(self):
        # Initialize BME688 for air quality
        pass

    def read_quality(self):
        # Return air quality data
        pass
    
    def read_pressure(self):
        # Return air quality data
        pass
    
class CCS811:
    """CCS811 gas sensor. Measures eCO2 in ppm and TVOC in ppb"""

    def __init__(self, i2c_channel=0, scl_pin=7, sda_pin=15, freq=400000, address=CCS811_ADDR):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        self.tVOC = 0
        self.eCO2 = 0
        self.configure_ccs811()

    def print_error(self):
        """Error code. """

        error = self.i2c.readfrom_mem(self.address, CCS811_ERROR_ID, 1)
        message = 'Error: '

        if (error[0] >> 5) & 1:
            message += 'HeaterSupply '
        elif (error[0] >> 4) & 1:
            message += 'HeaterFault '
        elif (error[0] >> 3) & 1:
            message += 'MaxResistance '
        elif (error[0] >> 2) & 1:
            message += 'MeasModeInvalid '
        elif (error[0] >> 1) & 1:
            message += 'ReadRegInvalid '
        elif (error[0] >> 0) & 1:
            message += 'MsgInvalid '

        print(message)
        
    def configure_ccs811(self):
        try:
            # Check that the HW id is correct
            hardware_id = self.i2c.readfrom_mem(self.address, CCS811_HW_ID, 1)
            # print(hardware_id)

            if (hardware_id[0] != 0x81):
                raise ValueError('CCS811 not found. Please check wiring. Pull nWake to ground.')

            if self.check_for_error():
                self.print_error()
                raise ValueError('Error at Startup.')

            if not self.app_valid():
                raise ValueError('Error: Application not valid.')

            self.i2c.writeto(self.address, bytes([CCS811_APP_START]))

            if self.check_for_error():
                self.print_error()
                raise ValueError('Error at AppStart.')

            self.set_drive_mode(0x18)

            if self.check_for_error():
                self.print_error()
                raise ValueError('Error at setDriveMode.')
        except OSError as e:
            print(f"Failed to initialize CCS811: {e}")
            raise
    
    def get_base_line(self):

        b = self.i2c.readfrom_mem(self.address, CCS811_BASELINE, 2)
        baselineMSB = b[0]
        baselineLSB = b[1]
        baseline = (baselineMSB << 8) | baselineLSB
        return baseline

    def check_for_error(self):
        value = self.i2c.readfrom_mem(self.address, CCS811_STATUS, 1)
        v = ((value[0] >> 0) & 1)

        return ((value[0] >> 0) & 1)

    def app_valid(self):
        value = self.i2c.readfrom_mem(self.address, CCS811_STATUS, 1)
        v = ((value[0] >> 4) & 1)

        return ((value[0] >> 4) & 1)

    def set_drive_mode(self, mode):
        
        self.i2c.writeto_mem(self.address, CCS811_MEAS_MODE, bytes([mode]))

    def data_available(self):

        status = self.i2c.readfrom_mem(self.address, 0x00, 1)
        value = self.i2c.readfrom_mem(self.address, CCS811_STATUS, 1)

        return value[0] << 3

    def readeCO2(self):
        """ Equivalent Carbone Dioxide in parts per millions. Clipped to 400 to 8192ppm."""

        if self.data_available():

            d = self.i2c.readfrom_mem(self.address, CCS811_ALG_RESULT_DATA, 4)

            co2MSB = d[0]
            co2LSB = d[1]

            return ((co2MSB << 8) | co2LSB)

        elif self.check_for_error():
                self.print_error()

    def readtVOC(self):
        """ Total Volatile Organic Compound in parts per billion. """

        if self.data_available():

            d = self.i2c.readfrom_mem(self.address, CCS811_ALG_RESULT_DATA, 4)

            tvocMSB = d[2]
            tvocLSB = d[3]

            return ((tvocMSB << 8) | tvocLSB)

        elif self.check_for_error():
                self.print_error()

    def readValues(self):
        """ Total Volatile Organic Compound in parts per billion. """

        if self.data_available():

            d = self.i2c.readfrom_mem(self.address, CCS811_ALG_RESULT_DATA, 4)

            co2MSB = d[0]
            co2LSB = d[1]
            tvocMSB = d[2]
            tvocLSB = d[3]

            self.eCO2 = ((co2MSB << 8) | co2LSB)
            self.tVOC = ((tvocMSB << 8) | tvocLSB)

            return True

        elif self.check_for_error():
            self.print_error()
            return False

    def reset(self):
        """ Initiate a software reset. """

        seq = bytearray([0x11, 0xE5, 0x72, 0x8A])
        self.i2c.writeto_mem(self.address, CCS811_SW_RESET, seq)
        
    def read_quality(self):
        """
        Reads the air quality data from the CCS811 sensor and validates it.
        """
        try:
            if self.readValues():
                return {'eCO2': self.eCO2, 'tVOC' : self.tVOC}
            else:
                return {'eCO@': None, 'tVOC': None}
        except Exception as e:
            logger.error(f"Failed to read temperature from MCP9808: {e}")
            return {}  # Return an empty dictionary in case of error
