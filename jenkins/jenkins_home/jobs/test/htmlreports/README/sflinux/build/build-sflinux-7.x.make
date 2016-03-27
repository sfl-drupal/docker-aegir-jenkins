api = 2
core = 7.x

defaults[projects][l10n_url] = http://ftp.drupal.org/files/translations/l10n_server.xml

; Drupal.org packaging standards
includes[] = ../drupal-org-core.make

; Installation profile
projects[sflinux][type] = profile
projects[sflinux][download][type] = git
projects[sflinux][download][branch] = 7.x
projects[sflinux][download][url] = git@gitlab.savoirfairelinux.com:drupal/sflinux.git
