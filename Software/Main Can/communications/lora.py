from machine import UART, Pin
import time
import json
from collections import OrderedDict
from utils.logger import Logger

log = Logger()
loraLog = Logger(log_file="LoraLog.txt")

class LoRaComm:
    commands = OrderedDict([
            ("sys reset", "RN2483 1.0.4 Oct 12 2017 14:59:25"),
            ("sys get hweui", None),  # Example response, change as needed
            ("mac pause", "4294967245"),
            ("radio set mod lora", "ok"),
            ("radio set freq {}".format(868000000), "ok"),
            ("radio set pwr 14", "ok"),
            ("radio set sf sf7", "ok"),
            ("radio set afcbw 41.7", "ok"),
            ("radio set rxbw 125", "ok"),
#             ("radio set prlen 8", "ok"),
#             ("radio set crc on", "ok"),
#             ("radio set iqi off", "ok"),
            ("radio set cr 4/5", "ok"),
            ("radio set wdt 60000", "ok"),
            ("radio set sync 12", "ok"),
            ("radio set bw 125", "ok"),
   #         ("radio get cr", "ok"),
   #         ("radio get bw", "ok"),
   #         ("radio get sf", "ok"),
   #         ("radio get mod", "ok")
#             ("mac resume", "ok")
        ])
    errors = ['ok',
              'busy',
              'fram_counter_err_rejoin_needed',
              'invalid_class',
              'invalid_data_len',
              'invalid_param',
              'keys_not_init',
              'mac_paused',
              'multicast_keys_not_set',
              'no_free_ch',
              'not_joined',
              'silent',
              'err'
              ]
    
    def __init__(self, uart_num=2, tx_pin=18, rx_pin=17, baudrate=57600, freq=868000000):
        # Initialize UART with the specified pins and baudrate
        self.uart = UART(2, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        time.sleep(0.5)  # Allow some time for the UART setup
        self.freq = freq
        self.init_lora()


    def send_lora_cmd(self, cmd):
        """Send a command to the RN2483 and handle busy responses."""
        retry = True
        full_cmd = "{}\x0d\x0a".format(cmd)
        self.uart.write(full_cmd.encode('ASCII'))
        time.sleep(0.2)
        while retry:
            response = self.uart.readline()
            if response is None:
                loraLog.log_event("WARNING", "No response received, possibly due to timeout or disconnection.")
                break  # Exit the loop if no data is received
                
            #print(response)
            resp=response.decode("utf-8").replace("\r\n","")
            if "busy" in resp:
                loraLog.log_event("WARNING", "Busy LoRa chip")
            else:
                #loraLog.log_event("INFO", "Command: {} | Response: {}".format("radio tx", resp))
                retry = False   
            
#             return None

    def init_lora(self):
        log.log_event("INFO", "Starting LoRa on {} MHz".format(round(self.freq/1000000,2)))
        loraLog.log_event("INFO", "Starting LoRa on {} MHz".format(round(self.freq/1000000,2)))
        print("  + LoRa setup started on {} MHz".format(round(self.freq/1000000,2)))
        # print(" [ LORA ] Starting LoRa on {} MHz".format(round(self.freq/1000000,2)))
        for cmd, expected_resp in LoRaComm.commands.items():
            response = self.send_lora_cmd(cmd)
            if response is None:
                loraLog.log_event("WARNING", f"Lora - No response for command: {cmd}")
                continue
            if expected_resp and expected_resp not in response:
                loraLog.log_event("ERROR", "Lora - Command failed", command = cmd, expected = expected_resp, response = response)
            else:
                loraLog.log_event("INFO", "Lora - Command executed successfully", command = cmd, response=response)

    def get_hardware_eui(self):
        """Get the hardware EUI from the module."""
        return self.send_lora_cmd('sys get hweui')

    def get_version(self):
        """Get the firmware version of the module."""
        return self.send_lora_cmd('sys get ver')
    
    def to_hex(self, data):
        """Convert a string to hex-encoded format without using zfill."""
        hex_str = ''
        for char in data:
            hex_char = hex(ord(char))[2:]  # Convert character to hex and remove the '0x'
            if len(hex_char) < 2:
                hex_char = '0' + hex_char  # Manually add zero padding if necessary
            hex_str += hex_char
        return hex_str
    
    def transmit(self, data, confirm=False):
        """Transmit data as a hex-encoded string using LoRaWAN.
        
        Args:
            data (str): The data to transmit, in plaintext.
            confirm (bool): If True, use confirmed messages; otherwise, use unconfirmed.
        """
#         response = self.send_lora_cmd(f'mac get status')
#         print('Sent: mac get status => Transmission Response:', response)
#         
#         response = self.send_lora_cmd(f'radio tx 48656C6C6F')
#         print('Sent: radio tx 48656C6C6F => Transmission Response:', response)
        
        # Convert the string data to hex
        hex_data = self.to_hex(data)
        cmd_type = 'cnf' if confirm else 'uncnf'
        # Send the data over LoRaWAN
        #print(f'radio tx {hex_data}')
        response = self.send_lora_cmd(f'radio tx {hex_data}')
        # response = self.send_lora_cmd(f'mac tx {cmd_type} 1 {hex_data}')
        
    def transmit_json(self, json_data, confirm=False):
        """Transmit JSON data as a hex-encoded string using LoRaWAN."""
        # Convert JSON object to string
        json_string = json.dumps(json_data)
        # Send the JSON string
        self.transmit(json_string, confirm)
        
    def led_on(self):
        self.send_lora_cmd(f'sys set pindig GPIO13 1')
    
    def led_off(self):
        self.send_lora_cmd(f'sys set pindig GPIO13 0')
# from network import LoRa
# import socket
# import time
# import struct

# class LoRaComm:
#     def __init__(self, frequency=LoRa.EU868):
#         # Initialize LoRa in LORA mode
#         self.lora = LoRa(mode=LoRa.LORA, region=frequency)
#         self.s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
#         self.s.setblocking(False)
# 
#     def transmit_data(self, data):
#         """Transmit data using LoRa."""
#         self.s.setblocking(True)  # Ensure data is sent before continuing
#         self.s.send(data)
#         self.s.setblocking(False)  # Set to non-blocking mode again
#         print("Data sent")
# 
#     def get_lora_data(self):
#         """Retrieve LoRa communication parameters."""
#         return {
#             'signal_strength': self.lora.stats().rssi,  # Received Signal Strength Indicator
#             'transmission_rate': self.lora.stats().sfr,  # Spreading Factor Rate
#             'acknowledge_receipt': self.lora.stats().tx_trials  # Transmit trials
#         }
# 
#     def receive_data(self):
#         """Receive data using LoRa. Call this method repeatedly in your loop."""
#         self.s.setblocking(False)  # Non-blocking mode
#         data = self.s.recv(512)  # Adjust as per the expected max packet size
#         if data:
#             return data.decode('utf-8')
#         return None
#     
#     def transmit_packets(packets):
#         for packet in packets:
#             packet_data = json.dumps(packet)  # Convert packet to JSON string
#             self.transmit_data(packet_data.encode('utf-8'))  # Encode packet as bytes and send
#             time.sleep(0.1)  # Wait a bit before sending the next packet to avoid congestion
# 