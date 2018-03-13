import os
import threading
import usb
import logging
import sys


logger = logging.getLogger(__name__)


class UsbOverlappedResult(threading._Event):
    buffer = None
    status = None
    cancel = False


class UsbOverlappedEndpoint(threading.Thread):

    def __init__(self, ep):
        self._ep = ep
        self._is_stopping = False
        self._queue = []
        self._event = threading.Event()
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        if (self._ep.bEndpointAddress & 0x80):
            self._read_handler()
        else:
            self._write_handler()

    def _read_handler(self):
        while (not self._is_stopping):
            self._event.wait()
            self._event.clear()
            while (self._queue):
                (result, length, timeout, fp) = self._queue.pop(0)
                if fp is not None:
                    curr_length = 0
                    while curr_length < length and not result.cancel:
                        try:
                            b = self._ep.read(32768, timeout)
                            if b:
                                curr_length = curr_length + len(b)
                                fp.write(b)
                        except:
                            logger.error("Unexpected error: %s", sys.exc_info()[0])
                            break
                    result.status = curr_length
                else:
                    try:
                        result.buffer = self._ep.read(length, timeout) or b''
                        result.status = len(result.buffer)
                    except:
                        logger.error("Unexpected error: %s", sys.exc_info()[0])
                        result.status = -1
                result.set()

    def _write_handler(self):
        while (not self._is_stopping):
            self._event.wait()
            self._event.clear()
            while (self._queue):
                (result, buf, timeout) = self._queue.pop(0)
                try:
                    result.status = self._ep.write(buf, timeout)
                except:
                    logger.error("Unexpected error: %s", sys.exc_info()[0])
                    result.status = -1
                result.set()

    def read(self, length, timeout=None):
        result = UsbOverlappedResult()
        result.clear()
        self._queue += [(result, length, timeout, None)]
        self._event.set()
        return result

    def read_to_file(self, length, fp, timeout=None):
        result = UsbOverlappedResult()
        result.clear()
        self._queue += [(result, length, timeout, fp)]
        self._event.set()
        return result
    
    def write(self, data, timeout=None):
        result = UsbOverlappedResult()
        result.clear()
        self._queue += [(result, data, timeout)]
        self._event.set()
        return result

    def stop(self):
        self._is_stopping = True
        self._event.set()
        self.join()


class ExceptionUsbDeviceNotFound(Exception):
    pass

class ExceptionUsbDeviceFailedToClaim(Exception):
    pass

# Direction is with respect to the host i.e., OUT => write from host to device
# IN => read from device to host
EP_MSG_OUT = 0
EP_MSG_IN = 1


class UsbHost():

    VENDOR_ID  = 0x0483     # STMicroelectronics
    PRODUCT_ID = 0x0100     # Seemingly spare for now

    dev = None

    def __init__(self):
        self._endpoints = []
        self.dev = usb.core.find(idVendor=UsbHost.VENDOR_ID, idProduct=UsbHost.PRODUCT_ID)
        if self.dev is None:
            raise ExceptionUsbDeviceNotFound
        if os.name != 'posix':
            self.dev.set_configuration()
        try:
            usb.util.claim_interface(self.dev, 0)
            logger.debug("Claimed device")
        except:
            logger.error("Failed to claim USB device. Device is already in use or python does not have root permissions")
            raise ExceptionUsbDeviceFailedToClaim
        iface = self.dev[0][(0,0)]   # Configuration #0 Interface #0
        self._endpoints = map(UsbOverlappedEndpoint, iface.endpoints())

    def read(self, idx, length, timeout=None):
        logger.debug('USB read ep %u', idx)
        return self._endpoints[idx].read(length, timeout)

    def read_to_file(self, idx, length, fp, timeout=None):
        logger.debug('USB read to file ep %u len %u fp %s', idx, length, fp)
        return self._endpoints[idx].read_to_file(length, fp, timeout)

    def write(self, idx, data, timeout=None):
        logger.debug('USB write ep %u', idx)
        return self._endpoints[idx].write(data, timeout)

    def cleanup(self):
        if self._endpoints:
            [ep.stop() for ep in self._endpoints]
        self._endpoints = None
        if self.dev is not None:
            usb.util.dispose_resources(self.dev) # Release interface

    def __del__(self):
        self.cleanup()
