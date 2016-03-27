api = 2
core = 8.x

; Drupal.org packaging standards
includes[] = ../drupal-org-core.make

; Installation profile
projects[sflinux][type] = profile
projects[sflinux][download][type] = git
projects[sflinux][download][branch] = 8.x
projects[sflinux][download][url] = git@gitlab.savoirfairelinux.com:drupal/sflinux.git
