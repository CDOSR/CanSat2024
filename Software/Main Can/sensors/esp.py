import network
import esp32
import gc  # Garbage collector for memory management

class ESP32Data:

    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)

#     def esp_hall_sensor(self):
#         return esp32.hall_sensor()  # Read the internal hall sensor, example of available function

    def esp_temperature(self):
        return esp32.raw_temperature()  # Temperature of the ESP32's internal sensor

    def esp_free_memory(self):
        return gc.mem_free()  # Available memory, a bit more reliable than custom APIs

    def esp_wifi_signal(self):
        if self.wlan.isconnected():
            return self.wlan.status('rssi')  # Received Signal Strength Indicator (RSSI)
        return 'Not Connected'

    def get_esp32_data(self):
        return {
#             'hall_sensor': self.esp_hall_sensor(),
#             'internal_temp': self.esp_temperature(),
            'free_memory': self.esp_free_memory(),
            'wifi_signal_strength': self.esp_wifi_signal()
        }

