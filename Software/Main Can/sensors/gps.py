from machine import UART, Pin
import time

class M8NNeo:
    def __init__(self, uart_num=1, tx_pin=5, rx_pin=4, baudrate=9600):
        self.uart = UART(uart_num, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.channel = uart_num
        self.gps_base_data = {
            'latitude': None,
            'longitude': None,
            'altitude': None,
            'timestamp': None
        }
        self.gps_data = {
            'speed': None,
            'course': None,
            'date': None,
            'magnetic_variation': None,
            'mode': None
        }
    
    def read_line(self):
        if self.uart.any():
            return self.uart.readline()
        return None
    
    def parse_gpgga(self, nmea):
        parts = nmea.split(',')
        if parts[0] == '$GPGGA' and len(parts) > 9:
            # Ensure that latitude and longitude are valid before updating
            if parts[2] and parts[4]:
                self.gps_base_data.update({
                    'latitude': parts[2],
                    'longitude': parts[4],
                    'altitude': parts[9] + parts[10],
                    'timestamp': parts[1]
                })
                
    def parse_gngll(self, nmea):
        parts = nmea.split(',')
        if parts[0] == '$GNGLL' and len(parts) >= 7:
            # Ensure that latitude and longitude are valid before updating
            if parts[1] and parts[3]:
                self.gps_base_data.update({
                    'latitude': parts[1] + " " + parts[2],  # Latitude and N/S indicator
                    'longitude': parts[3] + " " + parts[4], # Longitude and E/W indicator
                    'timestamp': parts[5] #,  # Time of position fix
                    #'status': parts[6]  # Status A=active or V=Void
                })
                
    def parse_gnrmc(self, nmea):
        parts = nmea.split(',')
        if parts[0] == '$GNRMC' and len(parts) > 11:
            # Ensure that the status is active
            if parts[2] == 'A':
                self.gps_base_data.update({
                    'timestamp': parts[1],
                    'latitude': parts[3] + " " + parts[4],
                    'longitude': parts[5] + " " + parts[6]
                    })
                self.gps_data.update({
                    'speed': parts[7],
                    'course': parts[8],
                    'date': parts[9],
                    'magnetic_variation': parts[10] + " " + parts[11] if parts[11] else None,
                    'mode': parts[12].strip().split('*')[0] if '*' in parts[12] else parts[12]  # Safely handling the checksum part
                })
                
#     def parse_gpvtg(self, nmea):
#         parts = nmea.split(',')
#         if parts[0] == '$GPVTG' and len(parts) > 7:
#             # Ensure speed is valid before updating
#             if parts[7]:
#                 self.gps_data.update({'speed': parts[7]})
                
    def parse_gnvtg(self, nmea):
        parts = nmea.split(',')
        if parts[0] == '$GNVTG':
            self.gps_data.update({
#                 'true_track_degrees': parts[1],
#                 'true_track_label': parts[2],
#                 'magnetic_track_degrees': parts[3] if parts[3] else None,
#                 'magnetic_track_label': parts[4] if parts[4] else None,
                'speed': parts[5] #,
#                 'speed': parts[6] # in knots,
#                 'ground_speed_kmph': parts[7],
#                 'speed_label_kmph': parts[8],
#                 'mode_indicator': parts[9].strip().split('*')[0] if '*' in parts[9] else parts[9]  # Safely handling the checksum part
            })
            
    def process_nmea_sentence(self, sentence):
        if 'GPGGA' in sentence or 'GNGGA' in sentence:
            self.parse_gpgga(sentence)
        if 'GNGLL' in sentence:
            self.parse_gngll(sentence)
        if 'GNRMC' in sentence or 'GPRMC' in sentence:
            self.parse_gnrmc(sentence)
    
    def get_gps_data(self):
        # Read and process all available lines
        while self.uart.any():
            line = self.read_line()
            if line:
                # Check if the start and end of the line look like a valid NMEA sentence
                if line.startswith(b'$') and b'*' in line:
                    try:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith('$'):
                            self.process_nmea_sentence(decoded_line)
                    except Exception as e:  # Catching all exceptions, including decode errors
                        print("Error decoding data: {}".format(str(e)))
        # Return a copy of the current GPS data
        # print(self.gps_data)
        return (self.gps_base_data.copy(), self.gps_data.copy())