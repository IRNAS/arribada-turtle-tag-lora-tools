import os
from bluepy.btle import Scanner

SCAN_NAME = 'Arribada_Tracker'
HCI_DEV = 0 if 'HCI_DEV' not in os.environ else int(os.environ['HCI_DEV'])

scanner = Scanner(HCI_DEV)
devices = scanner.scan(1)

device_list = []

for dev in devices:
    for (adtype, desc, value) in dev.getScanData():
        if desc == 'Complete Local Name' and value == SCAN_NAME:
            device_list = device_list + [ dev ]

for dev in device_list:
    print "Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi)
    for (adtype, desc, value) in dev.getScanData():
        print "  %s = %s" % (desc, value)
