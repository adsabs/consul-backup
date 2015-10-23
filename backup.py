import os
import sys
import logging
import datetime
import json
from utils import get_consul_session
from utils import get_records_from_consul
from utils import save_records
from utils import get_s3_resource
from utils import s3_upload_file
from utils import s3_download_file

# Configure logging
LOG_FILENAME = '/tmp/consul_backup.log'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.INFO,
                    )
# First check if we have the proper credentials for uploading
# backups to S3
aws_access_key = os.environ.get('AWS_ACCESS_KEY')
aws_secret_key = os.environ.get('AWS_SECRET_KEY')
aws_region     = os.environ.get('AWS_REGION','us-east-1')
# Both keys much exist
if not aws_access_key and not aws_secret_key:
    logging.error("No AWS credentials were specified. Cannot do backup! Exiting...")
    sys.exit(2)
# Check if the name of the backup folder on S3 was specified,
# otherwise exit
backup_folder = os.environ.get('S3_BACKUP_FOLDER')
# and let's make sure that it has a value
if not backup_folder:
    logging.error("No S3 backup folder was specified! Exiting...")
    sys.exit(2)
# Check whether necessary environment variables have been set to a non-empty value
# If not, fall back to default values
consul_host = os.environ.get('CONSUL_HOST')
if not consul_host:
    consul_host = 'localhost'
consul_port = os.environ.get('CONSUL_PORT')
if not consul_port:
    consul_host = '8500'
# Directory to locally store backup file (temporarily)
tmp_dir = os.environ.get('TMP_DIR','/tmp')
# If no action was specified, the default action is backup
action = os.environ.get('ACTION')
if not action:
    action = 'backup'
# If we need to restore, we need to be able to identify the backup file to be restored
# and if this has not been set, we need to exit
if action == 'restore':
    restore_id = os.environ.get('RESTORE_ID')
    if not restore_id:
        logging.error('Restore was requested, but no RESTORE_ID was set!')
        sys.exit(2)
# Register the Consul client with the server
logging.info("Registering consulate with %s on port %s"%(consul_host, consul_port))
try:
    session = get_consul_session(consul_host, consul_port)
except Exception,e:
    logging.error("Failed to register consulate: %s"%e)
    sys.exit(2)
# Request status info to check that we established a connection
try:
    leader = session.status.leader()
except Exception, e:
    logging.error("Failed to register consulate: %s"%e)
    sys.exit(2)
# Now take the appropriate action depending on the value of the ACTION variable
if action == 'backup':
    # Get today's date for the time stamp
    now = str(datetime.datetime.now().date())
    # Construct the name of the backup file
    backup_file = '%s/adsabs_consul_kv.%s.json' % (tmp_dir,now)
    # Get the records from the Consul key/value store
    try:
        records = get_records_from_consul(session)
    except Exception, e:
        logging.error('Unable to retrieve records from Consul store: %s'%e)
        sys.exit(2)
    # Write the records to the backup file
    try:
        save_records(records, backup_file)
    except Exception, e:
        logging.error('Unable to write to backup file: %s (%s)'%(backup_file,e))    
        sys.exit(2)
    logging.info('Backup was written to: %s'%backup_file)     
    # Now copy the backup to S3
    s3 = get_s3_resource(aws_access_key,aws_secret_key,aws_region)
    try:
        s3_upload_file(s3, backup_file, backup_folder)
    except Exception, e:
        logging.error('Unable to move backup to S3: %s'%e)
    # Finally, remove the local copy
    logging.info('Removing local copy of backup file: %s' % backup_file)
    os.remove(backup_file)
elif action == 'restore':
    # Construct the name of the backup file to retrieve
    backup_file = '%s/adsabs_consul_kv.%s.json' % (tmp_dir,restore_id)
    # Get the file from S3
    s3 = get_s3_resource(aws_access_key,aws_secret_key,aws_region)
    try:
        s3_download_file(s3, backup_file, backup_folder)
    except Exception, e:
        logging.error('Unable to get backup file %s from S3: %s'%(backup_file,e))
        sys.exit(2)
    # Now do the restore
    try:
        consul_restore_from_backup(session, backup_file)
    except Exception, e:
        logging.error('Failed restoring Consul key/value store: %s'%e)
        sys.exit(2)
else:
    logging.error('Unknown action: "%s"'%action)
    sys.exit(2)
