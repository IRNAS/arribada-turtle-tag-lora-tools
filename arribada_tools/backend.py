import pyusb
import message
from array import array
from ble import BluetoothTracker
import time

class ExceptionBackendNotFound(Exception):
    pass


class ExceptionBackendNotImplemented(Exception):
    pass


class _Backend(object):

    def __init__(self, **kwargs):
        pass

    def command_response(self, command, timeout=None):
        pass

    def write(self, data, timeout=None):
        pass

    def read(self, length, timeout=None):
        pass

    def cleanup(self):
        pass


class BackendBluetooth(_Backend):

    def __init__(self, uuid=None):
        try:
            self._ble = BluetoothTracker(uuid)
        except:
            raise ExceptionBackendNotFound

    def write(self, data, timeout=None):
        self._ble.write(data)

    def read(self, length, timeout=None):
        self._ble.read(timeout)


class BackendUsb(_Backend):

    def __init__(self, *kwargs):
        try:
            self._usb = pyusb.UsbHost()
        except:
            raise ExceptionBackendNotFound

    def command_response(self, command, timeout=None):
        """Send a command (optionally) over USB and wait for a response to come back.
        The input command is a message object and any response shall be
        first decoded to a response message object.
        """

        if timeout != None:
            timeout = timeout * 1000 # Scale timeout to milliseconds
            timeout = int(timeout)

        if command:
            resp = self._usb.write(pyusb.EP_MSG_OUT, command.pack(), timeout)
            resp.wait()
            if resp.status == -1:
                return None
        # All command responses are guaranteed to fit inside 512 bytes
        resp = self._usb.read(pyusb.EP_MSG_IN, 512, timeout)
        resp.wait()
        if resp.status == -1:
            return None
        else:
            (msg, _) = message.decode(resp.buffer)
            return msg

    def write(self, data, timeout=None):
        """Write data transparently over USB in small chunks
        until all bytes are transmitted or a timeout occurs.  Returns
        the total number of bytes sent.
        """

        if timeout != None:
            timeout = timeout * 1000 # Scale timeout to milliseconds
            timeout = int(timeout)

        size = 0
        while data:
            resp = self._usb.write(pyusb.EP_MSG_OUT, data[:512 - 1], timeout) # See https://www.microchip.com/forums/m818567.aspx for why 1 less than 512 is sent
            resp.wait()
            if resp.status <= 0:
                break
            data = data[resp.status:]
            size = size + resp.status
        return size

    def read(self, length, timeout=None):
        """Read data transparently over USB in small chunks
        until all bytes are received or a timeout occurs.  Returns
        the data buffer received.
        """

        if timeout != None:
            timeout = timeout * 1000 # Scale timeout to milliseconds
            timeout = int(timeout)

        data = array('B', [])
        while length > 0:
            resp = self._usb.read(pyusb.EP_MSG_IN, min(512, length), timeout)
            resp.wait()
            if resp.status == -1:
                break
            data = data + resp.buffer
            length = length - len(resp.buffer)
        return data

    def cleanup(self):
        self._usb.cleanup()
