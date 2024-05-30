
from network import LoRa
import socket
import ujson
import pycom
import time
import utime
from machine import SD, RTC
import os
import gc
from network import WLAN
from logger import Logger
from converters import timeConverter, localtime_to_epoch
from utils import generate_random_filename


# Constants
LoRa_freq = 868000000  # frequency in Hz
SDDir = 'BaseSD'
switch = True

# The provided KEY_MAP
KEY_MAP = {
    "pid": "pid",
    "type": "type",
    "epochtime": "etm",
    "valid": "vld",
    "esp32": "e32",
    "wifi_signal_strength": "wss",
    "free_memory": "fm",
    "altitude": "alt",
    "temperature": "tmp",
    "bmp280": "b28",
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
    "temp": "tme"
}

packets = {}
packet_count = {}
last_pid = None 

pycom.heartbeat(False)  # Disable the heartbeat LED
pycom.rgbled(0xFFFF00)
time.sleep(0.5)

try:
    print("\n"+60*"-"+"\nStarting initialization process...\n"+60*"-"+"\n")
    # disable LED heartbeat (so we can control the LED)
    pycom.heartbeat(False)
    # set LED to red
    pycom.rgbled(0x110000)

    # Reverse the KEY_MAP dictionary
    REVERSED_KEY_MAP = {v: k for k, v in KEY_MAP.items()}

    # Mount SD Card
    try:
        sd = SD()
        os.mount(sd, '/' + SDDir)
        print (" [  OK  ] SD Card mounted as '/{}'".format(SDDir)) 
    except Exception as e:
        print (" [ FAIL ] SD Card not mounted")
        pycom.rgbled(0xFFFF00)  # Yellow light if failed


    # Initialize LoRa
    try:
        lora = LoRa(mode=LoRa.LORA, 
                        frequency=LoRa_freq, 
                        region=LoRa.EU868, 
                        bandwidth=LoRa.BW_125KHZ, 
                        sf=7, 
                        coding_rate=LoRa.CODING_4_5, 
                        power_mode=LoRa.ALWAYS_ON, 
                        rx_iq=False, 
                        public=False)
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        s.setblocking(False)  # Non-blocking mode
        print(" [  OK  ] LoRa Initialized on {0:3.2f} MHz".format(LoRa_freq/1000000))  # Green light if LoRa initialized successfully
        pycom.rgbled(0x000011)
    except Exception as e:
        print(" [ FAIL ] LoRa initialization failed:", str(e))
        pycom.rgbled(0xFF0000)

    try:
        rtc = RTC()
        rtc.ntp_sync("pool.ntp.org")
        if not rtc.synced():
            rtc_on = False
            current_time = generate_random_filename()
        else:
            current_time = timeConverter(utime.localtime())
            rtc_on = True
        utime.sleep_ms(750)
        utime.timezone(7200)
        rtc_msg_log_ok = " [  OK  ] RTC Set from NTP\n"+14*" "+"EST timezone: {}".format(timeConverter(utime.localtime()))
        print (rtc_msg_log_ok)
    except Exception as e:
        rtc_msg_log_fail = " [ FAIL ] RTC raised an exception {}".format(e)
        rtc_on = False
        print (rtc_msg_log_fail)  

    try:
        if rtc_on:
            filename="{}_log".format(localtime_to_epoch(utime.localtime()))
        else:
            filename=generate_random_filename()
        wd = 'CanSat2024Data/'+ filename
        logger = Logger(workingDirectory = wd, daytime=utime.time())
        currentDir, currentLog = logger.files_setup(subdir=filename)
        print (" [  OK  ] Logger started on:\n"+14*" "+"{}".format(currentDir))
    except Exception as e:
        print (" [ FAIL ] Logger offline (error: {})".format(e)) 

except Exception as e:
    print("\n----------------------------------\nInitialization failed...\n----------------------------------\n")
    switch = False
    pycom.heartbeat(False)
    pycom.rgbled(0xffa500)

# print("Logs saved in {}".format(currentLog))
empty_dict={}
# print(currentLog)
with open(currentLog, 'w') as fp:
    ujson.dump(empty_dict, fp)

# Dictionary to hold the received parts of JSON packets
packets = {}

# global last_pid
# last_pid=1

def check_internet_and_sync_time():
    wlan = WLAN(mode=WLAN.STA)
    wlan.connect('CDOSR', auth=(WLAN.WPA2, 'c4ns4t2024'), timeout=5000)

    while not wlan.isconnected():  # Check if the connection was successful
        utime.sleep(0.25)
    if wlan.isconnected():
        print("Internet connected, syncing time...")
        # Sync time using NTP server; actual implementation depends on your device libraries
        # Assuming RTC is set up properly here and connected to NTP
        return True
    else:
        print("Failed to connect to the internet.")
        return False

def append_to_json(filelog, packet):
    # Ensure directory exists before opening a file
    try:
        # Open the file in read mode to check if it exists and has contents
        with open(filelog, 'r') as f:
            file_data = ujson.load(f)
    except FileNotFoundError:
        # If the file does not exist, initialize an empty dictionary
        file_data = {}

    # Update the file data with new packet data
    file_data.update({str(packet['pid']): packet})

    # Write the updated data back to the file
    try:
        with open(filelog, 'w') as f:
            ujson.dump(file_data, f)
            pycom.rgbled(0xFF00FF)
            print("Successfully updated {}".format(filelog))
    
    finally:
        # Optionally, reset the LED color or turn it off after a delay
        time.sleep(0.05)
        pycom.rgbled(0x000000) 

def process_packet(packet_data):
    global packets, packet_count, last_pid  # Ensure that packets is accessible and can maintain state across function calls
    try:
        # Decode bytes to string and adjust the JSON formatting
        formatted_data = packet_data.decode('utf-8').strip('b"\'').replace("'", '"')
        new_data = formatted_data.replace("\\", "")

        # Load the JSON data
        packet = ujson.loads(new_data)
        pid = packet['pid']

        # Initialize the storage for this pid if it does not exist
        if pid not in packets:
            packets[pid] = {}
            packet_count[pid] = 0

        # Merge new data into the existing structure for this PID
        packet_count[pid] += 1
        packets[pid] = merge_dicts(packet, packets[pid])

        # Temporary: Print the merged data to verify
        # print("Merged data for PID {}: {}".format(pid, packets[pid]))

        # # Update the packet data by merging it properly
        # merge_packet_data(packets[pid], packet)
        # print("Formatted data: " + ujson.dumps(packet))

        # Check if all required parts of the message have been received
        if packet_count[pid] == 4 or (last_pid is not None and pid != last_pid):
            if is_complete(packets[pid]):
                complete_data = packets.pop(pid)
                packet_count.pop(pid)
                # print("Complete data received for PID {}: {}".format(pid, ujson.dumps(complete_data)))
                return complete_data
            else:
                print("Data for PID {} is incomplete, awaiting more data.".format(pid))
        else:
            print("Awaiting more data for PID {}".format(pid))

        last_pid = pid  # Update last processed PID

    except Exception as e:
        print("Failed to process packet:", str(e))

def merge_dicts(source, destination):
    """
    Recursively merge dictionaries. 
    Update destination dictionary with values from the source dictionary.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # Get node or create one
            node = destination.setdefault(key, {})
            merge_dicts(value, node)
        else:
            destination[key] = value

    return destination

def merge_packet_data(existing_data, new_data):
    """Recursively merge new data into existing dictionary without overwriting."""
    for key, value in new_data.items():
        if key in existing_data and isinstance(existing_data[key], dict) and isinstance(value, dict):
            merge_packet_data(existing_data[key], value)
        else:
            existing_data[key] = value

def is_complete(data):
    """Determine if all required parts of the message have been received."""
    # Example check for required fields
    # required_fields = ['gps', 'temperature', 'pressure', 'humidity']  # Adjust based on actual requirements
    # return all(field in packet for field in required_fields)
    required_keys = ['gps', 'bat', 'tme', 'hum', 'alt', 'acc', 'gyro']  # Example
    return all(key in data for key in required_keys)


def receive_packets(filename):
    while True:
        try:
            s.setblocking(True)
            packet = s.recv(1024)  # Adjust based on expected maximum packet size
            if packet:
                pycom.rgbled(0xFFFF00) 
                #print(process_packet(packet_data=packet))
                complete_packet=process_packet(packet)
                if complete_packet is not None:
                    renamed_packet = {REVERSED_KEY_MAP.get(key, key): value for key, value in complete_packet.items()}
                    # print(ujson.dumps(renamed_packet))
                    append_to_json(filename, renamed_packet)
                    # with open('result.json', 'w') as fp:
                    #     ujson.dump(renamed_packet, fp)
                pycom.rgbled(0xFF00FF)  # Magenta LED indicates data processing
            else:
                print("No packet received")
        except socket.timeout:
            print("Socket timeout, no packet received")
            pycom.rgbled(0xFF0000)
        except Exception as e:
            print("Error receiving packet:", str(e))
            pycom.rgbled(0xFF0000) 
        time.sleep(0.25)

gc.enable()
receive_packets(currentLog)
