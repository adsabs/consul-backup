# Usage

Assuming that the Dockerfile has been used to create an image `consul_backup` on the `adsabs` Docker Hub account, a backup would be created as follows

	docker run --env-file ./env adsabs/consul_backup
  
where the file with environment variables `env` has entries

    CONSUL_HOST="foo.bar"
    S3_BACKUP_FOLDER="bucket_name"
    
In the case of restoring an existing backup, we need info to identify the backup file. In this case we would set environment variables like

    ACTION="restore"
    CONSUL_HOST="foo.bar"
    S3_BACKUP_FOLDER="bucket_name"
    RESTORE_ID="restore_id"
    
where the restore ID is determined by the naming scheme used for creating backup files. So, restoring an existing backup would involve going into the S3 bucket and visually inspect which backup you want restored.

The Task Definition for the backup of the Consul key/value store would then be

	{
	  "containerDefinitions": [
	    {
	      "name": "consul-backup",
	      "image": "adsabs/consul-backup",
	      "cpu": 384,
	      "memory": 384,
	      "essential": true,
	      "environment": []
	    }
	  ],
	  "family": "consul-backup"
	}

and for restoring a backup with identifier `restore_ID` the Task Definition would be

	{
	  "containerDefinitions": [
	    {
	      "name": "consul-backup",
	      "image": "adsabs/consul-backup",
	      "cpu": 384,
	      "memory": 384,
	      "essential": true,
	      "environment": [
			{ "name": "ACTION", "value": "restore" },
			{ "name": "RESTORE_ID", "value": "restore_ID" },
	      ]
	    }
	  ],
	  "family": "consul-backup"
	}
