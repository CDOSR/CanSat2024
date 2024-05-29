# This file is executed on every boot (including wake-boot from deepsleep)
import esp
from communications.internet import connect_to_wifi
from communications.ntp import sync_ntp
from utils.i2c_scanner import I2CScanner
import config
from machine import Pin, RTC, UART, I2C
from utils.neopixel import NeoPixelControl
from utils.logger import Logger


# import machine

esp.osdebug(None)  # Disable debug output to save power

# Initialize peripherals or configure pins
# Example: Set up a pin for wake-up
# pin = machine.Pin(2, machine.Pin.IN)
# machine.wake_on_ext0(pin, machine.WAKEUP_ALL_LOW)

# Optionally, start WebREPL if you need remote access for debugging (not recommended for production)
# import webrepl
# webrepl.start()

log = Logger()

print("Device Booted.")
log.log_event("INFO", "CanSat mission started")

sys_led = Pin(16, Pin.OUT)
gps_i2c_enable = Pin(6, Pin.OUT)

np_controller = NeoPixelControl(pin_number=10, num_pixels=1)
np_controller.clear()
np_controller.set_pixel(1, 0, 48, 216)


# Connect to Wi-Fi
try:
    connect_to_wifi()
    wifi_on = True
except Exception as e:
    wifi_on = False
    # print("Continuing without Wi-Fi:", str(e))
    log.log_event("WARNING", "Continuing without Wi-Fi", error=str(e))

# # Synchronize time via NTP
try:
    if wifi_on:
        localtime = sync_ntp()
        print(f"Local mission time: {localtime}")
except Exception as e:
    log.log_event("WARNING", "NTP connection not possible without internet access", nest="Continuing to I2C scanning", exception=str(e))

def enable_gps_i2c():
    """ Enable I2C communication on GPS module by setting the enable pin high. """
    log.log_event("INFO", "GPS_I2C_Enable pin set to 1", pin=6, value=1)
    gps_i2c_enable.value(1)

def disable_gps_i2c():
    """ Disable I2C communication on GPS module by setting the enable pin low. """
    log.log_event("INFO", "GPS_I2C_Enable pin set to 0", pin=6, value=0)
    gps_i2c_enable.value(0)

disable_gps_i2c()
#
print("Initializing sensors and communications...")
log.log_event("INFO", "Initializing sensors and communications..." )
# Create an instance of the I2CScanner and perform a scan
scanner = I2CScanner()
print("  - Scanning I2C bus 0 ...")
scanner.scan(bus_id=0)  # Scan first I2C bus
print("  - Scanning I2C bus 1 ...")
scanner.scan(bus_id=1)  # Scan second I2C bus
np_controller.set_pixel(1,0,216,24)