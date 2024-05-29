# Import necessary modules
from sensors.accelerometer import ICM20948
from sensors.pressure import LPS25H, BME688
from sensors.air_quality import AirQualitySensor
from sensors.temperature import TemperatureSensor, MCP9808, BME280
from sensors.uv_sensor import VEML6075
from sensors.gps import M8NNeo
from communications.bluetooth import BluetoothComm
from communications.lora import LoRaComm
from storage.sdcard import SDCard
from sensors.battery import MAX17048
from sensors.esp import ESP32Data
from machine import deepsleep, Pin
import cansat
import utime
import ntptime
from machine import RTC, Pin, UART, I2C
import network
import time
from config import WIFI_CREDENTIALS, KEY_MAP # Import your Wi-Fi credentials list
from communications.ntp import get_epoch_time, get_formatted_localtime
from communications.dataintegrity import get_data_checksum
from sensors.sensor_manager import SensorManager
from utils.logger import Logger
import json
import os
from utils.neopixel import NeoPixelControl
from utils.datalogger import DataLogger
from utils.buzzer import activate_buzzer, deactivate_buzzer, test_buzzer

# Configuration settings
# import config

sensor_data = {
    'epoch': None,
    'local': None,
    'pid': None,
    'data': {
        'alt': None, #altitude
        'acc': None, #acceleration
        'pres': None, #pressure
        'hum':  None, #humidity
        'gyro': None, #gyroscope
        'mag': None, #magnetometric
        'temp': None, #temperature
        'uv': None, #uv_index
        'air': None, #air_quality
        'gps': None, #gps_coordinates
        'bat': None # battery_level
    },
    'esp32': {
        'fmem': None, #free_memory
        'wss': None #wifi_signal_strength
    }
}

#buzzer = buzzer = Pin(21, Pin.OUT)

np_controller = NeoPixelControl(pin_number=10, num_pixels=1)
np_controller.clear()
np_controller.set_pixel(1,255,255,0)

# test_buzzer(1)

# Instantiate the loggers
log = Logger()
dlog = DataLogger()
#sd_card = SDCard(2, 40)

def initialize_system():
    """Initialize all system components including sensors and communication modules."""
    global altimeter, accelerometer, mems_module, air_quality_sensor, temperature_sensor, uv_sensor, gps_sensor, battery, bluetooth_comm, lora_comm, sd_card, esp32#, temperature_2
    log.log_event("INFO", "Sensor initialisation started", running="main.py", function="initialize_system()")
    
    try:
        accelerometer = ICM20948()
        # print(f"ICM20948 initialised done on I2C{ICM20948().channel}")
        log.log_event("INFO", f"ICM20948 initialised done on I2C{ICM20948().channel}", running="main.py", function="initialize_system()", module="ICM20948")
    except Exception as e:
        log.log_event("ERROR", "ICM20948 not initialised", running="main.py", function="initialize_system()", module="ICM20948")

    try:
        pressure = LPS25H()
        # print(f"ICM20948 initialised done on I2C{ICM20948().channel}")
        log.log_event("INFO", f"LPS25H initialised done on I2C{LPS25H().channel}", running="main.py", function="initialize_system()", module="LPS25H")
    except Exception as e:
        log.log_event("ERROR", "ICM20948 not initialised", running="main.py", function="initialize_system()", module="LPS25H", error=e)

    try:
        temperature_1 = MCP9808()
        # print(f"ICM20948 initialised done on I2C{ICM20948().channel}")
        log.log_event("INFO", f"MCP9808 initialised done on I2C{MCP9808().channel}", running="main.py", function="initialize_system()", module="MCP9808")
    except Exception as e:
        log.log_event("ERROR", "MCP9808 not initialised", running="main.py", function="initialize_system()", module="MCP9808", error=e)

    try:
        pressure2 = BME688()
        # print(f"ICM20948 initialised done on I2C{ICM20948().channel}")
        log.log_event("INFO", f"BME688 initialised done on I2C{BME688().channel}", running="main.py", function="initialize_system()", module="BME688")
    except Exception as e:
        log.log_event("ERROR", "BME688 not initialised", running="main.py", function="initialize_system()", module="BME688", error=e)

    try:
        temperature_2 = BME280()
        # print(f"ICM20948 initialised done on I2C{ICM20948().channel}")
        log.log_event("INFO", f"BME280 initialised done on I2C{BME280().channel}", running="main.py", function="initialize_system()", module="BME280")
    except Exception as e:
        log.log_event("ERROR", "BME280 not initialised", running="main.py", function="initialize_system()", module="BME280", error=e)
#     print(f"    BME280 initialised done on I2C{MCP9808().channel}")
    
    try:
        uv_sensor = VEML6075()
        log.log_event("INFO", f"VEML6075 initialised done on I2C{VEML6075().channel}", running="main.py", function="initialize_system()", module="VEML6075")
    except Exception as e:
        log.log_event("ERROR", "VEML6075 not initialised", running="main.py", function="initialize_system()", module="VEML6075", error=e)

    try:
        battery = MAX17048()
        log.log_event("INFO", f"MAX17048 initialised done on I2C{MAX17048().channel}", running="main.py", function="initialize_system()", module="MAX17048")
    except Exception as e:
        log.log_event("ERROR", "MAX17048 not initialised", running="main.py", function="initialize_system()", module="MAX17048", error=e)

    try:
        gps_sensor = M8NNeo()
        log.log_event("INFO", f"M8N-NEO initialised done on UART{M8NNeo().channel}", running="main.py", function="initialize_system()", module="M8N-NEO")
    except Exception as e:
        log.log_event("ERROR", "M8N-NEO not initialised", running="main.py", function="initialize_system()", module="M8N-NEO", error=e)

    try:
        esp32 = ESP32Data()
        log.log_event("INFO", f"ESP32Data initialised done", running="main.py", function="initialize_system()", module="ESP32Data")
    except Exception as e:
        log.log_event("ERROR", "ESP32Data not initialised", running="main.py", function="initialize_system()", module="ESP32Data")

    print("  + Sensors initialized successfully.")
    log.log_event("INFO", "Sensors initialized successfully.")
    
    try:
        bluetooth_comm = BluetoothComm()
    except Exception as e:
        print(f"Bluetooth init error {e}")
    
    try:
        lora_comm = LoRaComm()
    except Exception as e:
        print(f"Lora init error {e}")
#     print("...sdcard 1...")
#     sd_card = SDCard(spi_bus=1, cs_pin=40)
#     print("...sdcard 2...")
    
    print(" + System initialized successfully.")
    np_controller.clear()
    np_controller.set_pixel(1,0,255,0)



# Example usage of the logger
log.log_event("INFO", "Starting system initialization", running="main.py")
# logger.log("Debugging sensor connectivity", "DEBUG")

def format_filename(base_filename, counter):
    # Create a formatted string with leading zeros, assuming no more than 999 files
    filename = "{}_{:03}.json".format(base_filename, counter)
    return filename

def file_exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False

def get_next_filename(base_filename):
    """Generate filename with an incrementing suffix if the file exists and is too large."""
    counter = 0
    while True:
        filename = f"{base_filename}_{counter}.json"
        if not file_exists(filename): #or os.stat(filename)[6] < 5242880:
            return filename
        counter += 1

def flush_data_to_file(data, filename):
    """Write buffered data to the file."""
    with open(filename, "a+") as file:
        #print("Debug: Writing data to file")
        #print(f"Again epochtime is {data['pid']}->{data['epochtime']}")
        # Debugging print
        #json.dump(data, file)  # Dump the entire list of dictionaries as JSON
        file.write(str(data) + '\n')
        #file.write("\n")  # Add a newline after writing the JSON
        #print("Debug: Data written successfully")  # Debugging print
        #print("Data after JSON dump:", data)  # Debugging print

def save_data(data, base_filename="data", max_file_size=5242880):  # 5 MB limit
    """Save data to a JSON file and ensure it does not exceed the maximum file size.
    Automatically increments file name if the file size limit is reached."""
    filename = get_next_filename(base_filename)
    file_exists_and_size_check(filename, data, max_file_size)
    
def file_exists_and_size_check(filename, data, max_size):
    try:
        # print(f"Debug: Checking if {filename} exists...")  # Debugging print
        if file_exists(filename):
            file_size = os.stat(filename)[6]  # The size is the seventh element in the tuple
            # print(f"Debug: File exists. Current size: {file_size}")  # Debugging print
            if file_size + len(json.dumps(data)) >= max_size:
                #print( "Debug: File size limit exceeded, getting new filename...")  # Debugging print
                filename = get_next_filename(base_filename)  # Get a new file name if size limit is reached
        
        #print(f"Debug: Writing data to {filename}")  # Debugging print
        #print(f"Epochtime: {data['epochtime']}")
        flush_data_to_file(data, filename)
        
    except OSError:
        #print("Debug: File does not exist, creating new file...")  # Debugging print
        with open(filename, "w") as file:
            json.dump(data, file)
            file.write("\n")
            #print("Debug: New file created and data written successfully")  # Debugging print

def save_data_SD(data):
    """Save the collected data to the SD card."""
    print("SDCard start...")
    sd_card.write(data)
    sd_card.log_write(data['pid'])

def transmit_data_BT(data):
    """Transmit data over Bluetooth."""
    #bluetooth_comm.send_data(data)
    # lora_comm.transmit_data(data)
    
def transmit_data_LoRa(data):
    """Transmit data over  LoRa."""
    # bluetooth_comm.send_data(data)
    lora_comm.transmit_json(data)
    jdata = json.loads(data)
    print(f"Data package {jdata['pid']} sent ...")

def is_data_valid(data):
    # Example validation logic
    # return all(value is not None for value in data.values())
    
    # Define acceptable ranges or conditions for each sensor
    if data['alt'] is None:
        print("Non-critical error: Altitude data is missing.")
        # Continue despite missing temperature data
#     elif data['altitude'] < 0:
#         print("Critical error: Altitude data is invalid.")
#         return False  # Altitude might be critical

    if data['temp'] is None:
        print("Non-critical error: Temperature data is missing.")
        # Continue despite missing temperature data

    if data['gps'] is None:
        print("Critical error: GPS data is missing.")
        #return False  # Assume GPS is critical for your application

    # Additional checks can be added as per sensor specifications
    return True

def handle_invalid_data():
    # Logic to handle invalid data, e.g., notify a monitoring service, log extensively, or attempt a sensor re-initialization
    print("Handling invalid sensor data...")
    
def encode_data(data, key_map):
    encoded_packet = {}
    for key, value in data.items():
        new_key = key_map.get(key, key)  # Use shorthand if available
        if isinstance(value, dict):
            # Recursive call to handle nested dictionaries
            encoded_packet[new_key] = encode_data(value, key_map)
        else:
            encoded_packet[new_key] = value
    return encoded_packet

def decode_data(encoded_data, key_map):
    decoded_packet = {}
    reverse_key_map = {v: k for k, v in key_map.items()}  # Reverse mapping for decoding
    for key, value in encoded_data.items():
        new_key = reverse_key_map.get(key, key)  # Expand key using reversed map
        if isinstance(value, dict):
            # Recursive call to handle nested dictionaries
            decoded_packet[new_key] = decode_data(value, reverse_key_map)
        else:
            decoded_packet[new_key] = value
    return decoded_packet
    
    
# Function to split the data into packets
def split_data(data):
    packets = []
    # Encoding data for transmission
    if data["valid"] == True:
        
        # Packet 1: Basic Info and Core Data
        packet1 = {
            "pid": data["pid"],
            "type": data["type"],
            "epoch": data["epoch"],
            "bat": data["data"].get("bat"),
            "gps": data["data"].get("gps")#,
            # "valid": data["valid"],
            # "esp32": data["esp32"]
        }
        packets.append(encode_data(packet1, KEY_MAP))

        # Packet 2: GPS and battery data
        temperature_data = data["data"].get("temp", {})
        packet2 = {
            "pid": data["pid"],
            "pres": data["data"].get("pres", "N/A"),
            "temp": {
                "bmp280": temperature_data.get("bmp280", "N/A"),  # Default to "N/A" if not found
                "mcp9808": temperature_data.get("mcp9808", "N/A"),  # Default to "N/A" if not found
                "bme688": temperature_data.get("bme688", "N/A"),  # Default to "N/A" if not found
                "lps25h": temperature_data.get("lps25h", "N/A")   # Default to "N/A" if not found
            }
        }
        #print(f"Packet 2 length = {encode_data(packet2, KEY_MAP)} => {len(str(encode_data(packet2, KEY_MAP)))}")
        packets.append(encode_data(packet2, KEY_MAP))

        # Packet 2: Sensor Data Part 1
        packet3 = {
            "pid": data["pid"],
            "alt": data["data"].get("alt", "N/A"),
            "hum": data["data"].get("hum", "N/A")
        }
        #print(f"Packet 3 length = {encode_data(packet3, KEY_MAP)} => {len(str(encode_data(packet3, KEY_MAP)))}")
        packets.append(encode_data(packet3, KEY_MAP))

        # Packet 2: Sensor Data Part 1
        packet4 = {
            "pid": data["pid"],
            "acc": data["data"].get("acc"),
            "gyro": data["data"].get("gyro")
            #"air_quality": data["data"].get("air_quality")
        }
        #print(f"Packet 4 length = {encode_data(packet4, KEY_MAP)} => {len(str(encode_data(packet4, KEY_MAP)))}")
        packets.append(encode_data(packet4, KEY_MAP))


        # Packet 4: Sensor Data Part 3
#         packet5 = {
#             "pid": data["pid"],
#             "acc": data["data"].get("acc"),
#             "gyro": data["data"].get("gyro")
#         }
#         packets.append(encode_data(packet5, KEY_MAP))

        # Packet 5: GPS and Environmental Data
#         packet6 = {
#             "pid": data["pid"],
#             "gps": data["data"].get("gps")
#         }
#         packets.append(encode_data(packet6, KEY_MAP))

    return packets

def collect_sensor_data(sensor_manager, interval=5):
    """Collect data every few seconds and process in bulk."""
    start_time = utime.time()
    data_points = []

    while utime.time() - start_time < interval:
        data = sensor_manager.collect_data()
        data_points.append(data)
        #utime.sleep(1)  # Adjust sleep time based on the precision you need

    return process_data_bulk(data_points)

def main_loop():
    """Main operation loop."""
    counter = 1 # Initialize the counter for PID
    sensor_manager = SensorManager()  # Create an instance of SensorManager
    while True:
        try:
            
            # Get the current timestamp
            epoch_timestamp = get_epoch_time()  # This returns the number of seconds since the Epoch
            localtime = utime.localtime(epoch_timestamp)
            formatted_time = get_formatted_localtime(localtime)
            
            # Collect sensor data
            collected_data, radio_data = sensor_manager.collect_data()
            #print(collected_data)
            
#             if not is_data_valid(collected_data):
#                 raise ValueError("Collected sensor data is out of expected range.")
            if not is_data_valid(collected_data):
                print("Invalid data detected, handling...")
                handle_invalid_data()  # Implement this function as needed
                continue  # Skip this cycle or attempt data recollection
            
            # Update sensor_data with timestamps and collected sensor data
            sensor_data = {
                'pid': counter,
                'type': "TLM",
                'valid': True,
                'epoch': epoch_timestamp,
                'local': formatted_time,
                'data': collected_data,
                'esp32': {
                    'fmem': esp32.esp_free_memory(), #free_memory
                    'wss': esp32.esp_wifi_signal() #wifi_signal_strength
                }
            }
            
            radio_pack = {
                'pid': counter,
                'type': "TLM",
                'valid': True,
                'epoch': epoch_timestamp,
                'local': formatted_time,
                'data': radio_data
            }

            # print(f"Collecting radio data #{counter}: radio_data")
            
            # Hash, save, and transmit logic remains the same as before
            hash = get_data_checksum(sensor_data)

            # Save data locally
            #save_data(sensor_data)
            dlog.write_data(sensor_data)
 #           save_data_SD(sensor_data)
 #           print("saved")
            if counter % 10 == 0:
                packets = split_data(radio_pack)
#                 pl = []
#                 for p in packets:
#                     pl.append(p)
                #print("{}: {} ".format(counter, pl))
                # Print each packet as JSON string for transmission
                for i, packet in enumerate(packets, 1):
                    json_packet = json.dumps(packet)

                    # Send data to ground station or other devices
                    
                    # lora_comm.led_on()
                    transmit_data_LoRa(json_packet)
                    #transmit_data_LoRa(f"packet {counter}")
                    # print(f"packet {counter}")
                    np_controller.clear()
                    np_controller.set_pixel(1,255,0,0) 
                    time.sleep(0.02)
                    np_controller.clear()
                    np_controller.set_pixel(1,0,255,0)
                    # lora_comm.led_off()

            counter += 1
            
        except ValueError as e:
            print(f"Data validation error: {e}")
        except Exception as e:
            print(f"Unexpected error in main.py: {e}")
            break
#             initialize_system()  # Optionally re-initialize system components
#             continue  # Continue with the next iteration of the loop

# Entry point of the script
if __name__ == "__main__":
    try:
        initialize_system()
        print("System initialization completed.")
        log.log_event("INFO", "System initialization completed.")
        
        main_loop()
    except Exception as e:
        np_controller.clear()
        np_controller.set_pixel(1,255,0,0)
        print("An error occurred during initialization or main loop:", str(e))
        # Optional: Reboot or handle the error in other ways
