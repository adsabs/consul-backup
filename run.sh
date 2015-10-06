#!/bin/bash
# First, check if the name of the backup folder on S3 was specified, otherwise exit
if [[ -z "$S3_BACKUP_FOLDER" ]] ; then
    echo "No S3 destination was specified. Exiting...";
    exit 1;
fi
# Check whether necessary environment variables have been set to a non-empty value
# If not, fall back to default values
if [[ -z "$CONSUL_HOST" ]] ; then
    CONSUL_HOST="localhost"
fi

if [[ -z "$CONSUL_PORT" ]] ; then
    CONSUL_PORT=8500
fi

if [[ -z "$ACTION" ]] ; then
    ACTION="backup"
fi
# If we need to restore, we need to be able to identify the backup file to be restored
# and if this has not been set, we need to exit
if [ $ACTION = "restore" ]; then
    if [[ -z "$RESTORE_ID" ]] ; then
        echo "Restore was requested, but no RESTORE_ID was set!";
        exit 1;
    fi
fi
# Register the Consul client with the server
echo "Registering consulate with $CONSUL_HOST on port $CONSUL_PORT"
consulate register -a $CONSUL_HOST -p $CONSUL_PORT consul_client no-check
# Now take the appropriate action depending on the value of the ACTION variable
if [ $ACTION = "backup" ]; then
    # Get today's date for time stamp
    now="$(date +'%d%m%Y')"
    # Do backup
    backup_file="adsabs_consul_kv.$now.json"
    echo "Making backup of Consul key/value store from $CONSUL_HOST"
    echo "Backup is written to: $backup_file"
    consulate kv backup > $backup_file
    # Move backup to S3
    /usr/bin/aws s3 mv $backup_file s3://$S3_BACKUP_FOLDER
else
    # Get file with backup from S3
    backup_file="adsabs_consul_kv.$RESTORE_ID.json"
    /usr/bin/aws s3 cp s3://$S3_BACKUP_FOLDER/$backup_file ./$backup_file
    # Do restore
    echo "Restoring backup from: $backup_file"
    consulate kv restore < $backup_file
fi
