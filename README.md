# Usage

Assuming that the Dockerfile has been used to create an image `consul_backup` on the `adsabs` Docker Hub account, a backup would be created as follows

	docker run --env-file ./env adsabs/consul_backup
  
where the file with environment variables `env` has entries

    CONSUL_SERVER="foo.bar"
    S3_BACKUP_FOLDER="bucket_name"
    
In the case of restoring an existing backup, we need info to identify the backup file. In this case we would set environment variables like

    ACTION="restore"
    CONSUL_SERVER="foo.bar"
    S3_BACKUP_FOLDER="bucket_name"
    RESTORE_ID="restore_id"
    
where the restore ID is determined by the naming scheme used for creating backup files. So, restoring an existing backup would involve going into the S3 bucket and visually inspect which backup you want restored.

NOTE: apparently, the JSON for an AWS ECS Task Definition also supports a key "environment" where environment variables can be defined that will get set in the container.

An alternative approach to creating backups could perhaps be to add an entry

    0 0 * * * bash -l -c 'python /app/adsws/manage.py consul backup' >> /tmp/cron.log 2>&1

to

    mc/templates/docker/cron/adsws/cronjob.sh

in "Mission Control" and update `manage.py` of `adsws` to support this functionality.
