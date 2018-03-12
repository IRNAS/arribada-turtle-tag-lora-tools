# This is a rudimentary USB to STM32 test script that sends data and looks for the same data being returned
# The client must send any received data back

import time
import sys
from arribada_tools import pyusb

try:
    host = pyusb.UsbHost()
except:
    print("Unexpected error: %s", sys.exc_info()[0])
    quit()

numOfAttempts = 1000
timeout = None

timeAtStart = time.time()
for i in range(0, numOfAttempts):
    stringToSend = str(i)
    host.write(0, stringToSend, timeout).wait() # Send test string
    event = host.read(1, len(stringToSend), timeout) # Prepare to receive
    event.wait() # Receive data
    stringReceived = str(bytearray(event.buffer))
    if stringReceived != stringToSend: # Compare received to sent
        print("Strings are not equal!")
        print("String sent ", stringToSend)
        print("String received ", stringReceived)
        print("Test failed!")
        quit()

timeAtEnd = time.time()
timeElapsedInMs = int(round((timeAtEnd - timeAtStart) * 1000))
print "Test passed in", str(timeElapsedInMs), "ms"
del host
quit()