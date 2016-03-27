; Drush make for custom modules and theme.
core = 7.x
api = 2

; Modules Contrib SFL
projects[env_conf][type] = module
projects[env_conf][subdir] = "sflcontrib"
projects[env_conf][download][type] = git
projects[env_conf][download][url] = git@gitlab.savoirfairelinux.com:drupal/env-conf.git
projects[env_conf][download][tag] = 7.x-1.1
