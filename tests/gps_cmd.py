import sys
import time
import binascii
from arribada_tools import gps_config, ubx

backend = gps_config.GPSSerialBackend(sys.argv[1], baudrate=int(sys.argv[2]))

data = ubx.ubx_build_from_ascii(sys.argv[3])
backend.read(1024)
backend.write(data)
time.sleep(0.1)
data = backend.read()
(msg, data) = ubx.ubx_extract(data)
if msg:
    print ubx.ubx_to_string(msg), ':', binascii.hexlify(msg)
