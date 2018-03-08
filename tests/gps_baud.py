import sys
from arribada_tools import gps_config, ubx

backend = gps_config.GPSSerialBackend(sys.argv[1], baudrate=int(sys.argv[2]))
backend.read(1024)

msg = ubx.ubx_cfg_uart(int(sys.argv[3]))
backend.write(msg)
