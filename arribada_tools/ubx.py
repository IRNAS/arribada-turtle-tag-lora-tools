import struct
from cgitb import text


_UBX_MIN_MESSAGE_LEN = 8


class _Sync(object):
    SYNC1 = '\xb5'
    SYNC2 = '\x62'

0x01:"ACK-ACK"
0x00:"ACK-NAK"
0x30:"AID-ALM"
0x33:"AID-AOP"
0x31:"AID-EPH"
0x02:"AID-HUI"
0x01:"AID-INI"
0x13:"CFG-ANT"
0x09:"CFG-CFG"
0x06:"CFG-DAT"
0x06:"CFG-DAT"
0x61:"CFG-DOSC"
0x85:"CFG-DYNSEED"
0x60:"CFG-ESRC"
0x84:"CFG-FIXSEED"
0x69:"CFG-GEOFENCE"
0x3E:"CFG-GNSS"
0x02:"CFG-INF"
0x39:"CFG-ITFM"
0x47:"CFG-LOGFILTER"
0x01:"CFG-MSG"
0x24:"CFG-NAV5"
0x23:"CFG-NAVX5"
0x17:"CFG-NMEA"
0x1E:"CFG-ODO"
0x3B:"CFG-PM2"
0x86:"CFG-PMS"
0x00:"CFG-PRT"
0x57:"CFG-PWR"
0x08:"CFG-RATE"
0x34:"CFG-RINV"
0x04:"CFG-RST"
0x11:"CFG-RXM"
0x16:"CFG-SBAS"
0x62:"CFG-SMGR"
0x3D:"CFG-TMODE2"
0x31:"CFG-TP5"
0x53:"CFG-TXSLOT"
0x1B:"CFG-USB"
0x10:"ESF-STATUS"
0x04:"INF-DEBUG"
0x00:"INF-ERROR"
0x02:"INF-NOTICE"
0x03:"INF-TEST"
0x01:"INF-WARNING"
0x07:"LOG-CREATE"
0x03:"LOG-ERASE"
0x0E:"LOG-FINDTIME"
0x08:"LOG-INFO"
0x0f:"LOG-RETRIEVEPOSE..."
0x0b:"LOG-RETRIEVEPOS"
0x0d:"LOG-RETRIEVESTRING"
0x09:"LOG-RETRIEVE"
0x04:"LOG-STRING"
0x28:"MON-GNSS"
0x0B:"MON-HW2"
0x09:"MON-HW"
0x02:"MON-IO"
0x06:"MON-MSGPP"
0x27:"MON-PATCH"
0x07:"MON-RXBUF"
0x21:"MON-RXR"
0x2E:"MON-SMGR"
0x08:"MON-TXBUF"
0x04:"MON-VER"
0x04:"MON-VER"
0x60:"NAV-AOPSTATUS"
0x22:"NAV-CLOCK"
0x31:"NAV-DGPS"
0x04:"NAV-DOP"
0x61:"NAV-EOE"
0x39:"NAV-GEOFENCE"
0x09:"NAV-ODO"
0x34:"NAV-ORB"
0x01:"NAV-POSECEF"
0x02:"NAV-POSLLH"
0x07:"NAV-PVT"
0x10:"NAV-RESETODO"
0x35:"NAV-SAT"
0x32:"NAV-SBAS"
0x06:"NAV-SOL"
0x03:"NAV-STATUS"
0x30:"NAV-SVINFO"
0x24:"NAV-TIMEBDS"
0x25:"NAV-TIMEGAL"
0x23:"NAV-TIMEGLO"
0x20:"NAV-TIMEGPS"
0x26:"NAV-TIMELS"
0x21:"NAV-TIMEUTC"
0x11:"NAV-VELECEF"
0x12:"NAV-VELNED"
0x61:"RXM-IMES"
0x41:"RXM-PMREQ"
0x15:"RXM-RAWX"
0x59:"RXM-RLM"
0x13:"RXM-SFRBX"
0x20:"RXM-SVSI"
0x01:"SEC-SIGN"
0x03:"SEC-UNIQID"

_upd_dict = {
    0x14:"UPD-SOS"
}

_tim_dict = {
    "class":"TIM",
    0x11:"TIM-DOSC",
    0x16:"TIM-FCHG",
    0x17:"TIM-HOC",
    0x13:"TIM-SMEAS",
    0x04:"TIM-SVIN",
    0x03:"TIM-TM2",
    0x12:"TIM-TOS",
    0x01:"TIM-TP",
    0x15:"TIM-VCOCAL",
    0x06:"TIM-VRFY",
}

_mga_dict = {
    "class":"MGA",
    0x60:"ACK-DATA0",
    0x20:"ANO",
    0x03:"BDS",
    0x80:"DBD",
    0x21:"FLASH",
    0x02:"GAL",
    0x06:"GLO",
    0x00:"GPS",
    0x40:"INI",
    0x05:"QZSS-EPH",
}

_class_dict = {
    0x01: { 'class': 'NAV' },
    0x02: { 'class': 'RXM' },
    0x04: { 'class': 'INF' },
    0x05: _ack_dict,
    0x06: { 'class': 'CFG' },
    0x09: { 'class': 'UPD' },
    0x0A: { 'class': 'MON' },
    0x0B: { 'class': 'AID' },
    0x0D: _tim_dict
    0x10: { 'class': 'ESF' },
    0x13: _mga_dict,
    0x21: { 'class': 'LOG' },
    0x27: { 'class': 'SEC' },
}

def _checksum(class_and_payload):
    ck_a = 0
    ck_b = 0
    for i in class_and_payload:
        ck_a = ck_a + struct.unpack('B', i)[0]
        ck_b = ck_b + ck_a
    ck = struct.pack('<BB', ck_a & 0xFF, ck_b & 0xFF)
    return ck


def extract(data):
    pos = data.find(_Sync.SYNC1)
    if pos < 0:
        return (b'', b'')
    if (len(data) - pos - _UBX_MIN_MESSAGE_LEN) < 0:
        return (b'', data[pos:])
    if data[pos+1] != _Sync.SYNC2:
        return (b'', data[pos+2:])
    length = struct.unpack('<H', data[pos+4:pos+6])[0]
    if (len(data) - pos - _UBX_MIN_MESSAGE_LEN) < length:
        return (b'', data[pos:])
    ck = _checksum(data[pos+2:pos+6+length])
    if ck[0] != data[pos+6+length] or \
        ck[1] != data[pos+7+length]:
        return (b'', data[pos:])
    else:
        return (data[pos:pos+_UBX_MIN_MESSAGE_LEN+length], data[pos+_UBX_MIN_MESSAGE_LEN+length:])


def build(cls, msg_id, payload):
    length = struct.pack('<H', len(payload))
    msg = _Sync.SYNC1 + _Sync.SYNC2 + cls + msg_id + length + payload
    return msg + _checksum(msg[2:])


def dump(msg):
    cls = struct.unpack('B', msg[2])[0]
    msg_id = struct.unpack('B', msg[3])[0]
    if cls in _class_dict:
        text = _class_dict[cls]['class']
        if msg_id in _class_dict[cls]:
            text = text + '-' + _class_dict[cls]['class'][msg_id]
        else:
            text = text + '-???(%02x)' % struct.unpack('B', msg_id)[0]
    else:
        text = '???(%02x)-???(%02x)' % (struct.unpack('B', cls)[0], struct.unpack('B', msg_id)[0])
    print text
