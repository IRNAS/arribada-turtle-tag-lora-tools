import logging
import base64
import boto3
import log
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

    db_client = boto3.client('dynamodb')

    # Keep track of log entries of interest
    gps_pos = None
    ttff = None
    timestamp = None
    battery = None

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
            entry = { 'UUID': { 'S': str(uid) },
                      'THING_NAME': { 'S': thing_name },
                      'TIMESTAMP': { 'N': str(timestamp) },
                      'LONGITUDE': { 'N': str(gps_pos.longitude) },                      
                      'LATITUDE': { 'N': str(gps_pos.latitude) },
                      'HEIGHT': { 'N': str(gps_pos.height) },
                      'H_ACC': { 'N': str(gps_pos.accuracyHorizontal) },
                      'V_ACC': { 'N': str(gps_pos.accuracyVertical) }
            }
            if ttff:
                entry['TTFF'] = { 'N': str((ttff.ttff / 1000.0)) }
            #logger.debug('GPS Location: %s', entry)

            resp = db_client.put_item(TableName='ArribadaGPSLocation', Item=entry)
            logger.debug('resp=%s', resp)

            # Reset fields
            gps_pos = None
            ttff = None
            timestamp = None

        if battery is not None and timestamp is not None:
            # Create table entry            
            uid = uuid.uuid4()
            entry = { 'UUID': { 'S': str(uid) },
                      'THING_NAME': { 'S': thing_name },
                      'TIMESTAMP': { 'N': str(timestamp) },
                      'BATTERY_LEVEL': { 'N': str(battery.charge) }
            }
            #logger.debug('Battery: %s', entry)

            resp = db_client.put_item(TableName='ArribadaBatteryCharge', Item=entry)
            logger.debug('resp=%s', resp)

            # Reset fields
            battery = None      
            timestamp = None

    return {
        "statusCode": 200
    }
