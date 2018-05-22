import os
import sys
from bluepy.btle import Peripheral

if len(sys.argv) != 2:
    print "Fatal, must pass device address:", sys.argv[0], "<device address="">"
    sys.exit()

HCI_DEV = 0 if 'HCI_DEV' not in os.environ else int(os.environ['HCI_DEV'])

p = Peripheral(sys.argv[1], "random", HCI_DEV)

services=p.getServices()

#displays all services
for service in services:
    print service
