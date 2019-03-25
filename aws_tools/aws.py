import boto3
import os
import logging
import random
import time
from OpenSSL import crypto


logger = logging.getLogger(__name__)

# This sets a nominal 10 years expiry on the CA certificate
CERT_EXPIRY = 10*365*24*60*60

# These identifiers can be freely set.  However, the REGION must map
# to a valid AWS region identifier.  This must also be the
# same region identifier that was used when you configured
# your aws cli for the first time.  This tool depends on
# the existence of a valid client configuration for the
# aws cli tool.  Not doing so will result in boto3 client
# authentication errors.
S3_BUCKET = 'arribada'
REGION = 'us-west-2'
IOT_GROUP = 'arribada'
IOT_POLICY = 'arribada'


# The IOT policy is by default relaxed and should therefore
# work on any AWS account or with any topic path structure
# Any thing registered onto the account
IOT_POLICY_DOCUMENT = """{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "iot:*",
    "Resource": "*"
  }
]}"""

# !!! Don't change these without checking the AWS SAM module code won't break since these
# names are also hardcoded into the SAM code !!!
IOT_PIPELINES = ['arribada_gps_location', 'arribada_device_status', 'arribada_battery_charge']

# The topic path structure is encoded into these IOT rules for HTTP GET/POST:
#
# logging => POST     $arn:port/topics/thingName/logging
# shadow  => GET/POST $arn:port/things/thingName/shadow
#
# IMPORTANT NOTE:
#
# The shadow topic is fixed by Amazon and can't be changed.  Don't ever change this!
#
# The logging topic could be put onto any topic path starting with /topics/... but you should be aware
# that the IOT rule would need to change to ensure the thingName wildcard is correctly extracted from
# the topic path

IOT_RULES = [
                ('push_shadow_iotanalytics', 'PushShadowIOT',
                 "SELECT * AS update, topic(3) as thing_name FROM '$aws/things/+/shadow/update/documents'"),
                ('push_logging_iotanalytics', 'PushLoggingIOT',
                 "SELECT encode(*, 'base64') AS data, timestamp() AS ts, topic(1) as thing_name FROM '+/logging'")
            ]


# This specifies an IOT dataset update every 15 min on the hour -- this is the minimum permitted
# by the AWS IoT Analytics data pipeline scheduling job
# Forced updates can be done through the AWS IoT Analytics dashboard or via the AWS CLI tool
IOT_DATASET_CRON_SCHEDULE = 'cron(0/15 * * * ? *)'


def lookup_iot_channel_by_name(name):
    cli = boto3.client('iotanalytics')
    channels = cli.list_channels()
    for i in channels['channelSummaries']:
        if name in i['channelName']:
            return i['channelName']


def lookup_iot_datastore_by_name(name):
    cli = boto3.client('iotanalytics')
    datastores = cli.list_datastores()
    for i in datastores['datastoreSummaries']:
        if name in i['datastoreName']:
            return i['datastoreName']


def lookup_iot_pipeline_by_name(name):
    cli = boto3.client('iotanalytics')
    pipelines = cli.list_pipelines()
    for i in pipelines['pipelineSummaries']:
        if name in i['pipelineName']:
            return i['pipelineName']


def lookup_iot_dataset_by_name(name):
    cli = boto3.client('iotanalytics')
    datasets = cli.list_datasets()
    for i in datasets['datasetSummaries']:
        if name in i['datasetName']:
            return i['datasetName']


def lookup_function_arn_by_name(name):
    cli = boto3.client('lambda')
    funcs = cli.list_functions()
    for i in funcs['Functions']:
        if name in i['FunctionArn']:
            return i['FunctionArn']

def lookup_iam_role_by_name(name):
    cli = boto3.client('iam')
    funcs = cli.list_roles()
    for i in funcs['Roles']:
        if name in i['RoleName']:
            return i['RoleName']


def lookup_iot_rule_by_name(name):
    cli = boto3.client('iot')
    funcs = cli.list_topic_rules()
    for i in funcs['rules']:
        if name in i['ruleName']:
            return i['ruleName']


def lookup_iot_rule_arn_by_name(name):
    cli = boto3.client('iot')
    funcs = cli.list_topic_rules()
    for i in funcs['rules']:
        if name in i['ruleName']:
            return i['ruleArn']


def lookup_iot_group_arn_by_name(name):
    cli = boto3.client('iot')
    groups = cli.list_thing_groups()
    for i in groups['thingGroups']:
        if name == i['groupName']:
            return i['groupArn']


def lookup_iot_policy_arn_by_name(name):
    cli = boto3.client('iot')
    policies = cli.list_policies()
    for i in policies['policies']:
        if name == i['policyName']:
            return i['policyArn']


def check_s3():
    cli = boto3.client('s3')
    buckets = [ b['Name'] for b in cli.list_buckets()['Buckets'] ]
    return S3_BUCKET in buckets


def create_s3():
    if not check_s3():
        cli = boto3.client('s3')
        cli.create_bucket(Bucket=S3_BUCKET,
                          CreateBucketConfiguration={
                            'LocationConstraint': REGION
                          })
    else:
        logger.warn('S3 bucket %s already exists', S3_BUCKET)


def delete_s3():
    if check_s3():
        cli = boto3.client('s3')
        objs = cli.list_objects(Bucket=S3_BUCKET)
        for i in objs['Contents']:
            cli.delete_object(Bucket=S3_BUCKET, Key=i['Key'])
        cli.delete_bucket(Bucket=S3_BUCKET)


def lookup_cloudformation_stack_by_name(name):
    cli = boto3.client('cloudformation')
    stacks = cli.list_stacks()
    for i in stacks['StackSummaries']:
        if name in i['StackName']:
            return i['StackName']


def delete_sam_packages():

    for i in IOT_RULES:
        lambda_fn = lookup_function_arn_by_name(i[1])
        if lambda_fn:
            cli = boto3.client('lambda')
            cli.delete_function(FunctionName=lambda_fn)
        stack_name = lookup_cloudformation_stack_by_name(i[1])
        if stack_name:
            cli = boto3.client('cloudformation')
            cli.delete_stack(StackName=stack_name)


def deploy_sam_packages():

    if not check_s3():
        logger.error('S3 bucket %s must be created before deploying SAM packages', S3_BUCKET)
        return
    # These commands require that the "sam" tool is on your path and shall be invoked
    # from the system shell
    sam_commands = "cd %s; sam build; sam package --s3-bucket %s \
      --template-file template.yaml --output-template-file /tmp/tmp.yaml; \
      sam deploy --template-file /tmp/tmp.yaml --stack-name %s --capabilities CAPABILITY_IAM"
    for i in IOT_RULES:
        if not lookup_function_arn_by_name(i[1]):
            os.system(sam_commands % ('../aws_sam/' + i[0], S3_BUCKET, i[1]))
        else:
            logger.warn('Lambda function %s already installed', i[1])


def delete_iot_pipelines():
    cli = boto3.client('iotanalytics')
    for i in IOT_PIPELINES:

        if lookup_iot_dataset_by_name(i):
            cli.delete_dataset(datasetName=i)

        if lookup_iot_pipeline_by_name(i):
            cli.delete_pipeline(pipelineName=i)
        
        if lookup_iot_datastore_by_name(i):
            cli.delete_datastore(datastoreName=i)
        
        if lookup_iot_channel_by_name(i):
            cli.delete_channel(channelName=i)


def create_iot_pipelines():
    cli = boto3.client('iotanalytics')
    for i in IOT_PIPELINES:

        if not lookup_iot_channel_by_name(i):
            cli.create_channel(channelName=i)
        else:
            logger.warn('IOT channel %s already exists', i)

        if not lookup_iot_datastore_by_name(i):
            cli.create_datastore(datastoreName=i)
        else:
            logger.warn('IOT datastore %s already exists', i)

        if not lookup_iot_pipeline_by_name(i):
            cli.create_pipeline(pipelineName=i,
                                pipelineActivities=[
                                {
                                  'channel': {
                                     'channelName': i,
                                     'name': 'a_1',
                                     'next': 'a_2',
                                  }
                                },
                                {
                                  'datastore': {
                                      'datastoreName': i,
                                      'name': 'a_2'
                                  }
                                }])
        else:
            logger.warn('IOT pipeline %s already exists', i)
            
        if not lookup_iot_dataset_by_name(i):
            cli.create_dataset(datasetName=i,
                               actions=[
                               {
                                'actionName': 'query_%s' % i,
                                'queryAction': {
                                  'sqlQuery': 'SELECT * FROM %s' % i,
                                  'filters': []
                                }
                               }],
                               triggers=[
                               {
                                'schedule': {
                                  'expression': IOT_DATASET_CRON_SCHEDULE
                                }
                               }])
        else:
            logger.warn('IOT dataset %s already exists', i)


def delete_iot_rules():
    cli = boto3.client('iot')
    for i in IOT_RULES:
        rule_name = lookup_iot_rule_by_name(i[0])
        if rule_name:
            cli.delete_topic_rule(ruleName=rule_name)


def create_iot_rules():
    cli = boto3.client('iot')
    for i in IOT_RULES:
        lambda_arn = lookup_function_arn_by_name(i[1])
        if lambda_arn:
            # Annoyingly this function does not return
            # anything such as the ruleArn which would be quite useful
            cli.create_topic_rule(ruleName=i[0],
                                  topicRulePayload={
                                    'sql': i[2],
                                    'awsIotSqlVersion': '2016-03-23-beta',
                                    'actions': [{
                                      'lambda': {
                                        'functionArn': lambda_arn
                                      }
                                    }]
                                  })
            rule_arn = lookup_iot_rule_arn_by_name(i[0])
            if rule_arn:
                lam = boto3.client('lambda')
                lam.add_permission(FunctionName=lambda_arn,
                                   StatementId=i[0],
                                   Action='lambda:InvokeFunction',
                                   Principal='iot.amazonaws.com',
                                   SourceArn=rule_arn)
            else:
                logger.error('Could not add permission for rule %s to invoke lambda %s', i[0], lambda_arn)
        else:
            logger.error('Dependency lambda function %s is not installed', i[1])


def delete_iam_roles():
    """These are automatically generated by the SAM tool and
       can be deleted by performing an IAM look-up first"""
    cli = boto3.client('iam')
    for i in IOT_RULES:
        role_name = lookup_iam_role_by_name(i[1])
        if role_name:
            cli.delete_role(RoleName=role_name)


def delete_iot_thing(thing_name):
    cli = boto3.client('iot')
    principals = cli.list_thing_principals(thingName=thing_name)
    for p in principals['principals']:
        cli.detach_thing_principal(thingName=thing_name, principal=p)
    cli.delete_thing(thingName=thing_name)


def delete_iot_things():
    # TODO: need to remove client certificate for each thing
    """Delete only things that are in the IOT_GROUP group"""
    cli = boto3.client('iot')
    groups = cli.list_thing_groups()
    if IOT_GROUP not in [ i['groupName'] for i in groups['thingGroups'] ]:
        return
    things = cli.list_things_in_thing_group(thingGroupName=IOT_GROUP)
    for i in things['things']:
        principals = cli.list_thing_principals(thingName=i)
        for p in principals['principals']:
            cli.detach_thing_principal(thingName=i, principal=p)
        cli.delete_thing(thingName=i)


def delete_iot_thing_group():
    """Delete the IOT_GROUP thing group only if the group is empty"""
    cli = boto3.client('iot')
    groups = cli.list_thing_groups()
    group = None
    for i in groups['thingGroups']:
        if IOT_GROUP in i['groupName']:
            group = i
            break
    if group is None:
        return
    things = cli.list_things_in_thing_group(thingGroupName=IOT_GROUP)
    if things['things']:
        logger.error('Must delete all things from group %s first', IOT_GROUP)
        return
    cli.delete_thing_group(thingGroupName=IOT_GROUP)


def delete_iot_policies():
    cli = boto3.client('iot')
    policies = cli.list_policies()
    if IOT_POLICY not in [ i['policyName'] for i in policies['policies'] ]:
        return
    cli.delete_policy(policyName=IOT_POLICY)


def delete_iot_certificates_by_ca(ca_cert_id):
    cli = boto3.client('iot')
    ca_certs = cli.list_ca_certificates()
    if ca_cert_id not in [ i['certificateId'] for i in ca_certs['certificates'] ]:
        return
    certs = cli.list_certificates_by_ca(caCertificateId=ca_cert_id)
    policy_arn = lookup_iot_policy_arn_by_name(IOT_POLICY)
    for i in certs['certificates']:
        cli.update_certificate(certificateId=i['certificateId'], newStatus='INACTIVE')
        if policy_arn:
            cli.detach_policy(policyName=IOT_POLICY, target=i['certificateArn'])
        cli.delete_certificate(certificateId=i['certificateId'])


def delete_iot_ca_certificate(ca_cert_id):
    cli = boto3.client('iot')
    ca_certs = cli.list_ca_certificates()
    if ca_cert_id not in [ i['certificateId'] for i in ca_certs['certificates'] ]:
        return
    cli.update_ca_certificate(certificateId=ca_cert_id, newStatus='INACTIVE')
    cli.delete_ca_certificate(certificateId=ca_cert_id)


def create_iot_policy():
    cli = boto3.client('iot')
    policies = cli.list_policies()
    if IOT_POLICY in [ i['policyName'] for i in policies['policies'] ]:
        return
    cli.create_policy(policyName=IOT_POLICY,
                      policyDocument=IOT_POLICY_DOCUMENT)


def create_iot_thing_group():
    cli = boto3.client('iot')
    groups = cli.list_thing_groups()
    if IOT_GROUP in [ i['groupName'] for i in groups['thingGroups'] ]:
        return
    cli.create_thing_group(thingGroupName=IOT_GROUP)


def generate_root_cert(common_name):

    ca_key = crypto.PKey()
    ca_key.generate_key(crypto.TYPE_RSA, 2048)

    ca_cert = crypto.X509()
    ca_cert.set_version(2)
    ca_cert.set_serial_number(random.randint(50000000, 100000000))

    ca_subj = ca_cert.get_subject()
    ca_subj.commonName = common_name

    ca_cert.add_extensions([
        crypto.X509Extension("subjectKeyIdentifier", False, "hash", subject=ca_cert),
    ])

    ca_cert.add_extensions([
        crypto.X509Extension("authorityKeyIdentifier", False, "keyid:always", issuer=ca_cert),
    ])

    ca_cert.add_extensions([
        crypto.X509Extension("basicConstraints", False, "CA:TRUE"),
        crypto.X509Extension("keyUsage", False, "keyCertSign, cRLSign"),
    ])

    ca_cert.set_issuer(ca_subj)
    ca_cert.set_pubkey(ca_key)
    ca_cert.gmtime_adj_notBefore(0)
    ca_cert.gmtime_adj_notAfter(CERT_EXPIRY)
    ca_cert.sign(ca_key, 'sha256')

    return (ca_cert, ca_key)


def generate_cert_from_root(root, common_name):

    (ca_cert, ca_key) = root
    ca_subj = ca_cert.get_subject()

    client_key = crypto.PKey()
    client_key.generate_key(crypto.TYPE_RSA, 2048)
    
    client_cert = crypto.X509()
    client_cert.set_version(2)
    client_cert.set_serial_number(random.randint(50000000,100000000))

    client_subj = client_cert.get_subject()
    client_subj.commonName = common_name

    client_cert.add_extensions([
        crypto.X509Extension("basicConstraints", False, "CA:FALSE"),
        crypto.X509Extension("subjectKeyIdentifier", False, "hash", subject=client_cert),
    ])

    client_cert.add_extensions([
        crypto.X509Extension("authorityKeyIdentifier", False, "keyid:always", issuer=ca_cert),
        crypto.X509Extension("extendedKeyUsage", False, "clientAuth"),
        crypto.X509Extension("keyUsage", False, "digitalSignature"),
    ])

    client_cert.set_issuer(ca_subj)
    client_cert.set_pubkey(client_key)
    client_cert.gmtime_adj_notBefore(0)
    client_cert.gmtime_adj_notAfter(CERT_EXPIRY)
    client_cert.sign(ca_key, 'sha256')

    return (client_cert, client_key)


def register_root_ca(root_ca):

    cli = boto3.client('iot')
    ca_certs = cli.list_ca_certificates()
    if ca_certs['certificates']:
        logger.error('AWS account already has CA certificate(s)')
        raise Exception('CA certificate already exists')
    registration_code = cli.get_registration_code()['registrationCode']
    (verif_cert, _) = generate_cert_from_root(root_ca, registration_code)
    (root_cert, _) = root_ca
    resp = cli.register_ca_certificate(caCertificate=crypto.dump_certificate(crypto.FILETYPE_PEM, root_cert),
                                       verificationCertificate=crypto.dump_certificate(crypto.FILETYPE_PEM, verif_cert),
                                       setAsActive=True)
    return resp['certificateId']


def register_new_thing(root_ca, thing_name):

    cert = generate_cert_from_root(root_ca, thing_name)

    cli = boto3.client('iot')

    # Register certificate for new thing
    resp = cli.register_certificate(certificatePem=crypto.dump_certificate(crypto.FILETYPE_PEM, cert[0]),
                                    setAsActive=True)

    # Attach policy to certificate
    policy_arn = lookup_iot_policy_arn_by_name(IOT_POLICY)
    if policy_arn:
        cli.attach_policy(policyName=IOT_POLICY, target=resp['certificateArn'])
    else:
        logger.warn('Policy %s does not exist, so could not attach policy to certificate', IOT_POLICY)

    cli.create_thing(thingName=thing_name)
    group_arn = lookup_iot_group_arn_by_name(IOT_GROUP)
    if group_arn:
        cli.add_thing_to_thing_group(thingName=thing_name, thingGroupName=IOT_GROUP)
    else:
        logger.warn('Group %s does not exist, so could not add thing to group', IOT_GROUP)

    # Attach certificate to thing
    cli.attach_thing_principal(thingName=thing_name, principal=resp['certificateArn'])

    return cert


def get_iot_endpoint_address():
    cli = boto3.client('iot')
    return cli.describe_endpoint()['endpointAddress']


def list_iot_datasets():
    cli = boto3.client('iotanalytics')
    return [ i['datasetName'] for i in cli.list_datasets()['datasetSummaries'] ]


def get_iot_dataset_contents(dataset):
    cli = boto3.client('iotanalytics')
    resp = cli.get_dataset_content(datasetName=dataset)
    return [i['dataURI'] for i in resp['entries']]


def install(root_ca):
    """This registers a root CA certificate, IOT group, policies, etc.
       This action need only be done once
    """
    certificate_id = register_root_ca(root_ca)
    create_iot_policy()
    create_iot_thing_group()
    create_s3()
    deploy_sam_packages()
    create_iot_pipelines()
    create_iot_rules()
    return certificate_id


def uninstall(certificate_id):
    """Use with extreme caution! This function will delete everything that has been created
    on an AWS account, including all things, certificates, policies and any active data pipelines.
    """
    delete_iot_pipelines()
    delete_iot_rules()
    delete_sam_packages()
    delete_s3()
    # TODO: is this needed?
    #delete_iam_roles()
    delete_iot_things()
    delete_iot_thing_group()
    if certificate_id:
        delete_iot_certificates_by_ca(certificate_id)
        delete_iot_ca_certificate(certificate_id)
    delete_iot_policies()
