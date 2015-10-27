FROM phusion/baseimage

RUN apt-get update
RUN apt-get install -y git python-pip python-dev
RUN pip install --upgrade pip

# Set some environment variables
ENV CONSUL_HOST="consul.adsabs"
ENV S3_BACKUP_FOLDER="adsabs-consul-backups"
# Install Consul client
RUN pip install consulate
# The bash scripts for backup and restore
ADD ./backup.py /scripts/backup.py
ADD ./utils.py /scripts/utils.py
ADD ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt
# Set shell to bash
ENV SHELL /bin/bash
# Execute the script performing the operation (depending on environment variables)
CMD python scripts/backup.py
