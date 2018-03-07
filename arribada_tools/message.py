import struct
import logging
import inspect
import sys

logger = logging.getLogger(__name__)


def decode(data):
    """Attempt to decode a message from an input data buffer"""
    hdr = ConfigMessageHeader()
    if (len(data) < hdr.header_length):
        return (None, data)

    # Find first sync byte and decode from that position
    pos = data.find(ConfigMessageHeader.sync)
    if pos < 0:
        return (None, data)

    # Unpack message header at SYNC position
    hdr.unpack(data[pos:])

    msg = None
    unused_cls = [ ConfigMessage, ConfigMessageHeader ]
    for i in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        cls = i[1]
        if issubclass(cls, ConfigMessageHeader) and cls not in unused_cls and \
            msg.cmd == cls.cmd:
            msg = cls()
            break

    if (msg):
        msg.unpack(data)
        # Advance buffer past this message
        data = data[(pos + msg.length):]

    return (msg, data)


def convert_to_dict(obj):
    d = {}
    ignore = ['error_code', 'cmd', 'sync']
    for i in obj._args:
        if i not in ignore:
            d[i] = obj.i
    return d


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


class ConfigMessageHeader(_Blob):
    """Configuration message header"""
    sync = b'\x7E'

    def __init__(self, bytes_to_follow=0):
        _Blob.__init__(self, b'B', ['sync', 'cmd'])
        self.header_length = struct.calcsize(self._fmt)
        self.length = self.header_length + bytes_to_follow


class ConfigMessage(ConfigMessageHeader):
    """A configuration message which should be subclassed"""
    def __init__(self, fmt=b'', args=[], **kwargs):
        ConfigMessageHeader.__init__(self, struct.calcsize(fmt))
        self.extend(fmt, args)
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])


class GenericResponse(ConfigMessage):
    """A generic response message which should be subclassed"""
    cmd = 255
    name = 'GENERIC_RESP'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'B', ['error_code'], **kwargs)


class ConfigMessage_CFG_READ_REQ(ConfigMessage):

    cmd = 0
    name = 'CFG_READ_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'H', ['cfg_tag'], **kwargs)


class ConfigMessage_CFG_READ_RESP(ConfigMessage):

    cmd = 1
    name = 'CFG_READ_RESP'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'HI', ['error_code', 'length'], **kwargs)


class ConfigMessage_CFG_WRITE_REQ(ConfigMessage):

    cmd = 2
    name = 'CFG_WRITE_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'I', ['length'], **kwargs)


class ConfigMessage_CFG_SAVE_REQ(ConfigMessageHeader):

    cmd = 3
    name = 'CFG_SAVE_REQ'


class ConfigMessage_CFG_RESTORE_REQ(ConfigMessageHeader):

    cmd = 4
    name = 'CFG_RESTORE_REQ'


class ConfigMessage_CFG_ERASE_REQ(ConfigMessage):

    cmd = 5
    name = 'CFG_ERASE_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'H', ['cfg_tag'], **kwargs)


class ConfigMessage_CFG_PROTECT_REQ(ConfigMessageHeader):

    cmd = 6
    name = 'CFG_PROTECT_REQ'


class ConfigMessage_CFG_UNPROTECT_REQ(ConfigMessageHeader):

    cmd = 7
    name = 'CFG_UNPROTECT_REQ'


class ConfigMessage_GPS_WRITE_REQ(ConfigMessage):

    cmd = 8
    name = 'GPS_WRITE_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'I', ['length'], **kwargs)


class ConfigMessage_GPS_READ_REQ(ConfigMessage):

    cmd = 9
    name = 'GPS_READ_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'I', ['length'], **kwargs)


class ConfigMessage_GPS_RESP(ConfigMessage):

    cmd = 10
    name = 'GPS_RESP'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'BI', ['error_code', 'length'], **kwargs)


class ConfigMessage_GPS_CONFIG_REQ(ConfigMessage):

    cmd = 11
    name = 'GPS_CONFIG_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'?', ['enable'], **kwargs)


class ConfigMessage_BLE_CONFIG_REQ(ConfigMessage):

    cmd = 12
    name = 'BLE_CONFIG_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'?', ['enable'], **kwargs)


class ConfigMessage_BLE_WRITE_REQ(ConfigMessage):

    cmd = 13
    name = 'BLE_WRITE_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'BH', ['address', 'length'], **kwargs)


class ConfigMessage_BLE_READ_REQ(ConfigMessage):

    cmd = 14
    name = 'BLE_READ_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'BH', ['address', 'length'], **kwargs)


class ConfigMessage_STATUS_REQ(ConfigMessageHeader):

    cmd = 15
    name = 'STATUS_REQ'


class ConfigMessage_STATUS_RESP(ConfigMessage):

    cmd = 16
    name = 'BLE_READ_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'BIII', ['error_code', 'fw_version', 'fw_checksum', 'cfg_version'], **kwargs)


class ConfigMessage_FW_SEND_IMAGE_REQ(ConfigMessage):

    cmd = 17
    name = 'FW_SEND_IMAGE_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'BII', ['image_type', 'length', 'crc',], **kwargs)


class ConfigMessage_FW_SEND_IMAGE_COMPLETE_IND(GenericResponse):

    cmd = 18
    name = 'FW_SEND_IMAGE_COMPLETE_IND'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'B', ['error_code'], **kwargs)


class ConfigMessage_FW_APPLY_IMAGE_REQ(ConfigMessage):

    cmd = 19
    name = 'FW_APPLY_IMAGE_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'B', ['image_type'], **kwargs)


class ConfigMessage_RESET_REQ(ConfigMessage):

    cmd = 20
    name = 'RESET_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'B', ['reset_type'], **kwargs)


class ConfigMessage_BATTERY_STATUS_REQ(ConfigMessageHeader):

    cmd = 21
    name = 'BATTERY_STATUS_REQ'


class ConfigMessage_BATTERY_STATUS_RESP(ConfigMessage):

    cmd = 22
    name = 'BATTERY_STATUS_RESP'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'B?B', ['error_code', 'charging_ind', 'charging_level'], **kwargs)


class ConfigMessage_LOG_CREATE_REQ(ConfigMessage):

    cmd = 23
    name = 'LOG_CREATE_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'B?I', ['mode', 'sync_enable', 'max_file_size'], **kwargs)


class ConfigMessage_LOG_ERASE_REQ(ConfigMessageHeader):

    cmd = 24
    name = 'LOG_ERASE_REQ'


class ConfigMessage_LOG_READ_REQ(ConfigMessage):

    cmd = 25
    name = 'LOG_READ_REQ'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'II', ['start_offset', 'length'], **kwargs)


class ConfigMessage_LOG_READ_RESP(ConfigMessage):

    cmd = 26
    name = 'LOG_READ_RESP'

    def __init__(self, **kwargs):
        ConfigMessage.__init__(self, b'BI', ['error_code', 'length'], **kwargs)
