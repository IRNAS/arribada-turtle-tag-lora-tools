import argparse
import logging
from arribada_tools import backend, interface, config

parser = argparse.ArgumentParser()
parser.add_argument('--uuid', dest='bluetooth_uuid', required=False)
parser.add_argument('--debug', action='store_true', required=False)
parser.add_argument('--write', type=argparse.FileType('r'), required=False)
parser.add_argument('--read', type=argparse.FileType('w'), required=False)
parser.add_argument('--read_log', type=argparse.FileType('wb'), required=False)
parser.add_argument('--battery', action='store_true', required=False)
parser.add_argument('--status', action='store_true', required=False)
parser.add_argument('--save', action='store_true', required=False)
parser.add_argument('--restore', action='store_true', required=False)
parser.add_argument('--erase', action='store_true', required=False)
parser.add_argument('--erase_log', action='store_true', required=False)
parser.add_argument('--create_log', required=False)
parser.add_argument('--protect', action='store_true', required=False)
parser.add_argument('--unprotect', action='store_true', required=False)
parser.add_argument('--setdatetime', required=False)
parser.add_argument('--getdatetime', action='store_true', required=False)
parser.add_argument('--firmware_type', type=int, required=False)
parser.add_argument('--firmware', type=argparse.FileType('rb'), required=False)

args = parser.parse_args()

if args.debug:
    logging.basicConfig(format='%(asctime)s\t%(module)s\t%(levelname)s\t%(message)s', level=logging.DEBUG)

if args.bluetooth_uuid:
    bridged_backend = backend.BackendBluetooth(uuid=args.bluetooth_uuid)
else:
    bridged_backend = backend.BackendUsb()

cfg = interface.ConfigInterface(bridged_backend)

if args.read_log:
    args.read_log.write(cfg.read_log_file(0, 0))

if args.erase_log:
    cfg.erase_log_file()

if args.create_log:
    cfg.create_log_file(args.create_log)

if args.restore:
    cfg.restore_configuration()

if args.unprotect:
    cfg.unprotect_configuration()

if args.erase:
    cfg.erase_configuration()

if args.write:
    cfg.write_json_configuration(args.write.read())

if args.setdatetime:
    cfg.write_json_configuration('"rtc": { "dateTime": "%s"}' % args.datetime)

if args.getdatetime:
    print cfg.read_json_configuration(tag=config.ConfigItem_RTC_CurrentDateTime.tag)

if args.save:
    cfg.save_configuration()

if args.read:
    args.read.write(cfg.read_json_configuration())

if args.protect:
    cfg.protect_configuration()

if args.status:
    print cfg.get_status()

if args.battery:
    cfg.get_battery_status()

if args.firmware_type and args.firmware:
    cfg.fw_upgrade(args.firmware_type, args.firmware.read())
