import argparse
import logging
from arribada_tools import gps_config, ubx, backend, interface

parser = argparse.ArgumentParser()
parser.add_argument('--serial', required=False)
parser.add_argument('--baud', default=115200, type=int, required=False)
parser.add_argument('--uuid', dest='bluetooth_uuid', required=False)
parser.add_argument('--debug', action='store_true', required=False)
parser.add_argument('--new_baud', type=int, required=True)
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

msg = ubx.ubx_cfg_uart(args.new_baud)
gps_backend.write(msg)

# If we are bridged then we need to send an updated UART baud rate
# to ensure that the GPS/MCU configuration remains in sync
if bridged_backend:
    cfg = interface.ConfigInterface(backend)
    cfg.write_json_configuration('{"gps": {"uartBaudRate": %u}}' % args.new_baud)
    cfg.gps_config(False)
gps_backend.cleanup()