# Usage

Assuming that the Dockerfile has been used to create an image `consul_backup` on the `adsabs` Docker Hub account, a backup would be created as follows

	docker run adsabs/consul_backup
  
In the case of restoring an existing backup, we need info to identify the backup file. In this case we would set environment variables like

    ACTION="restore"
    RESTORE_ID="restore_id"
    
where the restore ID is determined by the naming scheme used for creating backup files.
Assuming these variables are set in a file `env`, you would execute

    docker run --env-file ./env adsabs/consul_backup

So, restoring an existing backup would involve going into the S3 bucket and visually inspect which backup you want restored.

In terms of executing the backup in an ECS container, we define both actions in terms of Task Definitions. The Task Definition for the backup of the Consul key/value store would then be

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

and using Mission Control, assuming the Task Definition is stored in the variable `task_def`, we would do

    python mc/manage.py register_task_def --task "$task_def"

followed by

    python mc/manage.py update_service --cluster staging --service consul-backup --desiredCount 1 --taskDefinition consul-backup

to execute the task.
