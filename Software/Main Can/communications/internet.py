from config import WIFI_CREDENTIALS  # Import your Wi-Fi credentials list
import network
import time
from utils.logger import Logger

log = Logger()

def connect_to_wifi():
    log.log_event("INFO", "Trying to connect to the internet...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Check if already connected
    if wlan.isconnected():
        connected_ssid = wlan.config('essid')
        log.log_event("INFO", "Already connected to internet", SSID=connected_ssid, IP=wlan.ifconfig()[0])
        return True

    # Attempt to connect to each network in the credentials list
    for ssid, password in WIFI_CREDENTIALS:
        log.log_event("INFO", f"Trying to connect to {ssid}...")
        wlan.connect(ssid, password)

        # Wait for connection with a timeout
        timeout = 5
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                log.log_event("WARNING", f"Failed to connect to {ssid}")
                break  # Exit the while loop and try the next SSID
            time.sleep(0.8)  # Sleep to prevent a busy-wait loop

        if wlan.isconnected():
            connected_ssid = wlan.config('essid')
            print(f"Connected to {ssid}")
            print(f"Network config: IP {wlan.ifconfig()[0]}, Netmask {wlan.ifconfig()[1]}, Gateway {wlan.ifconfig()[2]}, DNS {wlan.ifconfig()[3]}")
            log.log_event("INFO", f"Connected to {ssid}", IP=wlan.ifconfig()[0], Netmask=wlan.ifconfig()[1], Gateway=wlan.ifconfig()[2], DNS=wlan.ifconfig()[3])
            return True  # Exit function after successful connection

    log.log_event("WARNING", "Unable to connect to any of the configured networks.")
    return False  # Return False if all connection attempts fail


