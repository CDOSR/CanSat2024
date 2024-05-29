import ntptime
import utime
from utils.logger import Logger

log = Logger()

# EET is UTC+2 and EEST is UTC+3
# If observing daylight saving time, use UTC+3, otherwise use UTC+2
time_zone_offset = 3  # Daylight Saving EEST

def get_UTC_time():
    utc_time = utime.localtime()
    # print("Current system time:", utc_time)
    return utc_time

def convert_UTC_to_Epoch(utc_time, offset):
    epoch_time = utime.mktime(utc_time) + offset * 3600
    # print("Epoch time:", epoch_time)
    return epoch_time

def get_epoch_time():
    # Retrieve local time
    utc_time = get_UTC_time()

    # Convert local time to epoch time
    epoch_time = convert_UTC_to_Epoch(utc_time, time_zone_offset)
    
    return epoch_time

def get_local_time():
    epoch_time = get_epoch_time()
    return utime.localtime(epoch_time)

def get_formatted_localtime(local_time):
    # Format the time manually
    formatted_time = "{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}".format(
        year=local_time[0],
        month=local_time[1],
        day=local_time[2],
        hour=local_time[3],
        minute=local_time[4],
        second=local_time[5]
    )
    return formatted_time
    

def sync_ntp(retry_limit=3):
    attempts = 0
    while attempts < retry_limit:
        try:
            ntptime.settime()  # Sync the system time with NTP
            log.log_event("INFO", "Time synchronized with NTP server.")
            
            epoch_time = get_epoch_time()
            
            # Convert back to local time tuple
            local_time = utime.localtime(epoch_time)

            formatted_time = get_formatted_localtime(local_time)
            log.log_event("INFO", "Local time set", localtime=formatted_time)
            return formatted_time
        except OSError as e:
            log.log_event("WARNING", f"Failed to sync with NTP server on attempt {attempts+1}: {e}")
            attempts += 1
    log.log_event("WARNING", "NTP synchronization failed after multiple attempts.")

