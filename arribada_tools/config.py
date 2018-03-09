import struct
import logging
import sys
import json
import inspect


logger = logging.getLogger(__name__)


def _flatdict(base, olddict, newdict):
    """Convert a JSON dict to a flat dict i.e., nested dictionaries
    are assigned using dotted notation to represent hierarchy e.g.,
    bluetooth.advertising"""
    for i in olddict.keys():
        if isinstance(olddict[i], dict):
            _flatdict(base + ('.' if base else '') + i, olddict[i], newdict)
        else:
            newdict[base + ('.' if base else '') + i] = olddict[i]
    return newdict


def _pathsplit(fullpath):
    """Splits out the fullpath into a tuple comprising the variable name
    (i.e., given x.y.z, this would be z) and the root path (i.e., would
    be x.y given the previous example)"""
    items = fullpath.split('.')
    return ('.'.join(items[:-1]), items[-1])


def _findclass(fullpath):
    """Give a path name we identify to which configuration class it
    belongs.  The path uniquely identifies every configuration value
    and the root path denotes which class it belongs i.e., this code 
    performs a reverse search across all classes."""
    (path, param) = _pathsplit(fullpath)
    for i in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        cls = i[1]
        if issubclass(cls, ConfigItem) and cls != ConfigItem and path == cls.path and \
            param in cls.params:
            return (path, param, cls)
    return (None, None, None)


def decode(data):
    """Attempt to decode a single configuration item from an input data buffer.
    A tuple is returned containing an instance of the configuration object plus
    the input data buffer, less the amount of data consumed."""
    item = TaggedItem()
    if (len(data) < item.header_length):
        return (None, data)

    # Unpack header tag at current position
    item.unpack(data)

    # Find the correct configuration class based on the configuration tag
    cfg = None
    for i in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        cls = i[1]
        if issubclass(cls, ConfigItem) and cls != ConfigItem and \
            item.tag == cls.tag:
            cfg = cls()
            break
    if (cfg):
        try:
            cfg.unpack(data)
        except:
            # Likely insufficient bytes to unpack
            return (None, data)
        # Advance buffer past this configuration item
        data = data[cfg.length:]

    return (cfg, data)


def decode_all(data):
    """Iteratively decode an input data buffer to a list of configuration
    objects.
    """
    objects = []
    while data:
        (cfg, data) = decode(data)
        if cfg:
            objects += [ cfg ]
        else:
            break
    return objects


def encode_all(objects):
    """Encode a list of configuration objects, in order, to a serial byte
    stream.
    """
    data = b''
    for i in objects:
        data += i.pack()
    return data


def json_dumps(objects):
    """Convert a list of configuration objects representing a configuration
    set to JSON format."""
    obj_hash = {}
    for i in objects:
        h = obj_hash
        p = i.path.split('.')
        for j in p:
            if j not in h:
                h[j] = {}
            h = h[j]
        for j in i.params:
            h[j] = getattr(i, j)
    return json.dumps(obj_hash)


def json_loads(text):
    """Convert JSON text representing a configuration set to a list
    of configuration objects."""
    obj = {}
    flat = _flatdict('', json.loads(text), {})
    for i in flat:
        (path, param, cls) = _findclass(i)
        if cls:
            if path not in obj:
                obj[path] = cls()
            setattr(obj[path], param, flat[i])
    return [obj[i] for i in obj]


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
    """Configuration item bare (without any value)"""
    def __init__(self, bytes_to_follow=0):
        _Blob.__init__(self, b'<H', ['tag'])
        self.header_length = struct.calcsize(self._fmt)
        self.length = self.header_length + bytes_to_follow


class ConfigItem(TaggedItem):
    """A configuration item which should be subclassed"""
    def __init__(self, fmt=b'', args=[], **kwargs):
        TaggedItem.__init__(self, struct.calcsize(b'<' + fmt))
        self.extend(fmt, args)
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])


class ConfigItem_System_DeviceIdentifier(ConfigItem):
    tag = 0x0400
    path = 'system'
    params = ['deviceIdentifier']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'8s', self.params, **kwargs)


class ConfigItem_GPS_LogPositionEnable(ConfigItem):
    tag = 0x0000
    path = 'gps'
    params = ['logPositionEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_GPS_LogTTFFEnable(ConfigItem):
    tag = 0x0001
    path = 'gps'
    params = ['logTTFFEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_GPS_TriggerMode(ConfigItem):
    tag = 0x0002
    path = 'gps'
    params = ['triggerMode']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'B', self.params, **kwargs)


class ConfigItem_GPS_UARTBaudRate(ConfigItem):
    tag = 0x0003
    path = 'gps'
    params = ['uartBaudRate']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'I', self.params, **kwargs)


class ConfigItem_RTC_SyncToGPSEnable(ConfigItem):
    tag = 0x0600
    path = 'rtc'
    params = ['syncToGPSEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_RTC_CurrentDateTime(ConfigItem):
    tag = 0x0601
    path = 'rtc'
    params = ['day', 'month', 'year', 'hours', 'minutes', 'seconds']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'BBIBBB', self.params, **kwargs)


class ConfigItem_Logging_Enable(ConfigItem):
    tag = 0x0100
    path = 'logging'
    params = ['enable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_Logging_BytesWritten(ConfigItem):
    tag = 0x0101
    path = 'logging'
    params = ['bytesWritten']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'L', self.params, **kwargs)


class ConfigItem_Logging_FileSize(ConfigItem):
    tag = 0x0102
    path = 'logging'
    params = ['fileSize']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'L', self.params, **kwargs)


class ConfigItem_Logging_FileType(ConfigItem):
    tag = 0x0103
    path = 'logging'
    params = ['fileType']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'B', self.params, **kwargs)


class ConfigItem_Logging_GroupSensorReadingsEnable(ConfigItem):
    tag = 0x0104
    path = 'logging'
    params = ['groupSensorReadingsEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_Logging_StartEndSyncEnable(ConfigItem):
    tag = 0x0105
    path = 'logging'
    params = ['startEndSyncEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_Logging_DateTimeStampEnable(ConfigItem):
    tag = 0x0106
    path = 'logging'
    params = ['dateTimeStampEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_Logging_HighResolutionTimerEnable(ConfigItem):
    tag = 0x0106
    path = 'logging'
    params = ['highResolutionTimerEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_AXL_LogEnable(ConfigItem):
    tag = 0x0300
    path = 'accelerometer'
    params = ['logEnable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_AXL_SampleRate(ConfigItem):
    tag = 0x0301
    path = 'accelerometer'
    params = ['sampleRate']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'I', self.params, **kwargs)


class ConfigItem_AXL_LowThreshold(ConfigItem):
    tag = 0x0302
    path = 'accelerometer'
    params = ['lowThreshold']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'I', self.params, **kwargs)


class ConfigItem_AXL_HighThreshold(ConfigItem):
    tag = 0x0303
    path = 'accelerometer'
    params = ['highThreshold']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'I', self.params, **kwargs)


class ConfigItem_BLE_UUID(ConfigItem):
    tag = 0x0500
    path = 'bluetooth'
    params = ['UUID']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'16s', self.params, **kwargs)


class ConfigItem_BLE_BeaconEnable(ConfigItem):
    tag = 0x0501
    path = 'bluetooth.beacon'
    params = ['enable']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'?', self.params, **kwargs)


class ConfigItem_BLE_GeoFenceTriggerLocation(ConfigItem):
    tag = 0x0502
    path = 'bluetooth.geofence'
    params = ['longitude', 'latitude', 'radius']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'2lL', self.params, **kwargs)

    def pack(self):
        longitude = self.longitude
        latitude = self.latitude
        radius = self.radius
        self.longitude = int(self.longitude / 1E-7)
        self.latitude = int(self.latitude / 1E-7)
        self.radius = int(self.radius / 1E-2)
        data = ConfigItem.pack(self)
        self.longitude = longitude
        self.latitude = latitude
        self.radius = radius
        return data

    def unpack(self, data):
        ConfigItem.unpack(self, data)
        self.longitude = 1E-7 * self.longitude
        self.latitude = 1E-7 * self.latitude
        self.radius = 1E-2 * self.radius


class ConfigItem_BLE_BeaconAdvertisingInterval(ConfigItem):
    tag = 0x0503
    path = 'bluetooth.advertising'
    params = ['interval']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'I', self.params, **kwargs)


class ConfigItem_BLE_BeaconAdvertisingConfiguration(ConfigItem):
    tag = 0x0504
    path = 'bluetooth.advertising'
    params = ['configuration']

    def __init__(self, **kwargs):
        ConfigItem.__init__(self, b'B', self.params, **kwargs)
