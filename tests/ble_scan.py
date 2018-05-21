from bluepy.btle import Scanner

SCAN_NAME = 'Arribada_Tracker'

scanner = Scanner()
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
