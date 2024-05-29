# Imports
from micropython import const
from machine import I2C, Pin
import config
import time
import struct
from utils.logger import Logger

log = Logger()

class MPU9250:
    
    # MPU9250 Registers
    MPU9250_ADDR = 0x68
    AK8963_ADDR = 0x6B
    SMPLRT_DIV = 0x19
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    ACCEL_XOUT_H = 0x3B
    ACCEL_YOUT_H = 0x3D
    ACCEL_ZOUT_H = 0x3F
    TEMP_OUT_H = 0x41
    GYRO_XOUT_H = 0x43
    GYRO_YOUT_H = 0x45
    GYRO_ZOUT_H = 0x47
    PWR_MGMT_1 = 0x6B
    WHO_AM_I = 0x75
    
    # AK8963 registers (magnetometer inside MPU9250)
    AK8963_CNTL1 = 0x0A
    AK8963_HXL = 0x03
    
    # Constants for setting the accelerometer sensitivity
    ACCEL_FS_SEL_2G = 0x00  # ±2g configuration byte
    ACCEL_FS_SEL_4G = 0x08  # ±4g configuration byte
    ACCEL_FS_SEL_8G = 0x10  # ±8g configuration byte
    ACCEL_FS_SEL_16G = 0x18  # ±16g configuration byte
    
    # Constants for setting the accelerometer sensitivity
    GYRO_FS_SEL_250DPS = 0x00  # ±2g configuration byte
    GYRO_FS_SEL_500DPS = 0x08  # ±4g configuration byte
    GYRO_FS_SEL_1000DPS = 0x10  # ±8g configuration byte
    GYRO_FS_SEL_2000DPS = 0x18  # ±16g configuration byte
    
    # Scale factors for each sensitivity setting
    ACCEL_SENSITIVITY_SCALE_FACTOR = {
        ACCEL_FS_SEL_2G: 16384.0,
        ACCEL_FS_SEL_4G: 8192.0,
        ACCEL_FS_SEL_8G: 4096.0,
        ACCEL_FS_SEL_16G: 2048.0,
    }
    
    # Config name for each sensitivity setting
    SENSITIVITY_SCALE_NAME = {
        ACCEL_FS_SEL_2G: '±2g configuration',
        ACCEL_FS_SEL_4G: '±4g configuration',
        ACCEL_FS_SEL_8G: '±8g configuration',
        ACCEL_FS_SEL_16G: '±16g configuration',
    }
    
    GYRO_SENSITIVITY_SCALE_FACTOR = {
        GYRO_FS_SEL_250DPS: 131.0,    # ±250dps
        GYRO_FS_SEL_500DPS: 65.5,     # ±500dps
        GYRO_FS_SEL_1000DPS: 32.8,     # ±1000dps
        GYRO_FS_SEL_2000DPS: 16.4      # ±2000dps
    }
        
    def __init__(self, i2c_channel=0, scl_pin=7, sda_pin=15):
        # Initialize the MPU-9250 sensor
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = MPU9250.MPU9250_ADDR
        self.initialize_sensor()
        # Initialize sensitivity adjustment attributes
        self.ASAX = 1.0
        self.ASAY = 1.0
        self.ASAZ = 1.0

        # Read the sensitivity adjustments from the sensor
        self.read_sensitivity_adjustments()
        
    def initialize_sensor(self):
        # Wake up the MPU-9250
        self.i2c.writeto_mem(self.address, MPU9250.PWR_MGMT_1, b'\x00')
        # Check WHO_AM_I register
        # Accept either commonly expected values for MPU9250 or its variants
        who_am_i = self.i2c.readfrom_mem(self.address, self.WHO_AM_I, 1)[0]
        print(who_am_i)
        if who_am_i not in [0x71, 0x68, 0xEA, 0x40]:
            raise Exception("Unexpected WHO_AM_I response. MPU9250 not responding or incorrect address.")

        # Reset magnetometer
        self.i2c.writeto_mem(self.AK8963_ADDR, self.AK8963_CNTL1, b'\x00')
        time.sleep(0.01)  # Wait at least 100 microseconds
        # Set to continuous measurement mode 2
        self.i2c.writeto_mem(self.AK8963_ADDR, self.AK8963_CNTL1, b'\x16')
        time.sleep(0.01)  # Delay to ensure settings are applied
        
        # Set accelerometer range
        self.set_accel_config(self.ACCEL_FS_SEL_16G)
        # Set gyroscope range
        self.set_gyro_config(self.GYRO_FS_SEL_2000DPS)
        
    def get_accel_config(self):
        # Read the current accelerometer configuration
        config = self.i2c.readfrom_mem(self.address, self.ACCEL_CONFIG, 1)
        return config[0]
    
    def get_gyro_config(self):
        # Read the current accelerometer configuration
        config = self.i2c.readfrom_mem(self.address, self.GYRO_CONFIG, 1)
        return config[0]
    
    def set_accel_config(self, config_value):
        valid_configs = [self.ACCEL_FS_SEL_2G, self.ACCEL_FS_SEL_4G, self.ACCEL_FS_SEL_8G, self.ACCEL_FS_SEL_16G]
        if config_value in valid_configs:
            # Write to the accelerometer configuration register
            self.i2c.writeto_mem(self.address, self.ACCEL_CONFIG, bytes([config_value]))
            # After setting the config, read it back to verify
            current_config = self.get_accel_config()
            config_name = self.SENSITIVITY_SCALE_NAME.get(current_config, "Unknown configuration")
            print(f"Accelerometer Config set to: {config_name} ({current_config:#04x})")
        else:
            print(f"Invalid configuration value: {config_value:#04x}")
            
    def set_gyro_config(self, config_value):
        valid_configs = [self.GYRO_FS_SEL_250DPS, self.GYRO_FS_SEL_500DPS, self.GYRO_FS_SEL_1000DPS, self.GYRO_FS_SEL_1000DPS]
        if config_value in valid_configs:
            # Write to the accelerometer configuration register
            self.i2c.writeto_mem(self.address, self.GYRO_CONFIG, bytes([config_value]))
            # After setting the config, read it back to verify
            current_config = self.get_gyro_config()
            config_name = self.SENSITIVITY_SCALE_NAME.get(current_config, "Unknown configuration")
            print(f"Gyroscope Config set to: {config_name} ({current_config:#04x})")
        else:
            print(f"Invalid configuration value: {config_value:#04x}")
            
    def get_accel_scale_factor(self):
        config = self.get_accel_config() & 0x18  # Mask relevant bits for FS_SEL
        return self.ACCEL_SENSITIVITY_SCALE_FACTOR.get(config, 16384.0)  # Default to ±2g

    def get_gyro_scale_factor(self):
        config = self.get_gyro_config() & 0x18  # Mask relevant bits for FS_SEL
        return self.GYRO_SENSITIVITY_SCALE_FACTOR.get(config, 131.0)  # Default to ±2g
    
    def read_word_2c(self, addr):
        high = self.i2c.readfrom_mem(self.address, addr, 1)[0]
        low = self.i2c.readfrom_mem(self.address, addr + 1, 1)[0]
        val = (high << 8) + low
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val

    def read_acceleration(self):
        # Read accelerometer data
        x = self.read_word_2c(self.ACCEL_XOUT_H)
        y = self.read_word_2c(self.ACCEL_YOUT_H)
        z = self.read_word_2c(self.ACCEL_ZOUT_H)
        scaleFactor = self.ACCEL_SENSITIVITY_SCALE_FACTOR[self.ACCEL_FS_SEL_16G]
        return {
            'accel_x': x / scaleFactor,
            'accel_y': y / scaleFactor,
            'accel_z': z / scaleFactor
        }
    
    def read_gyroscope(self):
        x = self.read_word_2c(self.GYRO_XOUT_H)
        y = self.read_word_2c(self.GYRO_YOUT_H)
        z = self.read_word_2c(self.GYRO_ZOUT_H)
        scaleFactor = self.GYRO_SENSITIVITY_SCALE_FACTOR[self.GYRO_FS_SEL_2000DPS]
        return {
            'gyro_x': x / scaleFactor,
            'gyro_y': y / scaleFactor,
            'gyro_z': z / scaleFactor
        }
    
    def read_sensitivity_adjustments(self):
        # Set to Fuse ROM access mode to read sensitivity adjustment values
        self.i2c.writeto_mem(self.AK8963_ADDR, self.AK8963_CNTL1, b'\x1F')
        time.sleep(0.01)
        asa = self.i2c.readfrom_mem(self.AK8963_ADDR, 0x10, 3)  # Read ASAX, ASAY, ASAZ
        self.ASAX = (asa[0] - 128) / 256 + 1
        self.ASAY = (asa[1] - 128) / 256 + 1
        self.ASAZ = (asa[2] - 128) / 256 + 1
        # Return to power-down mode
        self.i2c.writeto_mem(self.AK8963_ADDR, self.AK8963_CNTL1, b'\x00')
        time.sleep(0.01)
        
    def read_magnetometer_id_info(self,address):
        # Read the Device ID from the WIA register
        device_id = self.i2c.readfrom_mem(address, 0x00, 1)
        # Read the INFO register
        device_info = self.i2c.readfrom_mem(address, 0x01, 1)

        return device_id[0], device_info[0]

    def read_magnetometer(self):
        # Ensure magnetometer is in continuous measurement mode
        self.i2c.writeto_mem(self.AK8963_ADDR, self.AK8963_CNTL1, b'\x16')
        time.sleep(0.01)  # Wait for data to be ready
        data = self.i2c.readfrom_mem(self.AK8963_ADDR, self.AK8963_HXL, 7)  # Read all 7 bytes from HXL to ST2
        
        if data[-1] & 0x08:
            print("Magnetic sensor overflow")
            return None
        
        x = int.from_bytes(data[0:2], 'little', True)
        y = int.from_bytes(data[2:4], 'little', True)
        z = int.from_bytes(data[4:6], 'little', True)
        
#         x = self.read_word_2c(self.AK8963_HXL)
#         y = self.read_word_2c(self.AK8963_HXL + 2)
#         z = self.read_word_2c(self.AK8963_HXL + 4)

        # Apply sensitivity adjustments
        x_adj = x * self.ASAX * 0.15
        y_adj = y * self.ASAY * 0.15
        z_adj = z * self.ASAZ * 0.15


        return {'mag_x': x_adj, 'mag_y': y_adj, 'mag_z': z_adj}
    



class ICM20948:
    # ICM-20948 Register Addresses and related constants
    ICM20948_ADDR = 0x68
    ICM20948_ALTERNATE_ADDR = 0x69
    WHO_AM_I = 0x00
    PWR_MGMT_1 = 0x06
    PWR_MGMT_2 = 0x07
    ACCEL_XOUT_H = 0x2D
    GYRO_XOUT_H = 0x33
    ACCEL_CONFIG = 0x14
    GYRO_CONFIG = 0x01
    GYRO_SCALE_FACTOR = 131.0

    # Constants for accelerometer and gyroscope sensitivity
    ACCEL_FS_SEL_2G = (0x00 << 1)
    ACCEL_FS_SEL_4G = (0x01 << 1)
    ACCEL_FS_SEL_8G = (0x02 << 1)
    ACCEL_FS_SEL_16G = (0x03 << 1)

    GYRO_FS_SEL_250DPS = (0x00 << 1)
    GYRO_FS_SEL_500DPS = (0x01 << 1)
    GYRO_FS_SEL_1000DPS = (0x02 << 1)
    GYRO_FS_SEL_2000DPS = (0x03 << 1)

    ACCEL_SENSITIVITY_SCALE_FACTOR = {
        ACCEL_FS_SEL_2G: 16384.0,
        ACCEL_FS_SEL_4G: 8192.0,
        ACCEL_FS_SEL_8G: 4096.0,
        ACCEL_FS_SEL_16G: 2048.0,
    }

    GYRO_SENSITIVITY_SCALE_FACTOR = {
        GYRO_FS_SEL_250DPS: 131.0,
        GYRO_FS_SEL_500DPS: 65.5,
        GYRO_FS_SEL_1000DPS: 32.8,
        GYRO_FS_SEL_2000DPS: 16.4,
    }

    def __init__(self, i2c_channel=0, scl_pin=7, sda_pin=15, address=0x68):
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin))
        if ICM20948.ICM20948_ADDR in self.i2c.scan():
            self.address = ICM20948.ICM20948_ADDR
        elif ICM20948.ICM20948_ALTERNATE_ADDR in self.i2c.scan():
            self.address = ICM20948.ICM20948_ALTERNATE_ADDR
        self.channel=i2c_channel
        self.initialize_sensor()
        self.init_icm20948()
        #log.log_event("INFO", "ICM20948 initialised", running="accelerometer.py", function="initialize_system()")

    def init_icm20948(self):
        # Reset device
        self._write_register(0x7F, 0x00)  # User Bank 0
        self._write_register(0x06, 0x01)  # Reset
        time.sleep(0.1)
        # Wake up device and disable I2C interface
        self._write_register(0x06, 0x01)  # Set clock source
        self._write_register(0x7F, 0x00)  # Select User Bank 0
        self._write_register(0x03, 0x20)  # Disable I2C interface

        # Set up I2C Master Mode to communicate with AK09916 magnetometer
        self._write_register(0x7F, 0x03)  # Select User Bank 3
        self._write_register(0x01, 0x4D)  # I2C Master mode and clock
        self._write_register(0x02, 0x07)  # I2C Master reset
        time.sleep(0.01)
        self._write_register(0x02, 0x01)  # I2C Master mode enable

        self._write_register(0x03, 0x0C)  # Set AK09916 I2C address
        self._write_register(0x04, 0x09)  # Register address to read
        self._write_register(0x05, 0x81)  # Enable reading, length=1 byte
        self._write_register(0x26, 0x01)  # Continuous read setup, burst mode

    def read_magnetometer(self):
        # Access magnetometer data via ICM-20948 I2C Master
        self._write_register(0x7F, 0x03)  # Select User Bank 3
        data = self._read_register(0x2A, 8)  # Read 6 bytes of magnetometer data

        # Convert bytes to integers
        x = self._bytes_to_int(data[1], data[0])
        y = self._bytes_to_int(data[3], data[2])
        z = self._bytes_to_int(data[5], data[4])

        return { 'mag_x': x,
                 'mag_y': y,
                 'mag_z': z }
    
    def read_magnetometer_round(self):
        # Access magnetometer data via ICM-20948 I2C Master
        self._write_register(0x7F, 0x03)  # Select User Bank 3
        data = self._read_register(0x2A, 8)  # Read 6 bytes of magnetometer data

        # Convert bytes to integers
        x = self._bytes_to_int(data[1], data[0])
        y = self._bytes_to_int(data[3], data[2])
        z = self._bytes_to_int(data[5], data[4])

        return { 'mag_x': round(x, 3),
                 'mag_y': round(y, 3),
                 'mag_z': round(z, 3) }

    def _write_register(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytearray([value]))

    def _read_register(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    def _bytes_to_int(self, msb, lsb):
        value = msb << 8 | lsb
        return value - 65536 if value > 32767 else value

    def initialize_sensor(self):
        # Reset device
        self.i2c.writeto_mem(self.address, self.PWR_MGMT_1, b'\x80')
        time.sleep(0.1)  # Wait for 100 milliseconds

        # Wake up device and disable sleep mode
        self.i2c.writeto_mem(self.address, self.PWR_MGMT_1, b'\x01')
        self.i2c.writeto_mem(self.address, self.PWR_MGMT_2, b'\x00')

        # Set accelerometer and gyroscope ranges
        self.set_accel_config(self.ACCEL_FS_SEL_16G)
        self.set_gyro_config(self.GYRO_FS_SEL_2000DPS)

        self.i2c.writeto_mem(self.address, self.GYRO_CONFIG, b'\x00')

    def set_accel_config(self, config_value):
        self.i2c.writeto_mem(self.address, self.ACCEL_CONFIG, bytes([config_value]))

    def set_gyro_config(self, config_value):
        self.i2c.writeto_mem(self.address, self.GYRO_CONFIG, bytes([config_value]))

    def read_acceleration(self):
        accel_data = self.i2c.readfrom_mem(self.address, self.ACCEL_XOUT_H, 6)
        x, y, z = struct.unpack('>hhh', accel_data)
        scaleFactor = self.ACCEL_SENSITIVITY_SCALE_FACTOR[self.get_accel_config()]
        return {
            'accel_x': x / scaleFactor,
            'accel_y': y / scaleFactor,
            'accel_z': z / scaleFactor
        }
    
    def read_acceleration_round(self):
        accel_data = self.i2c.readfrom_mem(self.address, self.ACCEL_XOUT_H, 6)
        x, y, z = struct.unpack('>hhh', accel_data)
        scaleFactor = self.ACCEL_SENSITIVITY_SCALE_FACTOR[self.get_accel_config()]
        return {
            'accel_x': round(x / scaleFactor, 3),
            'accel_y': round(y / scaleFactor, 3),
            'accel_z': round(z / scaleFactor, 3)
        }

    def read_gyroscope(self):
        gyro_data = self.i2c.readfrom_mem(self.address, self.GYRO_XOUT_H, 6)
        x, y, z = struct.unpack('>hhh', gyro_data)
        scaleFactor = self.GYRO_SENSITIVITY_SCALE_FACTOR[self.get_gyro_config()]
        gyro_x = x / self.GYRO_SCALE_FACTOR
        gyro_y = y / self.GYRO_SCALE_FACTOR
        gyro_z = z / self.GYRO_SCALE_FACTOR
        return {'gyro_x': gyro_x, 'gyro_y': gyro_y, 'gyro_z': gyro_z}
    
    def read_gyroscope_round(self):
        gyro_data = self.i2c.readfrom_mem(self.address, self.GYRO_XOUT_H, 6)
        x, y, z = struct.unpack('>hhh', gyro_data)
        scaleFactor = self.GYRO_SENSITIVITY_SCALE_FACTOR[self.get_gyro_config()]
        gyro_x = x / self.GYRO_SCALE_FACTOR
        gyro_y = y / self.GYRO_SCALE_FACTOR
        gyro_z = z / self.GYRO_SCALE_FACTOR
        return {'gyro_x': round(gyro_x, 3),
                'gyro_y': round(gyro_y, 3),
                'gyro_z': round(gyro_z, 3)}

    def get_accel_config(self):
        config = self.i2c.readfrom_mem(self.address, self.ACCEL_CONFIG, 1)[0]
        return config & 0x06  # Mask to keep only FS_SEL bits

    def get_gyro_config(self):
        config = self.i2c.readfrom_mem(self.address, self.GYRO_CONFIG, 1)[0]
        return config & 0x06  # Mask to keep only FS_SEL bits
