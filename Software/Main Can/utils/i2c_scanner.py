from machine import I2C, Pin
from utils.logger import Logger
from utils.i2c_config import SENSOR_MAP, I2C_PINS

class I2CScanner:
    def __init__(self, freq=400000):
        self.logger = Logger(level='DEBUG')
        self.freq = freq
        self.buses = {}
        # Initialize I2C buses based on the configuration
        for bus_id, pins in I2C_PINS.items():
            self.buses[bus_id] = I2C(bus_id, scl=Pin(pins['scl']), sda=Pin(pins['sda']), freq=freq)

    def scan(self, bus_id=0):
        if bus_id not in self.buses:
            # self.logger.log(f"Invalid I2C bus ID: {bus_id}", level="ERROR")
            self.logger.log_event("ERROR", "Invalid I2C bus ID: {bus_id}")
            return []
        
        i2c = self.buses[bus_id]
        # self.logger.log(f"Scanning for I2C devices on bus {bus_id}...")
        self.logger.log_event("INFO", f"Scanning for I2C devices on bus {bus_id}...")
        devices = i2c.scan()
        identified_devices = []
        unidentified_devices = []
        device_num = 0

        if devices:
            # Sort devices by I2C address
            devices.sort()
            for device in devices:
                device_hex = "0x{:02X}".format(device)
                sensor_name = SENSOR_MAP.get(device, "Unknown Sensor")
                if sensor_name != "Unknown Sensor": 
                    self.logger.log_event("INFO", f"Found {sensor_name} at address: {device_hex}")
                    identified_devices.append((device_hex, sensor_name))
                else:
                    self.logger.log_event("WARNING", f"{sensor_name} at address: {device_hex}")
                    unidentified_devices.append((device_hex, sensor_name))
            device_num = len(identified_devices)+len(unidentified_devices)
        else:
            self.logger.log_event("WARNING", "No I2C devices found")
            
        if len(identified_devices) > 0:
            print(f"      Identified I2C devices on bus {bus_id}:")
            for device, name in identified_devices:
                print(f"       * {name} at address {device}")
        else:
            if device_num == 0:
                print(f"      No I2C devices found on bus {bus_id}")
            
        if len(unidentified_devices) > 0:
            print(f"      Unidentified I2C devices on bus {bus_id}:")
            for device, name in unidentified_devices:
                print(f"       * {name} at address {device}")
        else:
            if device_num == 0:
                print(f"      No I2C devices found on bus {bus_id}")

        return identified_devices