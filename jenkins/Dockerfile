# NOT USED BEACUSE THE LIMITATION WITH THE IMAGE jenkins

#FROM jenkins
#MAINTAINER Ernesto Rodriguez Ortiz <ernesto.rodriguezortiz@savoirfairelinux.com>

# Change to the user root to add the sshkeys
#USER root


# Setup ssh keys to use fabric
#COPY id_rsa.pub /root/.ssh/
#RUN cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
#RUN chmod 600 /root/.ssh/id_rsa*
#RUN exec ssh-agent /bin/bash && ssh-add /root/.ssh/id_rsa
#RUN ssh-keyscan gitlab.savoirfairelinux.com >> /root/.ssh/known_hosts
#RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
# This IP will be change by fabric before the creation of the image
#RUN echo "172.17.1.1   local.aegir.sfl" >> /etc/hosts
#RUN ssh-keyscan local.aegir.sfl >> /root/.ssh/known_hosts


# Drop back to the regular jenkins user - good practice
#USER jenkins
