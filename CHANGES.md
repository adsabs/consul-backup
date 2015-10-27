### 1.0.5

* Connection to S3 via "boto3.resource('s3')" (no keys supplied)

### 1.0.4

* Fixed typo in backup.py

### 1.0.3

* Dockerfile fix (install requirements)

### 1.0.2

* Fix for Github issue 15 (copy utils.py over into Docker image)

### 1.0.1

* Replaced bash (backup/restore) script by Python script
* Implemented unittesting
* Added Travis config file (Travis seemsto prefer Docker containers to be set up through Travis file, rather than in unit test itself)

### 1.0.0

* First release
