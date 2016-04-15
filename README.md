# docker-aegir-jenkins

### Prérequis

1. [Docker 1.3+](https://docs.docker.com/installation/ubuntulinux/#upgrade-docker)
2. [Fabric 1.8+](http://www.fabfile.org/)

### Installation

  1. Clone the project
  $git clone https://github.com/sfl-drupal/docker-aegir-jenkins.git

  2. Run the fabric task to setup all.
  $ cd docker-aegir-jenkins/deploy
  $ fab docker_setup           
  
  3. This installation take some time, so be pacient and pay attetion because there are several questions that need to be answered during the installation. How this is a demo to work in the CI, we suggest you the following answers:

    Do you want add to the /etc/hosts the line "172.17.0.3    local.aegir.sfl"? If you say yes you will be able to visit the site using a more frienldy url "http://local.aegir.sfl". [Y/n] [press enter]

    Enter new UNIX password: aegir

    Retype new UNIX password: aegir

    Enter current password for root (enter for none):  [press enter]

    Set root password? [Y/n] [press enter]

    New password: root

    Re-enter new password: root

    Remove anonymous users? [Y/n] [press enter]

    Disallow root login remotely? [Y/n] [press enter]

    Remove test database and access to it? [Y/n] [press enter]

    Reload privilege tables now? [Y/n] [press enter]

    Aegir frontend URL [local.aegir.sfl]: [press enter]

    MySQL privileged user ("root") password: root

    Do you really want to proceed with the install (y/n): y 

    [localhost] local: sudo passwd jenkins

    Entrez le nouveau mot de passe UNIX : jenkins

    Retapez le nouveau mot de passe UNIX : jenkins

    Enter pass phrase for /home/<your user>/.ssh/id_rsa: (The password of your private ssh key)

    Do you want add to the /etc/hosts the line "172.17.0.4    local.jenkins.sfl"? If you say yes you will be able to visit the site using a more frienldy url "http://local.jenkins.sfl". [Y/n] [press enter]

  4. At this point you have already running your Jenkins and Aegir container:

    You should use the url to loggin in aegir and set the password for the admin, you can find it in the terminal,and is similar to:

    http://local.aegir.sfl/user/reset/1/1460750013/pH_hBmYMRhN_G8v9A9Ur_1VDnTLvJ4V2YCsqB5tOkik/login

    To access to jenkins you can use http://local.jenkins.sfl:8080/

  5. You need to activate some modules in aegir, you can use the administration page for it:

    http://local.aegir.sfl/admin/modules

    You have to enable at less "Site migration" and "Site cloning"
    
  6. The jobs in jenkins are already configured and you only need to setup the credentials to connect to the slave localhost: http://local.jenkins.sfl:8080/credential-store/domain/_/newCredentials

    user: jenkins

    password: jenkins

    Then edit the slave to use the good credential: http://local.jenkins.sfl:8080/computer/localhost/configure

  7. Now you should be able to run the jobs of test and deploy.

### Other options

  To see all the possible options
  $fab --list


