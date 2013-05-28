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

from __future__ import absolute_import

import os, time
from .CharmHooks import CharmHooks
from .pyutils.pyutils import try_makedirs


class CharmHooks_Storage(CharmHooks):

    PACKAGES = ('glusterfs-client', 'nfs-common')

    def __init__(self, metadata, default_config, default_os_env):
        super(CharmHooks_Storage, self).__init__(metadata, default_config, default_os_env)
        self.local_config = None  # Must be set by derived class

    # ----------------------------------------------------------------------------------------------

    @property
    def storage_config_is_enabled(self):
        c = self.config
        return c.storage_address and c.storage_fstype and c.storage_mountpoint

    @property
    def storage_is_mounted(self):
        return os.path.ismount(self.local_config.storage_path)

    # ----------------------------------------------------------------------------------------------

    def storage_remount(self, address=None, fstype=None, mountpoint=None, options=''):
        if self.storage_config_is_enabled:
            self.info('Override storage parameters with charm configuration')
            address = self.config.storage_address
            nat_address = self.config.storage_nat_address
            fstype = self.config.storage_fstype
            mountpoint = self.config.storage_mountpoint
            options = self.config.storage_options
        elif address and fstype and mountpoint:
            self.info('Use storage parameters from charm storage relation')
            nat_address = ''
        else:
            return
        if nat_address:
            self.info('Update hosts file to map storage internal address %s to %s' %
                      (address, nat_address))
            lines = filter(lambda l: nat_address not in l, open(self.local_config.hosts_file))
            lines += '%s %s\n' % (nat_address, address)
            open(self.local_config.hosts_file, 'w').write(''.join(lines))
        # Avoid unregistering and registering storage if it does not change ...
        if address == self.local_config.storage_address and \
           nat_address == self.local_config.storage_nat_address and \
           fstype == self.local_config.storage_fstype and \
           mountpoint == self.local_config.storage_mountpoint and \
           options == self.local_config.storage_options:
            self.remark('Skip remount already mounted shared storage')
        else:
            self.storage_unregister()
            self.debug("Mount shared storage [%s] %s:%s type %s options '%s' -> %s" % (nat_address,
                       address, mountpoint, fstype, options, self.local_config.storage_path))
            try_makedirs(self.local_config.storage_path)
            # FIXME try X times, a better way to handle failure
            for i in range(self.local_config.storage_mount_max_retry):
                if self.storage_is_mounted:
                    break
                mount_address = '%s:/%s' % (nat_address or address, mountpoint)
                mount_path = self.local_config.storage_path
                if options:
                    self.cmd(['mount', '-t', fstype, '-o', options, mount_address, mount_path])
                else:
                    self.cmd(['mount', '-t', fstype, mount_address, mount_path])
                time.sleep(self.local_config.storage_mount_sleep_delay)
            if self.storage_is_mounted:
                # FIXME update /etc/fstab (?)
                self.local_config.storage_address = address
                self.local_config.storage_nat_address = nat_address
                self.local_config.storage_fstype = fstype
                self.local_config.storage_mountpoint = mountpoint
                self.local_config.storage_options = options
                self.remark('Shared storage successfully registered')
            else:
                raise IOError('Unable to mount shared storage')

    def storage_unregister(self):
        self.info('Unregister shared storage')
        self.local_config.storage_address = ''
        self.local_config.storage_fstype = ''
        self.local_config.storage_mountpoint = ''
        self.local_config.storage_options = ''
        if self.storage_is_mounted:
            # FIXME update /etc/fstab (?)
            self.remark('Unmount shared storage (is mounted)')
            self.cmd(['umount', self.local_config.storage_path])
        else:
            self.remark('Shared storage already unmounted')

    def storage_hook_bypass(self):
        if self.storage_config_is_enabled:
            raise RuntimeError('Shared storage is set in config, storage relation is disabled')

    # ----------------------------------------------------------------------------------------------

    def hook_storage_relation_joined(self):
        self.storage_hook_bypass()

    def hook_storage_relation_changed(self):
        self.storage_hook_bypass()
        address = self.relation_get('private-address')
        fstype = self.relation_get('fstype')
        mountpoint = self.relation_get('mountpoint')
        options = self.relation_get('options')
        self.debug('Storage address is %s, fstype: %s, mountpoint: %s, options: %s' %
                   (address, fstype, mountpoint, options))
        if address and fstype and mountpoint:
            self.hook_stop()
            self.storage_remount(address, fstype, mountpoint, options)
            self.hook_start()
        else:
            self.remark('Waiting for complete setup')

    def hook_storage_relation_broken(self):
        self.storage_hook_bypass()
        self.hook_stop()
        self.storage_remount()
