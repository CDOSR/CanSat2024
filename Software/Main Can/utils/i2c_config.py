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
    0x5D: "LPS25H Pressure Sensor",
    0x68: "ICM 20948 Inertial Sensor",
    0x6B: "MPU-9250 IMU",
    0x76: "BME280 Environmental Sensor",
    0x77: "BME688 Environmental Sensor"
}
