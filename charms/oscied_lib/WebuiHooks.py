#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : COMMON LIBRARY
#
#  Authors   : David Fischer
#  Contact   : david.fischer.ch@gmail.com / david.fischer@hesge.ch
#  Project   : OSCIED (OS Cloud Infrastructure for Encoding and Distribution)
#  Copyright : 2012-2013 OSCIED Team. All rights reserved.
#**************************************************************************************************#
#
# This file is part of EBU/UER OSCIED Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this project.
# If not, see <http://www.gnu.org/licenses/>
#
# Retrieved from https://github.com/EBU-TI/OSCIED

import os, shutil, socket, string
from random import choice
from CharmHooks import DEFAULT_OS_ENV
from CharmHooks_Storage import CharmHooks_Storage
from CharmHooks_Website import CharmHooks_Website
from CharmConfig_Storage import MEDIAS_PATH, UPLOADS_PATH
from WebuiConfig import WebuiConfig
from pyutils.pyutils import chown, first_that_exist, rsync, try_makedirs


class WebuiHooks(CharmHooks_Storage, CharmHooks_Website):

    PACKAGES = tuple(set(CharmHooks_Storage.PACKAGES + CharmHooks_Website.PACKAGES +
                    ('mysql-server', 'apache2', 'php5', 'php5-cli', 'php5-curl', 'php5-gd',
                     'php5-mysql', 'libapache2-mod-auth-mysql', 'ntp')))
    FIX_PACKAGES = ('apache2.2-common', 'mysql-client-5.5', 'mysql-client-core-5.5', 'mysql-common',
                    'mysql-server', 'mysql-server-5.1', 'mysql-server-5.5', 'mysql-server-core-5.5')

    def __init__(self, metadata, default_config, local_config_filename, default_os_env):
        super(WebuiHooks, self).__init__(metadata, default_config, default_os_env)
        self.local_config = WebuiConfig.read(local_config_filename, store_filename=True)
        self.debug('My __dict__ is %s' % self.__dict__)

    # ----------------------------------------------------------------------------------------------

    def mysql_do(self, action=None, cli_input=None, fail=True):
        command = ['mysql', '-uroot', '-p%s' % self.config.mysql_root_password]
        if action:
            command.extend(['-e', action])
        return self.cmd(command=command, cli_input=cli_input, fail=fail)

    @staticmethod
    def randpass(length):
        chars = string.letters + string.digits
        return ''.join([choice(chars) for i in range(length)])

    # ----------------------------------------------------------------------------------------------

    @property
    def api_config_is_enabled(self):
        return self.config.api_url

    def api_hook_bypass(self):
        if self.api_config_is_enabled:
            raise RuntimeError('Orchestrator is set in config, api relation is disabled')

    def api_register(self, api_url=None):
        if self.api_config_is_enabled:
            self.info('Override api parameters with charm configuration')
            self.local_config.api_url = self.config.api_url
        elif api_url:
            self.info('Use storage parameters from charm api relation')
            self.local_config.api_url = api_url

    def api_unregister(self):
        self.info('Unregister the Orchestrator')
        self.local_config.api_url = ''

    # ----------------------------------------------------------------------------------------------

    def hook_api_relation_joined(self):
        self.api_hook_bypass()

    def hook_api_relation_changed(self):
        self.api_hook_bypass()
        # Get configuration from the relation
        api_url = self.relation_get('api_url')
        if not api_url:
            self.remark('Waiting for complete setup')
        else:
            self.hook_stop()
            self.api_register(api_url)
            self.hook_config_changed()
            self.hook_start()

    def hook_api_relation_broken(self):
        self.api_hook_bypass()
        self.hook_stop()
        self.api_unregister()
        self.hook_config_changed()

# storage_remount()
# {
#   # ...
#   if storage_is_mounted; then
#     storage_migrate_path 'medias'  "$STORAGE_MEDIAS_PATH"  "$WWW_MEDIAS_PATH"  'root'     755 644
#     storage_migrate_path 'uploads' "$STORAGE_UPLOADS_PATH" "$WWW_UPLOADS_PATH" 'www-data' 755 644
#     # FIXME update /etc/fstab (?)
#     pecho 'Configure Web UI : Register shared storage'
#     # FIXME this is a little bit cheating with paths ;-)
#     storage_uri="$fstype://$ip/$mountpoint"
#     uploads_uri="$storage_uri/uploads/"
#     medias_uri="$storage_uri/medias/"
#     setSettingPHP $GENERAL_CONFIG_FILE 'config' 'uploads_uri' "$uploads_uri" || xecho 'Config' 2
#     setSettingPHP $GENERAL_CONFIG_FILE 'config' 'medias_uri'  "$medias_uri"  || xecho 'Config' 3
#   else
#     xecho 'Unable to mount shared storage' 4
#   fi
# }
# # Migrate a local Web UI path to shared storage only if necessary ----------------------------------
# storage_migrate_path()
# {
#   if [ $# -ne 6 ]; then
#     xecho "Usage: $(basename $0).storage_migrate_path name storage local owner dmod fmod"
#   fi
#   name=$1
#   storage=$2
#   local=$3
#   owner=$4
#   dmod=$5
#   fmod=$6
#   if [ ! -d "$storage" ]; then
#     pecho "Create $name path in storage"
#     mkdir -p "$storage" || xecho "Unable to create $name path" 1
#   else
#     recho "Storage $name path already created"
#   fi
#   if [ -d "$local" ]; then
#     mecho "Migrating files from Web UI $name path to $name path in storage ..."
#     rsync -a "$local/" "$storage/" || xecho "Unable to migrate $name files" 2
#     rm -rf "$local"
#   fi
#   if [ ! -h "$local" ]; then
#     pecho "Link Web UI $name path to $name path in storage"
#     ln -s "$storage" "$local" || xecho "Unable to create $name link" 3
#   fi
#   pecho "Ensure POSIX rights (owner=$owner:$owner mod=(d=$dmod,f=$fmod)) of $name path in storage"
#   chown "$owner:$owner" "$storage" -R || xecho "Unable to chown $storage" 4
#   find "$storage" -type d -exec chmod "$dmod" "$storage" \;
#   find "$storage" -type f -exec chmod "$fmod" "$storage" \;
# }

    # ----------------------------------------------------------------------------------------------

    def hook_install(self):
        self.hook_uninstall()
        self.info('Upgrade system, pre-configure and install prerequisites')
        self.cmd('apt-get -y update', fail=False)
        self.cmd('apt-get -y upgrade')
        try_makedirs('/etc/mysql')
        debconf = 'debconf-set-selections'
        mysql = 'mysql-server mysql-server'
        mysql_root_pass = self.config.mysql_root_password
        # Tip : http://ubuntuforums.org/showthread.php?t=981801
        self.cmd(debconf, input='%s/root_password select %s' % (mysql, mysql_root_pass))
        self.cmd(debconf, input='%s/root_password_again select %s' % (mysql, mysql_root_pass))
        self.cmd('apt-get -y install %s' % ' '.join(WebuiHooks.PACKAGES))
        self.info('Restart network time protocol service')
        self.cmd('service ntp restart')
        self.info('Import Web UI database and create user')
        hostname = socket.gethostname()
        self.cmd('service mysql start', fail=False)
        self.mysql_do("DROP USER ''@'localhost'; DROP USER ''@'%s';" % hostname, fail=False)
        self.mysql_do("GRANT ALL PRIVILEGES ON *.* TO 'root'@'%%' WITH GRANT OPTION;")
        self.mysql_do('DROP DATABASE IF EXISTS webui')
        self.mysql_do(cli_input=open(self.local_config.site_database_file).read())
        self.mysql_do("GRANT ALL ON webui.* TO 'webui'@'%%' IDENTIFIED BY '%s';" %
                      self.config.mysql_user_password)
        self.info('Configure Apache 2')
        self.cmd('a2enmod rewrite')
        self.info('Copy and pre-configure Web UI')
        shutil.copy(self.local_config.site_template_file, self.local_config.sites_enabled_path)
        rsync('www/', self.local_config.www_root_path,
              archive=True, delete=True, exclude_vcs=True, recursive=True)
        try_makedirs(self.local_config.mysql_temp_path)
        chown(self.local_config.mysql_temp_path, 'mysql', 'mysql')
        chown(self.local_config.www_root_path, 'www-data', 'www-data', recursive=True)
        self.local_config.encryption_key = WebuiHooks.randpass(32)
        self.info('Expose Apache 2 service')
        self.open_port(80, 'TCP')

    def hook_config_changed(self):
        self.storage_remount()
        self.api_register()
        infos = self.config.__dict__
        infos.update(self.local_config.__dict__)
        infos['proxy_ips'] = self.proxy_ips_string
        infos['www_medias_uri'] = self.local_config.storage_uri(path=MEDIAS_PATH) or ''
        infos['www_uploads_uri'] = self.local_config.storage_uri(path=UPLOADS_PATH) or ''
        config = self.local_config
        self.template2config(config.general_template_file,  config.general_config_file,  infos)
        self.template2config(config.database_template_file, config.database_config_file, infos)
        self.template2config(config.htaccess_template_file, config.htaccess_config_file, infos)

    def hook_uninstall(self):
        self.info('Uninstall prerequisities, unregister service and load default configuration')
        self.hook_stop()
        self.storage_unregister()
        self.cmd('apt-get -y remove --purge %s' % ' '.join(WebuiHooks.PACKAGES))
        self.cmd('apt-get -y remove --purge %s' % ' '.join(WebuiHooks.FIX_PACKAGES), fail=False)
        self.cmd('apt-get -y autoremove')
        shutil.rmtree('/etc/apache2/',                 ignore_errors=True)
        shutil.rmtree(self.local_config.www_root_path, ignore_errors=True)
        shutil.rmtree('/var/log/apache2/',             ignore_errors=True)
        shutil.rmtree('/etc/mysql/',                   ignore_errors=True)
        shutil.rmtree('/var/lib/mysql/',               ignore_errors=True)
        shutil.rmtree('/var/log/mysql/',               ignore_errors=True)
        os.makedirs(self.local_config.www_root_path)
        self.local_config.reset()

    def hook_start(self):
        if not self.storage_is_mounted:
            self.remark('Do not start web user interface : No shared storage')
        elif not self.local_config.api_url:
            self.remark('Do not start web user interface : No orchestrator api')
        else:
            self.cmd('service mysql start')
            self.cmd('service apache2 start')
            self.remark('Web user interface successfully started')

    def hook_stop(self):
        self.cmd('service apache2 stop', fail=False)
        self.cmd('service mysql stop',   fail=False)

if __name__ == '__main__':
    WebuiHooks(first_that_exist('metadata.yaml',    '../oscied-webui/metadata.yaml'),
               first_that_exist('config.yaml',      '../oscied-webui/config.yaml'),
               first_that_exist('local_config.pkl', '../oscied-webui/local_config.pkl'),
               DEFAULT_OS_ENV).trigger()
