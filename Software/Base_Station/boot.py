# boot.py
# This script is executed on boot (start or reset of the device).

import os
import machine
import pycom

pycom.heartbeat(False)  # Disable the heartbeat LED
pycom.rgbled(0x00AA00)

# Optionally, configure network or other system settings here

print("Running boot.py... System initializing.")

# Now import main.py to run it
try:
    import main
except Exception as e:
    print("Error running main.py:", str(e))
    # Optional: Add error signaling with LED or logging