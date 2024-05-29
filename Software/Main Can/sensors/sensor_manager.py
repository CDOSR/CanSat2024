# Import necessary modules
# from sensors.altimeter import Altimeter
from sensors.accelerometer import ICM20948 #MPU9250
from sensors.pressure import LPS25H, BME688
# from sensors.mems_module import LIS3MDL
# from sensors.air_quality import AirQualitySensor, CCS811
from sensors.temperature import MCP9808, BME280
from sensors.uv_sensor import VEML6075
from sensors.gps import M8NNeo
from communications.bluetooth import BluetoothComm
from communications.lora import LoRaComm
from storage.sdcard import SDCard
from sensors.battery import MAX17048 
from sensors.esp import ESP32Data
from utils.logger import Logger

log = Logger()

class SensorManager:
    def __init__(self):
        self.initialize_sensors()

    def initialize_sensors(self):
        """Initialize or reinitialize all sensor objects."""
        self.accelerometer1 = ICM20948()
        self.pressure1 = LPS25H()
        self.pressure2 = BME688()
        self.pressure1.enableLPS()
        self.magnetometric1 = ICM20948()
        self.temperature1 = MCP9808()
        self.temperature2 = BME280()
        self.uv_sensor = VEML6075()
        self.gps_sensor = M8NNeo()
        self.battery = MAX17048()
        
    def log_error(self, sensor_name, error):
        log.log_event("ERROR", f"Error reading {sensor_name}", running="sensor_manager.py", function="collect_data()", error=f"{error}")
        print(f"Error reading {sensor_name}: {error}")

    def collect_data(self):
        """Collect data from all sensors, handling exceptions individually."""
        data = {
            'alt': {}, #altitude
            'acc': {}, #acceleration
            'pres': {}, #pressure
            'temp': {}, #temperature
            'hum' : {}, #humidity
            'gyro': {}, #gyroscope
            'mag': {}, #magnetometric
            'uv': {}, #uv_index
            'air': {}, #air_quality
            'gps': {}, #gps_coordinates
            'bat': {} #battery_level
        }
        radiodata = {
            'alt': {}, #altitude
            'acc': {}, #acceleration
            'pres': {}, #pressure
            'temp': {}, #temperature
            'hum' : {}, #humidity
            'gyro': {}, #gyroscope
            'mag': {}, #magnetometric
            'uv': {}, #uv_index
            'air': {}, #air_quality
            'gps': {}, #gps_coordinates
            'bat': {} #battery_level
        }

        try:
            data['acc']['icm20948'] = self.accelerometer1.read_acceleration()
            data['mag']['icm20948'] = self.magnetometric1.read_magnetometer()
            data['gyro']['icm20948'] = self.accelerometer1.read_gyroscope()
            radiodata['acc']['icm20948'] = self.accelerometer1.read_acceleration_round()
            radiodata['mag']['icm20948'] = self.magnetometric1.read_magnetometer_round()
            radiodata['gyro']['icm20948'] = self.accelerometer1.read_gyroscope_round()
        except Exception as e:
            data['acc']['icm20948'] = None
            data['mag']['icm20948'] = None
            data['gyro']['icm20948'] = None
            radiodata['acc']['icm20948'] = None
            radiodata['mag']['icm20948'] = None
            radiodata['gyro']['icm20948'] = None
            self.log_error("acceleration/magnetometric/gyroscope", e)
#             log.log_entry("ERROR", "Error reading acceleration/magnetometric/gyroscope data", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error reading acceleration/magnetometric/gyroscope data: {e}")

        try:
            data['temp']['bme688'] = self.pressure2.temperature
            data['pres']['bme688'] = self.pressure2.pressure
            data['hum']['bme688'] = self.pressure2.humidity
            data['alt']['bme688'] = self.pressure2.altitude
            radiodata['temp']['bme688'] = round(data['temp']['bme688'], 2)
            radiodata['pres']['bme688'] = round(data['pres']['bme688'], 2)
            radiodata['hum']['bme688'] = round(data['hum']['bme688'], 2)
            radiodata['alt']['bme688'] = round(data['alt']['bme688'], 2)
            #print(f"Temp: {self.pressure2.temperature}, Pres: {self.pressure2.pressure}, Hum: {self.pressure2.humidity}, Altitude: {self.pressure2.altitude}, Gas: {self.pressure2.gas}")
        except Exception as e:
            data['temp']['bme688'] = None
            data['pres']['bme688'] = None
            data['hum']['bme688'] = None
            data['alt']['bme688'] = None
            radiodata['temp']['bme688'] = None
            radiodata['pres']['bme688'] = None
            radiodata['hum']['bme688'] = None
            radiodata['alt']['bme688'] = None
            self.log_error("altitude", e)
#             log.log_entry("ERROR", "Error reading altitude", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error reading altitude: {e}")

        try:
            data['temp']['lps25h'] = self.pressure1.read_temperature()
            data['pres']['lps25h'] = self.pressure1.read_pressure()
            data['alt']['lps25h'] = self.pressure1.read_altitude()
            radiodata['temp']['lps25h'] = round(data['temp']['lps25h'], 2)
            radiodata['pres']['lps25h'] = round(data['pres']['lps25h'], 2)
            radiodata['alt']['lps25h'] = round(data['alt']['lps25h'], 2)
        except Exception as e:
            data['temp']['lps25h'] = None
            data['pres']['lps25h'] = None
            data['alt']['lps25h'] = None
            radiodata['temp']['lps25h'] = None
            radiodata['pres']['lps25h'] = None
            radiodata['alt']['lps25h'] = None
            self.log_error("pressure/temperature", e)
#             log.log_entry("ERROR", "Error reading pressure/temperature", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error reading pressure/temperature from LPS25H: {e}")
        
        try:
            data['temp']['mcp9808'] = self.temperature1.getTemp()
            radiodata['temp']['mcp9808'] = round(data['temp']['mcp9808'], 2)
        except Exception as e:
            data['temp']['mcp9808'] = None
            radiodata['temp']['mcp9808'] = None
            self.log_error("temperature", e)
#             log.log_entry("ERROR", "Error reading temperature from MCP9808", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error reading temperature from MCP9808: {e}")

#         try:
#             data['air_quality']['ccs811'] = self.air_quality_sensor.read_quality()
#         except Exception as e:
#             data['air_quality']['ccs811'] = None
#             print(f"Error reading air quality: {e}")

        try:
            data['temp']['bmp280'] = self.temperature2.get_temperature()
            data['pres']['bmp280'] = self.temperature2.get_pressure()
            data['hum']['bmp280'] = self.temperature2.get_humidity()
            data['alt']['bmp280'] = self.temperature2.get_altitude()
            radiodata['temp']['bmp280'] = round(data['temp']['bmp280'], 2)
            radiodata['pres']['bmp280'] = round(data['pres']['bmp280'], 2)
            radiodata['hum']['bmp280'] = round(data['hum']['bmp280'], 2)
            radiodata['alt']['bmp280'] = round(data['alt']['bmp280'], 2)
        except Exception as e:
            data['temp']['bmp280'] = None
            data['pres']['bmp280'] = None
            data['hum']['bmp280'] = None
            data['alt']['bmp280'] = None
            radiodata['temp']['bmp280'] = None
            radiodata['pres']['bmp280'] = None
            radiodata['hum']['bmp280'] = None
            radiodata['alt']['bmp280'] = None
            self.log_error("temperature", e)
#             log.log_entry("ERROR", "Error reading temperature from BMP280 sensor", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error reading temperature from BMP280 sensor: {e}")

        try:
            data['uv']['uva'] = self.uv_sensor.read_uv_index()
            data['uv']['uvb'] = self.uv_sensor.read_uv_index()
            data['uv']['uvidx'] = self.uv_sensor.read_uv_index()
            radiodata['uv']['uva'] = data['uv']['uva']
            radiodata['uv']['uvb'] = data['uv']['uvb']
            radiodata['uv']['uvidx'] = data['uv']['uvidx']
        except Exception as e:
            data['uv']['uva'] = None
            data['uv']['uvb'] = None
            data['uv_']['uvidx'] = None
            radiodata['uv']['uva'] = None
            radiodata['uv']['uvb'] = None
            radiodata['uv']['uvidx'] = None
            self.log_error("UV index", e)
#             log.log_entry("ERROR", "Error reading UV index", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error reading UV index: {e}")

        try:
            data['gps']['gps1'] = self.gps_sensor.get_gps_data()[0]
            data['gps']['gps2'] = self.gps_sensor.get_gps_data()[1]
            if data['gps']['gps1']:
                radiodata['gps']['lat'] = data['gps']['gps1']['latitude']
                radiodata['gps']['lon'] = data['gps']['gps1']['longitude']
                radiodata['gps']['gtm'] = data['gps']['gps1']['timestamp']
        except Exception as e:
            data['gps']['gps1'] = None
            data['gps']['gps2'] = None
            radiodata['gps']['lat'] = None
            radiodata['gps']['lon'] = None
            radiodata['gps']['gtm'] = None
            self.log_error("GPS coordinates error", f"{e}")
#             log.log_entry("ERROR", "Error getting GPS coordinates", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error getting GPS coordinates: {e}")

        try:
            data['bat']['volt'] = round(self.battery.read_voltage(), 2)
            data['bat']['soc'] = round(self.battery.read_soc(), 2)
            radiodata['bat']['volt'] = round(self.battery.read_voltage(), 2)
            radiodata['bat']['soc'] = round(self.battery.read_soc(), 2)
        except Exception as e:
            data['bat']['volt'] = None
            data['bat']['soc'] = None
            radiodata['bat']['volt'] = None
            radiodata['bat']['soc'] = None
            log_error("battery level", e)
#             log.log_entry("ERROR", "Error reading battery level", running="sensor_manager.py", function="collect_data()", error=f"{e}" )
#             print(f"Error reading battery level: {e}")

        return data, radiodata
