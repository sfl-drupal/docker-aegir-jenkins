FROM savoirfairelinux/lampd
MAINTAINER Ernesto Rodriguez Ortiz <ernesto.rodriguezortiz@savoirfairelinux.com>

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# Update software source
RUN apt-get update

# Install dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install sudo php5-cli rsync git-core unzip openjdk-7-jdk

# Copy public ssh key and site migrate scripts
COPY id_rsa.pub /root/.ssh/
COPY . /root

# Setup ssh keys to use fabric
RUN cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/id_rsa*
RUN exec ssh-agent /bin/bash && ssh-add /root/.ssh/id_rsa
