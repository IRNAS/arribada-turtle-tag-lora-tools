import sys
from bluepy.btle import Peripheral

if len(sys.argv) != 2:
    print "Fatal, must pass device address:", sys.argv[0], "<device address="">"
    sys.exit(0)

p = Peripheral(sys.argv[1], "random")

chList = p.getCharacteristics()
print "Handle   UUID                                Properties"
print "-------------------------------------------------------"

for ch in chList:
    print "  0x"+ format(ch.getHandle(),'02X')  +"   "+str(ch.uuid) +" " + ch.propertiesToString()
