import json
import hashlib
# import uzlib
from collections import OrderedDict

def serialize_data(data):
    """ Convert data to a JSON formatted string. """
    return json.dumps(data, separators=(',', ':'))

def deserialize_data(data_string):
    """ Convert JSON formatted string back to data. """
    return json.loads(data_string)

def get_data_checksum(data):
    """ Generate an MD5 checksum for the data. """
    # Convert data to JSON ensuring consistent order
    sorted_dict = OrderedDict(sorted(data.items()))
    sorted_json = json.dumps(sorted_dict)
    encoded_data = sorted_json.encode()

    # Calculate MD5 hash
    md5_hash = hashlib.md5(encoded_data)
    # Convert the binary digest to a hexadecimal string
    hex_digest = ''.join('{:02x}'.format(x) for x in md5_hash.digest())
    
    return hex_digest

def compute_crc32(data):
    """ Compute CRC32 checksum for given data. """
    serialized_data = serialize_data(data)
    crc32_result = uzlib.crc32(serialized_data.encode())
    return crc32_result

def decode_hex(hex_str):
    """ Convert a hexadecimal string to bytes. """
    byte_data = bytes.fromhex(hex_str)
    return byte_data

def crc32(data):
    crc = 0xffffffff
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return crc ^ 0xffffffff

# # Example data
# data = {
#     'type': "telemetry",
#     'pid': 101,
#     'valid': True,
#     'epochtime': 768364735,
#     'localtime': "2024-05-07 02:38:57",
#     'data': {
#         'temperature': 20.13,
#         'altitude': None,
#         'acceleration': {'accel_x': 0.56, 'accel_y': 0.01, 'accel_z': 9.89},
#         'gyroscope': {'gyro_x': 0.56, 'gyro_y': 0.01, 'gyro_z': 9.89},
#         'magnetometric': {'mag_x': 0.56, 'mag_y': 0.01, 'mag_z': 9.89},
#         'pressure': 980,
#         'uv_index': 434,
#         'air_quality': None,
#         'gps_coordinates': {'latitude': 47.843570709228516, 'longitude': 21.253999710083008},
#         'battery_level': 67
#     }
# }
# 
# # Calculate checksum
# checksum = get_data_checksum(data)
# print("Checksum:", checksum)
# 
# # Decode the checksum hexadecimal back to bytes (mostly for demonstration, not practical for hashes)
# dec = decode_hex(checksum)
# print("Decoded Hex to Bytes:", dec)
# 
# # # Calculate checksum
# # crc_value = crc32(data)
# # print("CRC32 Checksum:", crc_value)
