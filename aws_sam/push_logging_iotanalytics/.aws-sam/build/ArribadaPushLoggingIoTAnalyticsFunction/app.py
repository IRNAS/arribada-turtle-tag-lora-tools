import logging
import base64
import boto3
import log
import json
import uuid
import datetime
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def convert_date_time_to_timestamp(t):
    dt = datetime.datetime(t.year, t.month, t.day, t.hours, t.minutes, t.seconds)
    return int(time.mktime(dt.timetuple()))


def lambda_handler(event, context):

    thing_name = event['thing_name']
    log_data = base64.b64decode(event['data'])
    logger.debug('Got binary data length %s from %s', len(log_data), event['thing_name'])

    log_entries = log.decode_all(log_data)
    logger.debug('Got %s log entries', len(log_entries))

    iot_client = boto3.client('iotanalytics')

    # Keep track of log entries of interest
    gps_pos = None
    ttff = None
    timestamp = None
    battery = None

    iot_gps_messages = []
    iot_battery_messages = []

    for i in log_entries:

        # Check for log entries of interest
        if i.tag == log.LogItem_GPS_TimeToFirstFix.tag:
            ttff = i
        elif i.tag == log.LogItem_GPS_Position.tag:
            gps_pos = i
        elif i.tag == log.LogItem_Time_DateTime.tag:
            timestamp = convert_date_time_to_timestamp(i)
        elif i.tag == log.LogItem_Battery_Charge.tag:
            battery = i

        if gps_pos is not None and timestamp is not None:
            uid = uuid.uuid4()
            entry = { 'thing_name': thing_name,
                      'timestamp': timestamp,
                      'longitude': gps_pos.longitude,
                      'latitude': gps_pos.latitude,
                      'height': gps_pos.height,
                      'h_acc': gps_pos.accuracyHorizontal,
                      'v_acc': gps_pos.accuracyVertical
            }
            if ttff:
                entry['ttff'] = ttff.ttff / 1000.0

            #logger.debug('GPS Location: %s', entry)
            iot_gps_messages.append({
                'messageId': str(uid),
                'payload': json.dumps(entry)
                })

            # Reset fields
            gps_pos = None
            ttff = None
            timestamp = None

        if battery is not None and timestamp is not None:
            # Create table entry            
            uid = uuid.uuid4()
            entry = { 'thing_name': thing_name,
                      'timestmap': timestamp,
                      'battery_level': battery.charge
            }
            #logger.debug('Battery: %s', entry)

            iot_battery_messages.append({
                'messageId': str(uid),
                'payload': json.dumps(entry)
                })

            # Reset fields
            battery = None      
            timestamp = None

    if iot_gps_messages:
        #resp = iot_client.batch_put_message(channelName='arribada_gps_location', messages=iot_gps_messages)
        #logger.debug('resp=%s', resp)
        pass

    if iot_battery_messages:
        resp = iot_client.batch_put_message(channelName='arribada_battery_charge', messages=iot_battery_messages)
        logger.debug('resp=%s', resp)

    return {
        "statusCode": 200
    }
