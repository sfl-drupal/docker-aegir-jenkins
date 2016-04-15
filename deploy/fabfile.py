# coding: utf-8
#
# Copyright (C) 2014 Savoir-faire Linux Inc. (<www.savoirfairelinux.com>).
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import unicode_literals
from getpass import getuser
import pwd
from fabric.api import lcd, cd, task, roles, env, local, run, runs_once, execute
from fabric.colors import red, green
from fabric.contrib.files import exists
from fabric.contrib.console import confirm

# Import socket to find the localhost IP address
import socket

# Import default variables
from default_vars import *

# Import local variables' overrides, if they exist
if path.exists(path.join(path.dirname(__file__), 'local_vars.py')):
    from local_vars import *


# Function to manage differents users, hosts, roles, and variables  #
#####################################################################
# Get info of the current user and host
user_name = getuser()
host_name = local("hostname", capture=True)

# Set the env dict with the roles and the hosts
env.roledefs['local'] = ["{}@{}".format(user_name, host_name)]
env.roledefs['docker'] = ["root@{}".format(AEGIR_HOSTNAME)]
env.roledefs['dk_aegir'] = ["aegir@{}".format(AEGIR_HOSTNAME)]
env.roledefs['jenkins'] = ["jenkins@{}".format(host_name)]


def set_env(role):
    """
    Helper function to set the correct values of the global variables in function of the role
    :param role: the role to use for define the host
    :return:
    """
    global WORKSPACE
    WORKSPACE = {
        'local': LOCAL_WORKSPACE,
        'docker': AEGIR_DOCKER_WORKSPACE,
        'dk_aegir': AEGIR_DOCKER_WORKSPACE,
    }[role]


def fab_run(role="local", cmd="", capture=False):
    """
    Helper function to run the task locally or remotely
    :param role: the role to use for define the host
    :param cmd: the command to execute
    :param capture: if it should return or not the output of the command
    :return: the function to execute the command locally or remotely
    """
    if role == "local":
        return local(cmd, capture)
    else:
        return run(cmd)


def fab_cd(role, directory):
    """
    Helper function to manage the context locally or remotely
    :param role: the role to use for define the host
    :param directory: the directory of context
    :return: the function to manage the context locally or remotely
    """
    if role == "local":
        return lcd(directory)
    else:
        return cd(directory)


def fab_exists(role, directory):
    """
    Herlper function to check if a directory exist locally or remotely
    :param role: the role to use for define the host.
    :param directory: the directory to check
    :return: the function for check the existence of the directory locally or remotely
    """
    if role == "local":
        return path.exists(directory)
    else:
        return exists(directory)


def fab_add_to_hosts(ip, site_hostname):
    """
    Helper function to add the ip and hostname to /etc/hosts
    :param ip:
    :param site_hostname:
    :return:
    """
    if confirm(green('Do you want add to the /etc/hosts the line "{}    {}"? '
                     'If you say yes you will be able to visit the site using a more frienldy url '
                     '"http://{}".'.format(ip, site_hostname, site_hostname))):
        # Add if not find the comment "# Docker auto-added host" to the file /etc/hosts
        local(
            'grep "# Docker auto-added host" /etc/hosts > /dev/null || '
            'sudo sed -i "$ a # Docker auto-added host" /etc/hosts')

        # Add the ip address and hostname after the comment "# Docker auto-added host"
        local('sudo sed -i "/# Docker auto-added host/i\{}     {}" /etc/hosts'.format(ip, site_hostname))


def fab_remove_from_hosts(site_hostname):
    """
    Helper function to remove the ip  and the hostname to /etc/hosts
    :param site_hostname:
    :return:
    """
    print(green('Enter your password to remove the {} from your /etc/hosts file'.format(site_hostname)))
    local('sudo sed -i "/{}/d" /etc/hosts'.format(site_hostname))


def fab_update_hosts(ip, site_hostname):
    """
    Helper function to update the file /etc/hosts
    :param ip:
    :param site_hostname:
    :return:
    """
    fab_remove_from_hosts(site_hostname)
    fab_add_to_hosts(ip, site_hostname)


# Helper functions to manage docker images and containers #
###########################################################

def docker_ps(running_only=False):
    args = '' if running_only else '-a'
    result = local('docker ps {}'.format(args), capture=True)
    lines = result.stdout.splitlines()
    # container name is supposed to be the last column
    assert lines[0].strip().endswith('NAMES')
    return [line.strip().split(' ')[-1] for line in lines[1:]]


def docker_tryrun(imgname, containername=None, opts='', mounts=None, cmd='', restart=True):
    # mounts is a list of (from, to, canwrite) path tuples. ``from`` is relative to the project root.
    # Returns True if the container was effectively ran (false if it was restarted or aborted)
    if not mounts:
        mounts = []
    if containername and containername in docker_ps(running_only=True):
        print green("{} already running".format(containername))
        return False
    if containername and containername in docker_ps(running_only=False):
        if restart:
            print green("{} already exists and is stopped. Restarting!".format(containername))
            local('docker restart {}'.format(containername))
            return True
        else:
            print red("There's a dangling container {}! That's not supposed to happen. Aborting".format(containername))
            print "Run 'docker rm {}' to remove that container".format(containername)
            return False
    for from_path, to_path, canwrite in mounts:
        abspath = from_path
        opt = ' -v {}:{}'.format(abspath, to_path)
        if not canwrite:
            opt += ':ro'
        opts += opt
    if containername:
        containername_opt = '-h {} --name {}'.format(containername, containername)
    else:
        containername_opt = ''
    local('docker run {} {} {} {}'.format(opts, containername_opt, imgname, cmd))
    return True


def docker_ensureruns(containername):
    # Makes sure that containername runs. If it doesn't, try restarting it. If the container
    # doesn't exist, spew an error.
    if containername not in docker_ps(running_only=True):
        if containername in docker_ps(running_only=False):
            local('docker restart {}'.format(containername))
            return True
        else:
            return False
    else:
        return True


def docker_ensure_data_container(containername, volume_paths=None, base_image='busybox'):
    # Make sure that we have our data containers running. Data containers are *never* removed.
    # Their only purpose is to hold volume data.
    # Returns whether a container was created by this call
    if containername not in docker_ps(running_only=False):
        if volume_paths:
            volume_args = ' '.join('-v %s' % volpath for volpath in volume_paths)
        else:
            volume_args = ''
        local('docker create %s --name %s %s' % (volume_args, containername, base_image))
        return True
    return False


def docker_isrunning(containername):
    # Check if the containername is running.
    if containername not in docker_ps(running_only=True):
        return False
    else:
        return True


def docker_images():
    result = local('docker images', capture=True)
    lines = result.stdout.splitlines()
    # image name is supposed to be the first column
    assert lines[0].strip().startswith('REPOSITORY')
    return [line.strip().split(' ')[0] for line in lines]


# Task to manage docker's images and containers generally in the localhost#
###########################################################################

@task
@roles('local')
def docker_create_aegir_image(role='local'):
    """
    Create docker aegir image.
    """
    set_env(role)
    with fab_cd(role, '{}/aegir'.format(WORKSPACE)):
        # Set the key avialable for the container
        manage_needed_files('local', 'aegir', True)
        if '{}/{}'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE) in docker_images():
            print(red('Docker image {}/{} was found, you has already build this image'.format(AEGIR_PROJECT_NAME,
                                                                                              AEGIR_PROJECT_TYPE)))
        else:
            fab_run(role, 'docker build -t {}/{} .'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE))
            print(green('Docker image {}/{} was build successful'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE)))
        manage_needed_files('local', 'aegir', False)


@task
@roles('local')
def docker_run_aegir_container(role='local'):
    """
    Run docker aegir container.
    """
    set_env(role)
    with fab_cd(role, '{}/aegir'.format(WORKSPACE)):
        #fab_run(role, 'sudo chmod -R 777 {}'.format(AEGIR_HOME_WORKSPACE))
        if '{}/{}'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE) in docker_images():
            if docker_tryrun('{}/{}'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE),
                             '{}_container'.format(AEGIR_PROJECT_NAME),
                             '-d -p {}'.format(AEGIR_DOCKER_PORT_TO_BIND) ):
                             # ,mounts=[(AEGIR_HOME_WORKSPACE, AEGIR_DOCKER_WORKSPACE, True)]):
                # If container was successful build, get the IP address and show it to the user.
                ip = fab_run(role, 'docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" '
                                   '{}_container'.format(AEGIR_PROJECT_NAME), capture=True)
                fab_update_hosts(ip, AEGIR_HOSTNAME)
                print(green('Docker container {}_container was build successful. '
                            'To visit the Website open a web browser in http://{} or http://localhost:{}.'
                            ''.format(AEGIR_PROJECT_NAME, AEGIR_HOSTNAME, AEGIR_DOCKER_PORT_TO_BIND)))

        else:
            print(red('Docker image {}/{} not found and is a requirement to run the {}_container.'
                      'Please, run first "fab create" in order to build the {}/{} '
                      'image'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE, AEGIR_PROJECT_NAME, AEGIR_PROJECT_NAME,
                                     AEGIR_PROJECT_TYPE)))


@task
@roles('local')
def docker_stop_aegir_container(role='local'):
    """
    Stop docker aegir container.
    """
    set_env(role)
    with fab_cd(role, '{}/aegir'.format(WORKSPACE)):
        if '{}_container'.format(AEGIR_PROJECT_NAME) in docker_ps():
            fab_remove_from_hosts(AEGIR_HOSTNAME)
            fab_run(role, 'docker stop {}_container'.format(AEGIR_PROJECT_NAME))
            print(green('Docker container {}_container was successful stopped'.format(AEGIR_PROJECT_NAME)))
        else:
            print(red('Docker container {}_container was not running or paused'.format(AEGIR_PROJECT_NAME)))


@task
@roles('local')
def docker_remove_aegir_container(role='local'):
    """
    Remove docker aegir container.
    """
    set_env(role)
    with fab_cd(role, '{}/aegir'.format(WORKSPACE)):
        if '{}_container'.format(AEGIR_PROJECT_NAME) in docker_ps():
            fab_remove_from_hosts(AEGIR_HOSTNAME)
            fab_run(role, 'docker rm -f {}_container'.format(AEGIR_PROJECT_NAME))
            print(green('Docker container {}_container was successful removed'.format(AEGIR_PROJECT_NAME)))
        else:
            print(red('Docker container {}_container was already removed'.format(AEGIR_PROJECT_NAME)))


@task
@roles('local')
def docker_remove_aegir_image(role='local'):
    """
    Remove docker aegir image.
    """
    set_env(role)
    with fab_cd(role, '{}/aegir'.format(WORKSPACE)):
        if docker_isrunning('{}_container'.format(AEGIR_PROJECT_NAME)):
            print(red('Docker container {}_container is running, '
                      'you should stopped it after remove the image {}/{}'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_NAME,
                                                                                  AEGIR_PROJECT_TYPE)))
        if '{}/{}'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE) in docker_images():
            fab_run(role, 'docker rmi -f {}/{}'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE))
            # Remove dangling docker images to free space.
            if '<none>' in docker_images():
                fab_run(role, 'docker images --filter="dangling=true" -q | xargs docker rmi -f')
            print(green('Docker image {}/{} was successful removed'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE)))
        else:
            print(red('Docker image {}/{} was not found'.format(AEGIR_PROJECT_NAME, AEGIR_PROJECT_TYPE)))


@task
@roles('local')
def docker_connect_aegir_container(role='local'):
    """
    Connect to docker aegir container using "docker -it exec <name> bash".
    """
    set_env(role)
    with fab_cd(role, '{}/aegir'.format(WORKSPACE)):
        if docker_isrunning('{}_container'.format(AEGIR_PROJECT_NAME)):
            fab_run(role, 'docker exec -it {}_container bash'.format(AEGIR_PROJECT_NAME))
        else:
            print(red('Docker container {}_container is not running, it should be running to be able to connect.'))


@task
@roles('local')
def docker_ssh_aegir_container(role='local', path_key='~/.ssh/id_rsa'):
    """
    Connect to docker aegir container through ssh protocol using you private key that should be in '~/.ssh/id_rsa'.
    """
    set_env(role)
    ip = fab_run(role, 'docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" {}_container'.format(AEGIR_PROJECT_NAME),
                 capture=True)
    if ip:
        fab_run(role, 'ssh -i {} root@{}'.format(path_key, ip))


@task
@roles('docker')
def docker_update_host_aegir_container():
    """
    Helper function to update the ip and hostname in docker container.
    """
    # Get the ip of the container, this
    ip = local('docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" {}_container'.format(AEGIR_PROJECT_NAME),
               capture=True)
    run("sed  '/{}/c\{} {} {}_container localhost localhost.domainlocal' "
        "/etc/hosts > /root/hosts.backup".format(ip, ip, AEGIR_HOSTNAME, AEGIR_PROJECT_NAME))
    run("cat /root/hosts.backup > /etc/hosts")


@task
@roles('local')
def docker_run_jenkins_container(role='local'):
    """
    Run docker jenkins container. The same that run: $ fab cjrun
    """
    set_env(role)
    # Change permision in jenkins_home dir and run the container using the official image
    fab_run(role, 'sudo chmod -R 777 {}'.format(JENKINS_HOME_WORKSPACE))
    fab_run(role, 'docker run -d -p {} -v {}:{} -h {} --name {}_container '
                  'jenkins'.format(JENKINS_DOCKER_PORT_TO_BIND, JENKINS_HOME_WORKSPACE, JENKINS_DOCKER_WORKSPACE,
                                   JENKINS_HOSTNAME, JENKINS_PROJECT_NAME))


@task
@roles('local')
def docker_stop_jenkins_container(role='local'):
    """
    Stop docker jenkins container.
    """
    set_env(role)
    # Create aegir dir and Setup ssh keys to use fabric
    if docker_isrunning('{}_container'.format(JENKINS_PROJECT_NAME)):
        fab_run(role, 'docker stop jenkins_container')


@task
@roles('local')
def docker_remove_jenkins_container(role='local'):
    """
    Remove docker jenkins container, always stop docker jenkins container first.
    """
    set_env(role)
    if docker_isrunning('{}_container'.format(JENKINS_PROJECT_NAME)):
        docker_stop_jenkins_container()
    # Create aegir dir and Setup ssh keys to use fabric
    fab_run(role, 'docker rm {}_container'.format(JENKINS_PROJECT_NAME))


@task
@roles('local')
def docker_connect_jenkins_container(role='local'):
    """
    Connect to docker jenkins container using "docker -it exec <name> bash".
    """
    set_env(role)
    with fab_cd(role, '{}/aegir'.format(WORKSPACE)):
        if docker_isrunning('{}_container'.format(JENKINS_PROJECT_NAME)):
            fab_run(role, 'docker exec -it {}_container bash'.format(JENKINS_PROJECT_NAME))
        else:
            print(red('Docker container {}_container is not running, it should be running to be able to connect.'))


@task
@roles('local')
def copy_ssh_keys(role='local', ):
    """
    Copy your ssh keys to use it to clone git projects and to connect to containers using ssh protocol.
    """
    set_env(role)
    fab_run(role, 'sudo chown {}:{} -R {}'.format(user_name, user_name, WORKSPACE))
    copy = True
    if fab_exists(role, '{}/deploy/id_rsa.pub'.format(WORKSPACE)):
        if confirm(red('There is a SSH public key in your deploy directory Say [Y] to keep this key, say [n] to '
                       'overwrite the key')):
            copy = False

    with fab_cd(role, WORKSPACE):
        if copy:
            fab_run(role, 'cp ~/.ssh/id_rsa* deploy/')
            print(green('SSH public key copied successful'))
        else:
            print(red('Keeping public the existing SSH key'))


@task
@roles('local')
def manage_needed_files(role='local', project='aegir', action=True):
    """
    Handle your ssh keys to use it in the docker aegir container to clone git projects and to connect to it using ssh.
    """
    set_env(role)
    with fab_cd(role, WORKSPACE):
        if action:
            fab_run(role, 'cp deploy/id_rsa.pub {}'.format(project))
            fab_run(role, 'cp deploy/migrate-sites {}'.format(project))
            fab_run(role, 'cp deploy/remove-platforms {}'.format(project))
        else:
            fab_run(role, 'rm {}/id_rsa.pub'.format(project))
            fab_run(role, 'rm {}/migrate-sites'.format(project))
            fab_run(role, 'rm {}/remove-platforms'.format(project))


@task
@roles('docker')
def create_aegir_user(role='docker'):
    """
    Create the Aegir user dans docker aegir container.
    """
    set_env(role)
    # Create aegir dir and Setup ssh keys to use fabric
    fab_run(role, 'adduser --system --group --home /var/aegir --shell /bin/bash aegir')
    fab_run(role, 'passwd aegir')
    fab_run(role, 'adduser aegir www-data')
    if not fab_exists(role, '/var/aegir/.ssh'):
        fab_run(role, 'mkdir /var/aegir/.ssh')
    fab_run(role, 'cp /root/.ssh/* /var/aegir/.ssh')
    fab_run(role, 'cp /root/migrate-sites /var/aegir/')
    fab_run(role, 'cp /root/remove-platforms /var/aegir/')
    fab_run(role, 'cat /var/aegir/.ssh/id_rsa.pub >> /var/aegir/.ssh/authorized_keys')
    fab_run(role, 'chown -R aegir:aegir /var/aegir')
    fab_run(role, 'a2enmod rewrite')


@task
@roles('docker')
def webserver_config(role='docker'):
    """
    Webserver configuration dans docker aegir container.
    """
    set_env(role)
    fab_run(role, 'ln -s /var/aegir/config/apache.conf /etc/apache2/conf-available/aegir.conf')


@task
@roles('docker')
def php_config(role='docker'):
    """
    PHP configuration dans docker aegir container.
    """
    set_env(role)
    fab_run(role, 'sudo sed -i "s@memory_limit = 128M@memory_limit = 512M@g" /etc/php5/cli/php.ini')
    fab_run(role, 'sudo sed -i "s@memory_limit = 128M@memory_limit = 512M@g" /etc/php5/apache2/php.ini')


@task
@roles('docker')
def sudo_config(role='docker'):
    """
    Sudo configuration dans docker aegir container.
    """
    set_env(role)
    fab_run(role, 'touch /etc/sudoers.d/aegir')
    fab_run(role, 'echo "Defaults:aegir  !requiretty" > /etc/sudoers.d/aegir')
    fab_run(role, 'echo "aegir ALL=NOPASSWD: /usr/sbin/apache2ctl" > /etc/sudoers.d/aegir')


@task
@roles('docker')
def database_config(role='docker'):
    """
    Database configuration dans docker aegir container.
    """
    set_env(role)
    fab_run(role, 'mysql -uroot -e "GRANT ALL PRIVILEGES ON *.* TO \'{}\'@\'%\' '
                  'IDENTIFIED BY \'{}\'; FLUSH PRIVILEGES;"'.format(AEGIR_DB_USER, AEGIR_DB_PASS))
    fab_run(role, 'mysql_secure_installation')


@task
@roles('dk_aegir')
def install_aegir_components(role='dk_aegir'):
    """
    Install Aegir components dans docker aegir container.
    """
    set_env(role)
    with fab_cd(role, AEGIR_DOCKER_WORKSPACE):
        fab_run(role, 'drush dl provision-7.x')
        fab_run(role, 'drush cc drush')
        fab_run(role, 'drush hostmaster-install')


@task
@roles('docker')
def enable_aegir_conf(role='docker'):
    """
    Enable Aegir configuration dans docker aegir container.
    """
    set_env(role)
    fab_run(role, 'a2enconf aegir')
    fab_run(role, 'service apache2 reload')
    fab_run(role, 'ln -s /var/aegir /opt/aegir')


@task
@roles('local')
def create_jenkins_user(role='local'):
    """
    Create the Jenkins user in you localhost to use it like an slave.
    """
    set_env(role)

    try:
        pwd.getpwnam('jenkins')
    except KeyError:
        fab_run(role, 'sudo adduser --system --group --shell /bin/bash jenkins')
        fab_run(role, 'sudo passwd jenkins')
        fab_run(role, 'sudo adduser jenkins www-data')
        fab_run(role, 'sudo adduser jenkins docker')
        # WARNING THIS MODIFY YOU PERSONNAL .ssh/ files.
        fab_run(role, 'cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys')
        fab_run(role, 'ssh-keyscan gitlab.savoirfairelinux.com >> ~/.ssh/known_hosts')
        fab_run(role, 'ssh-keyscan github.com >> ~/.ssh/known_hosts')
        fab_run(role, 'ssh-keyscan local.aegir.sfl >> ~/.ssh/known_hosts')
        fab_run(role, 'ssh-keyscan localhost >> ~/.ssh/known_hosts')
        # The files are reused by the Jenkins user.
        fab_run(role, 'sudo cp -r ~/.ssh /home/jenkins/')
        fab_run(role, 'sudo openssl rsa -in ~/.ssh/id_rsa -out /home/jenkins/.ssh/id_rsa')
        fab_run(role, 'sudo mkdir /home/jenkins/workspace')
        fab_run(role, 'sudo chown -R jenkins:jenkins /home/jenkins')


@task
@roles('local')
def remove_jenkins_user(role='local'):
    """
    Remove the Jenkins user from you localhost to use it like an slave.
    """
    set_env(role)

    fab_run(role, 'sudo userdel jenkins')
    fab_run(role, 'sudo rm -rf /home/jenkins')

@task
@roles('local')
def add_jenkins_host(role='local'):
    """
    Add the IP and hostname of the Jenkins container to your /etc/hosts, so you can use the hostname to visit the site.
    """
    ip = fab_run(role, 'docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" jenkins_container'
                       ''.format(AEGIR_PROJECT_NAME), capture=True)
    fab_update_hosts(ip, JENKINS_HOSTNAME)
    print(green('Now you can visit your the site at http://{}:8080'.format(JENKINS_HOSTNAME)))


@task(alias='ds')
@runs_once
def docker_setup():
    """
    Complete docker setup process, used generally when building the docker image for install and configure Aegir.
    The same that run: $ fab ds
    """
    # General task
    execute(copy_ssh_keys)

    # Aegir tasks
    execute(docker_create_aegir_image)
    execute(docker_run_aegir_container)
    execute(docker_update_host_aegir_container)
    execute(create_aegir_user)
    execute(webserver_config)
    execute(php_config)
    execute(sudo_config)
    execute(database_config)
    execute(install_aegir_components)
    execute(enable_aegir_conf)

    # Jenkins task
    execute(create_jenkins_user)
    execute(docker_run_jenkins_container)
    execute(add_jenkins_host)
    print green('Docker setup finished with success!')


@task(alias='dcc')
@runs_once
def docker_clean_all():
    """
    Complete docker REMOVE process, used generally to remove all containers and images. The same that run: $ fab dcc
    """
    execute(docker_stop_jenkins_container)
    execute(docker_stop_aegir_container)
    execute(docker_remove_jenkins_container)
    execute(docker_remove_aegir_container)
    execute(docker_remove_aegir_image)
    execute(remove_jenkins_user)

    print green('Docker clean all finished with success!')


@task(alias='dkstop')
@runs_once
def docker_stop_all():
    """
    Complete docker STOP process, used generally to stop all containers. The same that run: $ fab dkstop
    """
    execute(docker_stop_jenkins_container)
    execute(docker_stop_aegir_container)

    print green('Docker clean all finished with success!')


@task(alias='dkstart')
@runs_once
def docker_start_all():
    """
    Complete docker STOP process, used generally to stop all containers. The same that run: $ fab dkstart
    """
    execute(docker_run_aegir_container)
    fab_run('local', 'docker start {}_container'.format(JENKINS_PROJECT_NAME))
    execute(add_jenkins_host)

    print green('Docker clean all finished with success!')
