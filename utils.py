import os
import sys
import consulate
import json
import boto3
import base64

PYTHON3 = True if sys.version_info > (3, 0, 0) else False

class UnknownActionRequest(Exception):
    pass

def get_consul_session(host, port):
    return consulate.Consul(host=host, port=port)

def get_records_from_consul(session):
    return session.kv.records()

def consul_restore_from_backup(session, backup):
    handle = open(backup, 'r')
    data = json.load(handle)
    for row in data:
        if isinstance(row, dict):
            # translate raw api export to internal representation
            if row['Value'] is not None:
                row['Value'] = base64.b64decode(row['Value'])
            row = [row['Key'], row['Flags'], row['Value']]
        # Here's an awesome thing to make things work
        # source: https://github.com/gmr/consulate/blob/master/consulate/cli.py#L312
        if not PYTHON3 and isinstance(row[2], unicode):
            row[2] = row[2].encode('utf-8')
        session.kv.set_record(row[0], row[1], row[2])
        
def save_records(records, target):
    handle = open(target, 'w')
    handle.write(json.dumps(records) + '\n')

def get_s3_resource(access_key, secret_key, region):
    return boto3.resource('s3') 

def s3_upload_file(s3_resource, backup_file, backup_bucket):

    s3_object = os.path.basename(backup_file)

    with open(backup_file, 'rb') as f:
        binary = f.read()

    s3_resource.Bucket(backup_bucket).put_object(
        Key=s3_object,
        Body=binary
    )

def s3_download_file(s3_resource, backup_file, backup_bucket):

    s3_object = os.path.basename(backup_file)

    body = s3_resource.Object(backup_bucket, s3_object).get()['Body']
    with open(backup_file, 'wb') as f:
        for chunk in iter(lambda: body.read(1024), b''):
            f.write(chunk)
