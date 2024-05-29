# Configuration for I2C pins
I2C_SCL_PIN = 7  # Change to your specific SCL pin number
I2C_SDA_PIN = 15  # Change to your specific SDA pin number

# I2C bus pin configurations
I2C_PINS = {
    0: {'scl': 7, 'sda': 15},  # Example pins for the first I2C bus
    1: {'scl': 48, 'sda': 47}   # Example pins for the second I2C bus
}

# Dictionary to map sensor I2C addresses to sensor names
SENSOR_MAP = {
    0x10: "VEML6075 UV Sensor",
    0x18: "MCP9808 Temperature Sensor",
    0x1E: "Magnetometer or Other Sensor",
    0x36: "MAX17048 LiPoly/LiIon Fuel Gauge and Battery Monitor",
    0x42: "Unidentified Sensor",
    0x5B: "CCS811 Air Quality Sensor",
    0x5D: "Alternate CCS811 Air Quality Sensor",
    0x68: "MPU-9250 IMU",
    0x6B: "Alternate MPU-9250 IMU",
    0x76: "BME280 Environmental Sensor",
    0x77: "BME688 Environmental Sensor"
}

# WiFi credentials for network connection
WIFI_CREDENTIALS = [
    ("CDOSR", "c4ns4t2024"),
    ("CV20", "r3sist3nc3i5f"),
    ("Cdosr", "c4ns4t2024")
]

KEY_MAP = {
    "pid": "pid",
    "type": "type",
    "epoch": "etm",
    "telemetry": "tele",
    "valid": "vld",
    "esp32": "e32",
    "wss": "wss",
    "fmem": "fm",
    "altitude": "alt",
    "temperature": "tmp",
    "bmp280": "b28",
    "bme688": "b68",
    "lps25h": "l25",
    "lis3mdl": "l3m",
    "pressure": "prs",
    "acceleration": "acc",
    "gyroscope": "gyr",
    "gps_coordinates": "gps",
    "air_quality": "aq",
    "ccs811": "c81",
    "eCO2": "eco",
    "tVOC": "tvoc",
    "telemetry": "tlm",
    "mpu9250": "mpu",
    "mcp9808": "mcp",
    "accel_x": "a_x",
    "accel_y": "a_y",
    "accel_z": "a_z",
    "gyro_x": "g_x",
    "gyro_y": "g_y",
    "gyro_z": "g_z",
    "mag_x": "m_x",
    "mag_y": "m_y",
    "mag_z": "m_z",
    "longitude": "lon",
    "latitude": "lat",
    "speed": "spd",
    "timestamp": "tmsp",
    "magnetic_variation": "mv",
    "course": "crs",
    "null": "na",
    "pres": "pre",
    "temp": "tme",
    "volt": "V",
    "soc": "soc",
    "icm20948": "icm"
}