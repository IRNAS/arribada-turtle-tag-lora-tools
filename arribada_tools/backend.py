import pyusb
import message


class ExceptionBackendNotFound(Exception):
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


class BackendBluetooth(_Backend):
    pass


class BackendUsb(_Backend):

    def __init__(self, *kwargs):
        try:
            self._usb = pyusb.UsbHost()
        except:
            raise ExceptionBackendNotFound

    def command_response(self, command, timeout=None):
        """Send a command over USB and wait for a response to come back.
        The input command is a message object and any response shall be
        first decoded to a response message object.
        """
        resp = self._usb.write(pyusb.EP_MSG_OUT, command.pack(), timeout)
        resp.wait()
        if resp.status == -1:
            return None
        resp = self._usb.read(pyusb.EP_MSG_IN, 512, timeout)
        resp.wait()
        if resp.status == -1:
            return None
        else:
            return message.decode(resp.buffer)

    def write(self, data, timeout=None):
        """Write data transparently over USB in small chunks
        until all bytes are transmitted or a timeout occurs.  Returns
        the total number of bytes sent.
        """
        size = 0
        while data:
            resp = self._usb.write(pyusb.EP_MSG_OUT, data[:512], timeout)
            resp.wait()
            if resp.status <= 0:
                break
            data = data[resp.length:]
            size = size + resp.length
        return size

    def read(self, length, timeout=None):
        """Read data transparently over USB in small chunks
        until all bytes are received or a timeout occurs.  Returns
        the data buffer received.
        """
        data = b''
        while True:
            resp = self._usb.read(pyusb.EP_MSG_IN, timeout)
            resp.wait()
            if resp.status == -1:
                break
            data = data + resp.buffer
        return data
