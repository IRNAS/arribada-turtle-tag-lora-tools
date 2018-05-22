import struct
import os
from bluepy.btle import UUID, Peripheral, DefaultDelegate

config_service_uuid = UUID('04831523-6c9d-6ca9-5d41-03ad4fff4abb')
config_char_uuid = UUID('04831524-6c9d-6ca9-5d41-03ad4fff4abb')
MAX_PACKET_SIZE = 20

HCI_DEV = 0 if 'HCI_DEV' not in os.environ else int(os.environ['HCI_DEV'])


class Buffer():
    def __init__(self):
        self._buffer = b''

    def write(self, data):
        self._buffer = self._buffer + data

    def read(self, length):
        data = self._buffer[:length]
        self._buffer = self._buffer[length:]
        return data
    
    def occupancy(self):
        return len(self._buffer)


class MyDelegate(DefaultDelegate):

    def __init__(self, buf):
        DefaultDelegate.__init__(self)
        self._buffer = buf

    def handleNotification(self, cHandle, data):
        self._buffer.write(data)


def notifications_enable(p, char):
    for desc in p.getDescriptors(char.getHandle(), 0x00F): 
        if desc.uuid == 0x2902:
            ccc_handle = desc.handle
            p.writeCharacteristic(ccc_handle, struct.pack('<bb', 0x01, 0x00))
            break


class BluetoothTracker():
    def __init__(self, uuid):
        self._buffer = Buffer()
        self._periph = Peripheral(uuid, 'random', HCI_DEV)
        self._periph.setDelegate(MyDelegate(self._buffer))
        self._config_service = self._periph.getServiceByUUID(config_service_uuid)
        self._config_char = self._config_service.getCharacteristics(config_char_uuid)[0]
        notifications_enable(self._periph, self._config_char)

    def write(self, data):
        while data:
            self._config_char.write(data[:MAX_PACKET_SIZE])
            data = data[MAX_PACKET_SIZE]

    def read(self, length, timeout=0):
        if not self._buffer.occupancy():
            self.periph.waitForNotifications(timeout)
        return self._buffer.read(length)
