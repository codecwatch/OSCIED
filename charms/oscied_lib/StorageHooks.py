#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : COMMON LIBRARY
#
#  Authors   : David Fischer
#  Contact   : david.fischer.ch@gmail.com
#  Project   : OSCIED (OS Cloud Infrastructure for Encoding and Distribution)
#  Copyright : 2012-2013 OSCIED Team. All rights reserved.
#**********************************************************************************************************************#
#
# This file is part of EBU/UER OSCIED Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this project.
# If not, see <http://www.gnu.org/licenses/>
#
# Retrieved from https://github.com/ebu/OSCIED

import os, re, shutil
from kitchen.text.converters import to_bytes
from CharmHooks import CharmHooks, DEFAULT_OS_ENV
from StorageConfig import StorageConfig
from pyutils.py_filesystem import first_that_exist


class StorageHooks(CharmHooks):

    def __init__(self, metadata, default_config, local_config_filename, default_os_env):
        super(StorageHooks, self).__init__(metadata, default_config, default_os_env)
        self.local_config = StorageConfig.read(local_config_filename, store_filename=True)
        self.debug(u'My __dict__ is {0}'.format(self.__dict__))

    # ------------------------------------------------------------------------------------------------------------------

    @property
    def allowed_ips_string(self):
        try:
            allowed_ips = self.config.allowed_ips.split(u',')
        except:
            allowed_ips = [self.config.allowed_ips]
        return u','.join(sorted(list(filter(None, self.local_config.allowed_ips + allowed_ips))))

    @property
    def brick(self):
        return u'{0}:{1}/exp{2}'.format(self.private_address, self.bricks_path, self.id)

    @property
    def bricks_path(self):
        return os.path.join(self.config.bricks_root_path, 'bricks')

    @property
    def volume(self):
        return u'medias_volume_{0}'.format(self.id)

    @property
    def volumes(self):
        return re.findall(u'Name:\s*(\S*)', self.volume_do(u'info', volume=u'all')[u'stdout'])

    # ------------------------------------------------------------------------------------------------------------------

    def peer_probe(self, peer_address, fail=True):
        return self.cmd(u'gluster peer probe {0}'.format(peer_address))

    def volume_create_or_expand(self, volume=None, bricks=None, replica=None):
        volume = volume or self.volume
        bricks = bricks or [self.brick]
        replica = replica or self.config.replica_count
        extra = (u' ' if replica == 1 else u' replica {0} transport tcp '.format(replica)) + u' '.join(bricks)
        if len(bricks) < replica:
            self.remark(u'Waiting for {0} peers to create and start a replica={1} volume {2}'.format(
                        replica - len(bricks), replica, volume))
        elif len(bricks) == replica:
            self.info(u'Create and start a replica={0} volume {1} with {2} brick{3}'.format(
                      replica, volume, len(bricks), u's' if len(bricks) > 1 else u''))
            self.volume_do(u'create', volume=volume, options=extra)
            self.volume_do(u'start', volume=volume)
            self.local_config.volume_flag = True
        else:
            vol_bricks = self.volume_infos(volume=volume)['bricks']
            self.debug(u'Volume bricks: {0}'.format(vol_bricks))
            new_bricks = [b for b in bricks if b not in vol_bricks]
            if len(new_bricks) == replica:
                self.info(u'Expand replica={0} volume {1} with new bricks'.format(replica, volume))
                self.volume_do(u'add-brick', volume=volume, options=u' '.join(new_bricks))
                self.volume_do(u'rebalance', volume=volume, options=u'start', fail=False)
            else:
                self.remark(u'Waiting for {0} peers to expand replica={1} volume {2}'.format(
                            replica - len(new_bricks), replica, volume))
        self.info(self.volume_infos(volume=volume))
        self.info(self.volume_do(u'rebalance', volume=volume, options=u'status', fail=False)[u'stdout'])

    def volume_do(self, action, volume=None, options=u'', input=None, cli_input=None, fail=True):
        volume = volume or self.volume
        return self.cmd(u'gluster volume {0} {1} {2}'.format(action, volume, options), input=input, cli_input=cli_input,
                        fail=fail)

    def volume_set_allowed_ips(self, volume=None):
        volume, ips = volume or self.volume, self.allowed_ips_string
        self.info(u'Set volume {0} allowed clients IP list to {1}'.format(volume, ips))
        self.volume_do(u'set', volume=volume, options=u'auth.allow "{0}"'.format(ips), fail=False)
        auth_allow = self.volume_infos(volume=volume)[u'auth_allow']
        if auth_allow != ips:
            raise ValueError(to_bytes(u'Volume {0} auth.allow={1} (expected {2})'.format(volume, ips, auth_allow)))
        self.info(self.volume_infos(volume=volume))

    def volume_infos(self, volume=None):
        u"""
        Returns a dictionary containing informations about a volume.

        **Example output**::

            {'name': 'medias_volume_6', 'type': 'Distribute', 'status': 'Started',
             'transport': 'tcp', 'bricks': ['domU-12-31-39-06-6C-E9.compute-1.internal:/mnt/bricks/exp6']}
        """
        stdout = self.volume_do(u'info', volume=volume, fail=False)[u'stdout']
        self.debug(u'Volume infos stdout: {0}'.format(repr(stdout)))
        match = self.local_config.volume_infos_regex.match(stdout)
        if match:
            infos = match.groupdict()
            infos[u'bricks'] = re.findall(u'Brick[0-9]+:\s*(\S*)', stdout)
            infos[u'auth_allow'] = u','.join(filter(None, re.findall(u'auth.allow:\s*(\S*)', stdout)))
            return infos
        return None

    # ------------------------------------------------------------------------------------------------------------------

    def hook_install(self):
        self.hook_uninstall()
        self.info(u'Upgrade system and install prerequisites')
        self.cmd(u'apt-get -y update', fail=False)
        self.cmd(u'apt-get -y upgrade')
        self.cmd(u'apt-get -y install ntp glusterfs-server nfs-common')
        self.info(u'Restart network time protocol service')
        self.cmd(u'service ntp restart')

        # Create medias volume if it is already possible to do so
        self.volume_create_or_expand()

        self.info(u'Expose GlusterFS Server service')
        self.open_port(111,   u'TCP')   # For portmapper, and should have both TCP and UDP open
        self.open_port(24007, u'TCP')   # For the Gluster Daemon
        #self.open_port(24008, u'TCP')  # Infiniband management (optional unless you are using IB)
        self.open_port(24009, u'TCP')   # We have only 1 storage brick (24009-24009)
        #self.open_port(38465, u'TCP')  # For NFS (not used)
        #self.open_port(38466, u'TCP')  # For NFS (not used)
        #self.open_port(38467, u'TCP')  # For NFS (not used)

    def hook_config_changed(self):
        if self.local_config.volume_flag:
            self.volume_set_allowed_ips()

    def hook_uninstall(self):
        self.info(u'Uninstall prerequisites, remove files & bricks and load default configuration')
        self.hook_stop()
        if self.config.cleanup:
            self.cmd(u'apt-get -y remove --purge glusterfs-server nfs-common')
            self.cmd(u'apt-get -y autoremove')
            shutil.rmtree(u'/etc/glusterd',  ignore_errors=True)
            shutil.rmtree(u'/etc/glusterfs', ignore_errors=True)
        shutil.rmtree(self.bricks_path, ignore_errors=True)
        os.makedirs(self.bricks_path)
        self.local_config.reset()

    def hook_start(self):
        if self.cmd(u'pgrep glusterd', fail=False)[u'returncode'] != 0:
            self.cmd(u'service glusterfs-server start')

    def hook_stop(self):
        if self.cmd(u'pgrep glusterd', fail=False)[u'returncode'] == 0:
            self.cmd(u'service glusterfs-server stop')

    def hook_storage_relation_joined(self):
        if self.local_config.volume_flag:
            self.info(u'Send filesystem (volume {0}) configuration to remote client'.format(self.volume))
            self.relation_set(fstype=u'glusterfs', mountpoint=self.volume, options=u'')
            client_address = self.relation_get('private-address')
            if not client_address in self.local_config.allowed_ips:
                self.info(u'Add {0} to allowed clients IPs'.format(client_address))
                self.local_config.allowed_ips.append(client_address)
                self.hook_config_changed()

    def hook_storage_relation_departed(self):
        # Get configuration from the relation
        client_address = self.relation_get(u'private-address')
        if not client_address:
            self.remark(u'Waiting for complete setup')
        elif client_address in self.local_config.allowed_ips:
            self.info(u'Remove {0} from allowed clients IPs'.format(client_address))
            self.local_config.allowed_ips.remove(client_address)
            self.hook_config_changed()

    def hook_storage_relation_broken(self):
        self.info(u'Cleanup allowed clients IPs')
        self.local_config.allowed_ips = []
        self.hook_config_changed()

    def hook_peer_relation_joined(self):
        if not self.is_leader:
            self.info(u'As slave, stop and delete my own volume {0}'.format(self.volume))
            if self.volume in self.volumes:
                self.debug(self.volume_infos())
                self.volume_do(u'stop', options=u'force', cli_input=u'y\n')
                self.volume_do(u'delete', cli_input=u'y\n', fail=False)  # FIXME temporary hack
                self.local_config.volume_flag = False

    def hook_peer_relation_changed(self):
        # Get configuration from the relation
        peer_address = self.relation_get(u'private-address')
        self.info(u'Peer address is {0}'.format(peer_address))
        if not peer_address:
            self.remark(u'Waiting for complete setup')
            return

        # FIXME close previously opened ports if some bricks leaved ...
        self.info(u'Open required ports')
        port, bricks = 24010, [self.brick]
        for peer in self.relation_list():
            self.open_port(port, u'TCP')  # Open required
            bricks.append(u'{0}:/exp{1}'.format(self.relation_get(u'private-address', peer), self.id))
            port += 1

        if self.is_leader:
            self.info(u'As leader, probe remote peer {0} and create or expand volume {1}'.format(
                      peer_address, self.volume))
            self.peer_probe(peer_address)
            self.volume_create_or_expand(bricks=bricks)

    def hook_peer_relation_broken(self):
        self.remark(u'FIXME NOT IMPLEMENTED')

# Main -----------------------------------------------------------------------------------------------------------------

if __name__ == u'__main__':
    from pyutils.py_unicode import configure_unicode
    configure_unicode()
    StorageHooks(first_that_exist(u'metadata.yaml',    u'../oscied-storage/metadata.yaml'),
                 first_that_exist(u'config.yaml',      u'../oscied-storage/config.yaml'),
                 first_that_exist(u'local_config.pkl', u'../oscied-storage/local_config.pkl'),
                 DEFAULT_OS_ENV).trigger()
