import argparse
import time
import binascii
import logging
from arribada_tools import gps_config, ubx, backend, interface

parser = argparse.ArgumentParser()
parser.add_argument('--serial', required=False)
parser.add_argument('--baud', default=115200, type=int, required=False)
parser.add_argument('--uuid', dest='bluetooth_uuid', required=False)
parser.add_argument('--debug', action='store_true', required=False)
args = parser.parse_args()

if args.debug:
    logging.basicConfig(format='%(asctime)s\t%(module)s\t%(levelname)s\t%(message)s', level=logging.DEBUG)

bridged_backend = None

if args.serial:
    gps_backend = gps_config.GPSSerialBackend(args.serial, baudrate=args.baud)
else:
    if args.bluetooth_uuid:
        bridged_backend = backend.BackendBluetooth(uuid=args.bluetooth_uuid)
    else:
        bridged_backend = backend.BackendUsb()
    gps_backend = gps_config.GPSBridgedBackend(bridged_backend)
    interface.ConfigInterface(bridged_backend).gps_config(True)

while True:
    try:
        data = gps_backend.read()
        while True:
            (msg, data) = ubx.ubx_extract(data)
            if msg:
                print ubx.ubx_to_string(msg), ':', binascii.hexlify(msg)
            else:
                break;
        time.sleep(0.5)
    except KeyboardInterrupt:
        break

if bridged_backend:
    interface.ConfigInterface(bridged_backend).gps_config(False)
gps_backend.cleanup()