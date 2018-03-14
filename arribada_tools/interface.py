import config
import message
import logging
import binascii


logger = logging.getLogger(__name__)


class ExceptionBackendCommsError(Exception):
    pass


class ConfigInterface(object):

    timeout = 2.0

    def __init__(self, backend):
        self._backend = backend

    def gps_config(self, enable):
        cmd = message.ConfigMessage_GPS_CONFIG_REQ(enable=enable)
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to GPS_CONFIG_REQ')
            raise ExceptionBackendCommsError

    def write_json_configuration(self, json):
        objs = config.json_loads(json)
        config_data = config.encode_all(objs)
        cmd = message.ConfigMessage_CFG_WRITE_REQ(length=len(config_data))
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to CFG_WRITE_REQ')
            raise ExceptionBackendCommsError
        length = self._backend.write(config_data, self.timeout)
        if length != len(config_data):
            logger.error('Failed to send all configuration bytes (%u/%u)', length, len(config_data))
            raise ExceptionBackendCommsError
        resp = self._backend.command_response(None, self.timeout)
        if not resp or resp.name != 'CFG_WRITE_CNF' or resp.error_code:
            logger.error('Did not receive valid CFG_WRITE_CNF')
            raise ExceptionBackendCommsError

    def read_json_configuration(self, tag=0xFFFF):
        cmd = message.ConfigMessage_CFG_READ_REQ(cfg_tag=tag)
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'CFG_READ_RESP' or resp.error_code:
            logger.error('Bad response to CFG_READ_REQ')
            raise ExceptionBackendCommsError
        config_data = self._backend.read(resp.length, self.timeout)
        if resp.length != len(config_data) or resp.error_code:
            logger.error('Failed to receive expected configuration bytes (%u/%u)',
                         len(config_data), resp.length)
            raise ExceptionBackendCommsError
        objs = config.decode_all(config_data)
        return config.json_dumps(objs)

    def protect_configuration(self):
        cmd = message.ConfigMessage_CFG_PROTECT_REQ()
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to CFG_PROTECT_REQ')
            raise ExceptionBackendCommsError

    def unprotect_configuration(self):
        cmd = message.ConfigMessage_CFG_UNPROTECT_REQ()
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to CFG_UNPROTECT_REQ')
            raise ExceptionBackendCommsError

    def erase_configuration(self, tag=0xFFFF):
        cmd = message.ConfigMessage_CFG_ERASE_REQ(cfg_tag=tag)
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to CFG_ERASE_REQ')
            raise ExceptionBackendCommsError

    def restore_configuration(self):
        cmd = message.ConfigMessage_CFG_RESTORE_REQ()
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to CFG_RESTORE_REQ')
            raise ExceptionBackendCommsError

    def save_configuration(self):
        cmd = message.ConfigMessage_CFG_SAVE_REQ()
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to CFG_SAVE_REQ')
            raise ExceptionBackendCommsError

    def create_log_file(self, file_type, sync_enable=False, max_size=0):
        cmd = message.ConfigMessage_LOG_CREATE_REQ(mode=file_type,
                                                   sync_enable=sync_enable,
                                                   max_file_size=max_size)
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to LOG_CREATE_REQ')
            raise ExceptionBackendCommsError

    def erase_log_file(self):
        cmd = message.ConfigMessage_LOG_ERASE_REQ()
        # Could take 30 seconds to erase a large log file so use a
        # larger timeout period for this command
        resp = self._backend.command_response(cmd, 30 + self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to LOG_ERASE_REQ')
            raise ExceptionBackendCommsError

    def read_log_file(self, start_offset=0, length=0):
        cmd = message.ConfigMessage_LOG_READ_REQ(start_offset=start_offset, length=length)
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'LOG_READ_RESP' or resp.error_code:
            logger.error('Bad response to LOG_READ_REQ')
            raise ExceptionBackendCommsError
        return self._backend.read(resp.length, self.timeout)

    def fw_upgrade(self, image_type, data):
        crc = binascii.crc32(data)
        cmd = message.ConfigMessage_FW_SEND_IMAGE_REQ(image_type=image_type,
                                                      length=len(data),
                                                      crc=crc)
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to FW_SEND_IMAGE_REQ')
            raise ExceptionBackendCommsError
        length = self._backend.write(data, self.timeout)
        if length != len(data):
            logger.error('Failed to send all firmware data bytes (%u/%u)', length, len(data))
            raise ExceptionBackendCommsError
        resp = self._backend.command_response(None, self.timeout)
        if not resp or resp.name != 'FW_SEND_IMAGE_COMPLETE_CNF' or resp.error_code:
            logger.error('Did not receive valid FW_SEND_IMAGE_COMPLETE_CNF')
            raise ExceptionBackendCommsError
        cmd = message.ConfigMessage_FW_APPLY_IMAGE_REQ(image_type=image_type)
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to FW_APPLY_IMAGE_REQ')
            raise ExceptionBackendCommsError

    def reset(self):
        cmd = message.ConfigMessage_RESET_REQ()
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'GENERIC_RESP' or resp.error_code:
            logger.error('Bad response to RESET_REQ')
            raise ExceptionBackendCommsError

    def get_battery_status(self):
        cmd = message.ConfigMessage_BATTERY_STATUS_REQ()
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'BATTERY_STATUS_RESP' or resp.error_code:
            logger.error('Bad response to BATTERY_STATUS_REQ')
            raise ExceptionBackendCommsError
        return message.convert_to_dict(resp)

    def get_status(self):
        cmd = message.ConfigMessage_STATUS_REQ()
        resp = self._backend.command_response(cmd, self.timeout)
        if not resp or resp.name != 'STATUS_RESP' or resp.error_code:
            logger.error('Bad response to STATUS_REQ')
            raise ExceptionBackendCommsError
        return message.convert_to_dict(resp)
