import sys
import time
import binascii
from arribada_tools import gps_config, ubx

backend = gps_config.GPSSerialBackend(sys.argv[1], baudrate=int(sys.argv[2]))
backend.read(1024)

while True:
    data = backend.read()
    while True:
        (msg, data) = ubx.ubx_extract(data)
        if msg:
            print ubx.ubx_to_string(msg), ':', binascii.hexlify(msg)
        else:
            break;
    time.sleep(0.5)
