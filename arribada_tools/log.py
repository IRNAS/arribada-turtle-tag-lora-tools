import struct
import logging
import sys
import inspect
import binascii

logger = logging.getLogger(__name__)

def decode(data, offset):
    """Attempt to decode a single log item from an input data buffer.
    A tuple is returned containing an instance of the log object plus
    the input data buffer, less the amount of data consumed."""
    item = TaggedItem()
    if ((len(data) + offset) < item.header_length):
        return None

    # Unpack header tag at current position
    item.unpack(data[offset:offset + item.header_length])

    # Find the correct configuration class based on the configuration tag
    cfg = None
    for i in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        cls = i[1]
        if issubclass(cls, LogItem) and cls != LogItem and \
            item.tag == cls.tag:
            cfg = cls()
            break
    if (cfg):
        try:
            cfg.unpack(data[offset:offset + cfg.length])
        except:
            return None # Likely insufficient bytes to unpack

    return cfg

def decode_all(data):
    """Iteratively decode an input data buffer to a list of log
    objects.
    """
    objects = []
    offset = 0
    while offset < len(data):
        cfg = decode(data, offset)
        if cfg:
            objects += [ cfg ]
            offset += cfg.length
        else:
            break
    return objects


def encode_all(objects):
    """Encode a list of log objects, in order, to a serial byte
    stream.
    """
    data = b''
    for i in objects:
        data += i.pack()
    return data


class _Blob(object):
    """Blob object is a container for arbitrary message fields which
    can be packed / unpacked using python struct"""
    _fmt = ''
    _args = []

    def __init__(self, fmt, args):
        self._fmt = fmt
        self._args = args

    def extend(self, fmt, args):
        self._fmt += fmt
        self._args += args

    def pack(self):
        packer = struct.Struct(self._fmt)
        args = tuple([getattr(self, k) for k in self._args])
        return packer.pack(*args)

    def unpack(self, data):
        unpacker = struct.Struct(self._fmt)
        unpacked = unpacker.unpack_from(data)
        i = 0
        for k in self._args:
            setattr(self, k, unpacked[i])
            i += 1

    def __repr__(self):
        s = self.__class__.__name__ + ' contents:\n'
        for i in self._args:
            s += i + ' = ' + str(getattr(self, i, 'undefined')) + '\n'
        return s


class TaggedItem(_Blob):
    """Tagged item bare (without any value)"""
    def __init__(self, bytes_to_follow=0):
        _Blob.__init__(self, b'<B', ['tag'])
        self.header_length = struct.calcsize(self._fmt)
        self.length = self.header_length + bytes_to_follow


class LogItem(TaggedItem):
    """A log item which should be subclassed"""
    def __init__(self, fmt=b'', args=[], **kwargs):
        TaggedItem.__init__(self, struct.calcsize(b'<' + fmt))
        self.extend(fmt, args)
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])


class LogItem_Builtin_LogStart(LogItem):
    tag = 0x7E
    name = 'LogStart'


class LogItem_Builtin_LogEnd(LogItem):
    tag = 0x7F
    name = 'LogEnd'
    fields = ['parity']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'B', self.fields, **kwargs)


class LogItem_GPS_Position(LogItem):
    tag = 0x00
    name = 'GPSPosition'
    fields = ['iTOW', 'longitude', 'latitude', 'height', 'accuracyHorizontal', 'accuracyVertical']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'IlllII', self.fields, **kwargs)

    def pack(self):
        longitude = self.longitude
        latitude = self.latitude
        height = self.height
        accuracyHorizontal = self.accuracyHorizontal
        accuracyVertical = self.accuracyVertical
        self.longitude = int(self.longitude / 1E-7)
        self.latitude = int(self.latitude / 1E-7)
        self.height = int(self.height * 1000.0)
        self.accuracyHorizontal = int(self.accuracyHorizontal * 1000.0)
        self.accuracyVertical = int(self.accuracyVertical * 1000.0)
        data = LogItem.pack(self)
        self.longitude = longitude
        self.latitude = latitude
        self.height = height
        self.accuracyHorizontal = accuracyHorizontal
        self.accuracyVertical = accuracyVertical
        return data

    def unpack(self, data):
        LogItem.unpack(self, data)
        self.longitude = 1E-7 * self.longitude
        self.latitude = 1E-7 * self.latitude
        self.height = self.height / 1000.0
        self.accuracyHorizontal = self.accuracyHorizontal / 1000.0
        self.accuracyVertical = self.accuracyVertical / 1000.0


class LogItem_GPS_TimeToFirstFix(LogItem):
    tag = 0x01
    name = 'TimeToFirstFix'
    fields = ['ttff']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'I', self.fields, **kwargs)


class LogItem_Pressure_Pressure(LogItem):
    tag = 0x02
    name = 'Pressure'
    fields = ['pressure']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'i', self.fields, **kwargs)

    def pack(self):
        pressure = self.pressure
        self.pressure = int(self.pressure * 1000.0)
        data = LogItem.pack(self)
        self.pressure = pressure
        return data

    def unpack(self, data):
        LogItem.unpack(self, data)
        self.pressure = self.pressure / 1000.0

class LogItem_AXL_XYZ(LogItem):
    tag = 0x03
    name = 'Accelerometer'
    fields = ['x', 'y', 'z']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'3h', self.fields, **kwargs)


class LogItem_Time_DateTime(LogItem):
    tag = 0x04
    name = 'DateTime'
    fields = ['year', 'month', 'day', 'hours', 'minutes', 'seconds']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'H5B', self.fields, **kwargs)


class LogItem_Time_HighResTimer(LogItem):
    tag = 0x05
    name = 'HighResTimer'
    fields = ['hrt']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'Q', self.fields, **kwargs)


class LogItem_Temperature_Temperature(LogItem):
    tag = 0x06
    name = 'Temperature'
    fields = ['temperature']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'H', self.fields, **kwargs)


class LogItem_SaltwaterSwitch_Surfaced(LogItem):
    tag = 0x07
    name = 'Surfaced'


class LogItem_SaltwaterSwitch_Submerged(LogItem):
    tag = 0x08
    name = 'Submerged'


class LogItem_Battery_Charge(LogItem):
    tag = 0x09
    name = 'BatteryCharge'
    fields = ['charge']

    def __init__(self, **kwargs):
        LogItem.__init__(self, b'B', self.fields, **kwargs)