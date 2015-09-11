#********************************
# WARNING WARNING WARNING
#********************************

# YOU MUST NOT MODIFY THIS FILE!

# If you need to override the values of the variables defined in this file you should
# Copy and paste this file with the name local_vars.py and set your values there.

# When you create a file local_vars.py and define the values there, the fabfile.py file will use
# your values and not the values defined in this file.


#********************************
# END WARNING
#********************************

from os import path

# Variables to use at your local machine
LOCAL_WORKSPACE = path.join(path.dirname(__file__), path.pardir)

#=================#
# The Apache user #
#=================#
APACHE = 'www-data'

#=================#
# Aegir variables #
#=================#
AEGIR = 'aegir'
AEGIR_HOSTNAME = 'local.aegir.sfl'
AEGIR_PROJECT_NAME = 'aegir'
AEGIR_PROJECT_TYPE = 'drupal'
#AEGIR_HOME_WORKSPACE = '{}/aegir/aegir_home'.format(LOCAL_WORKSPACE)
AEGIR_DOCKER_WORKSPACE = "/var/aegir"
AEGIR_DOCKER_PORT_TO_BIND = '8431:80'
AEGIR_ROOT_PASS = ''
AEGIR_DB_USER = 'dev'
AEGIR_DB_PASS = 'dev'
AEGIR_DB_HOST = 'localhost'


#===================#
# Genkins variables #
#===================#
JENKINS = 'jenkins'
JENKINS_HOSTNAME = 'local.jenkins.sfl'
JENKINS_PROJECT_NAME = 'jenkins'
JENKINS_HOME_WORKSPACE = '{}/jenkins/jenkins_home'.format(LOCAL_WORKSPACE)
JENKINS_DOCKER_WORKSPACE = '/var/jenkins_home'
JENKINS_DOCKER_PORT_TO_BIND = '5000:5000'
JENKINS_DB_USER = 'dev'
JENKINS_DB_PASS = 'dev'
JENKINS_DB_NAME = 'db_test'
JENKINS_AEGIRSRV = 'localhost'
JENKINS_AEGIRUSER = AEGIR
JENKINS_AEGIRPATH = AEGIR_DOCKER_WORKSPACE