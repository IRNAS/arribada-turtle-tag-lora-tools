import message
import logging
import serial


logger = logging.getLogger(__name__)


_timeout = 0.75


class ExceptionCellularCommsTimeoutError(Exception):
    pass


class ExceptionCellularUnexpectedResponse(Exception):
    pass


class CellularSerialBackend(object):
    """Use a serial backend"""
    def __init__(self, path, baudrate, timeout=_timeout):
        self._serial = serial.Serial(port=path,
                                     baudrate=baudrate,
                                     bytesize=8,
                                     parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE,
                                     timeout=timeout,
                                     rtscts=True,
                                     inter_byte_timeout=None)

    def read(self, length=512):
        return self._serial.read(length)

    def write(self, data):
        self._serial.write(data)

    def cleanup(self):
        pass


class CellularBridgedBackend(object):
    """Use a USB/BLE bridged backend"""

    def __init__(self, backend):
        self._backend = backend

    def read(self, length=512):
        cmd = message.ConfigMessage_CELLULAR_READ_REQ(length=length)
        resp = self._backend.command_response(cmd, _timeout)
        if not resp or resp.name != 'Cellular_READ_RESP' or resp.error_code:
            logger.error('Bad response to Cellular_READ_REQ')
            raise ExceptionCellularCommsTimeoutError
        if (resp.length > 0):
            return self._backend.read(resp.length, _timeout)
        return b''

    def write(self, data):
        cmd = message.ConfigMessage_CELLULAR_WRITE_REQ(length=len(data));
        resp = self._backend.command_response(cmd, _timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to Cellular_WRITE_REQ')
            raise ExceptionCellularCommsTimeoutError
        self._backend.write(data, _timeout)

    def cleanup(self):
        self._backend.cleanup


class CellularConfig(object):
    """Cellular configuration wrapper class for AT commands to SARA-U270"""
    def __init__(self, cellular_backend):
        # See CellularBridgedBackend and CellularSerialBackend
        self._backend = cellular_backend
        self._sync_comms()
        self._disable_local_echo()

    def _expect(self, expected):
        resp = self._backend.read()
        logger.debug('read: %s exp: %s', resp.strip(), expected)
        if resp:
            if expected not in resp:
                raise ExceptionCellularUnexpectedResponse('Got %s but expected %s' % (resp, expected))
        else:
            raise ExceptionCellularCommsTimeoutError()

    def _flush(self):
        while (self._backend.read()):
            pass

    def _disable_local_echo(self):
        self._flush()
        self._backend.write('ATE0\r')
        self._expect('OK')

    def _sync_comms(self):
        retries = 3
        while retries:
            self._flush()
            self._backend.write('AT\r')
            try:
                self._expect('OK')
            except Exception as e:
                if retries == 0:
                    raise e
                retries = retries - 1
            else:
                break

    def _delete(self, index, name):
        cmd = 'AT+USECMNG=2,%u,"%s"\r' % (index, name)
        logger.debug('send: %s', cmd.strip())
        self._flush()
        self._backend.write(cmd)
        self._expect('OK')
        logger.info('%s removed successfully', name)

    def _create(self, index, name, data):
        cmd = 'AT+USECMNG=0,%u,"%s",%u\r' % (index, name, len(data))
        logger.debug('send: %s', cmd.strip())
        self._flush()
        self._backend.write(cmd)
        self._expect('>')
        self._backend.write(data)
        self._expect('OK')
        logger.info('%s added successfully', name)

    def delete_all(self):
        try:
            self._delete(0, 'root-CA.pem')
        except:
            logger.warn('Unable to remove root-CA.pem')
        try:
            self._delete(1, 'deviceCert.pem')
        except:
            logger.warn('Unable to remove deviceCert.pem')
        try:
            self._delete(2, 'deviceCert.key')
        except:
            logger.warn('Unable to remove deviceCert.key')

    def create_all(self, root_ca, cert, key):
        self._create(0, 'root-CA.pem', root_ca)
        self._create(1, 'deviceCert.pem', cert)
        self._create(2, 'deviceCert.key', key)

    def disable_auto_attach(self):
        cmd = 'AT+COPS=2\r'
        logger.debug('send: %s', cmd.strip())
        self._backend.write(cmd)
        self._expect('OK')
        cmd = 'AT&W0\r'
        logger.debug('send: %s', cmd.strip())
        self._backend.write(cmd)
        self._expect('OK')
