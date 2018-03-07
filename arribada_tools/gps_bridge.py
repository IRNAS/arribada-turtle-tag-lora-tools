import ubx
import message
import logging


logger = logging.getLogger(__name__)

_timeout = 1.0


class ExceptionCommsError(Exception):
    pass


def gps_read(backend):
    cmd = message.ConfigMessage_GPS_READ_REQ(512)
    resp = backend.command_response(cmd, _timeout)
    if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
        logger.error('Bad response to GPS_READ_REQ')
        raise ExceptionCommsError
    if (resp.length > 0):
        return backend.read(resp.length, _timeout)
    return b''


def gps_write(backend, data):
    cmd = message.ConfigMessage_GPS_WRITE_REQ(len(data))
    resp = backend.command_response(cmd, _timeout)
    if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
        logger.error('Bad response to GPS_WRITE_REQ')
        raise ExceptionCommsError
    backend.write(data, _timeout)


def gps_bridge_session(backend, gps_data):
    responses = b''
    while True:
        (msg, gps_data) = ubx.extract(gps_data) 
        if msg:
            gps_write(backend, msg)
        else:
            break
        responses += gps_read(backend)
    return (responses, gps_data)
