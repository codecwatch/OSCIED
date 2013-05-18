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

# Charmhelpers : /usr/share/pyshared/charmhelpers/__init__.py

import subprocess
try:
    import charmhelpers
except ImportError:
    subprocess.check_call(['apt-add-repository', '-y', 'ppa:juju/pkgs'])
    subprocess.check_call(['apt-get', 'install', '-y', 'python-charmhelpers'])

import charmhelpers  # This is not unused, this import is necessary
import os
import shlex
import sys
import yaml
from shelltoolbox import command

DEFAULT_OS_ENV = {
    'APT_LISTCHANGES_FRONTEND': 'none',
    'CHARM_DIR': '/var/lib/juju/units/oscied-storage-0/charm',
    'DEBIAN_FRONTEND': 'noninteractive',
    '_JUJU_CHARM_FORMAT': '1',
    'JUJU_AGENT_SOCKET': '/var/lib/juju/units/oscied-storage-0/.juju.hookcli.sock',
    'JUJU_CLIENT_ID': 'constant',
    'JUJU_ENV_UUID': '878ca8f623174911960f6fbed84f7bdd',
    'JUJU_PYTHONPATH': ':/usr/lib/python2.7/dist-packages:/usr/lib/python2.7'
                       ':/usr/lib/python2.7/plat-x86_64-linux-gnu'
                       ':/usr/lib/python2.7/lib-tk'
                       ':/usr/lib/python2.7/lib-old'
                       ':/usr/lib/python2.7/lib-dynload'
                       ':/usr/local/lib/python2.7/dist-packages'
                       ':/usr/lib/pymodules/python2.7',
    '_': '/usr/bin/python',
    'JUJU_UNIT_NAME': 'oscied-storage/0',
    'PATH': '/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin',
    'PWD': '/var/lib/juju/units/oscied-storage-0/charm',
    'SHLVL': '1'
}

__get_ip = None


def get_ip():
    global __get_ip
    if __get_ip is None:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        __get_ip = s.getsockname()[0]
        s.close()
    return __get_ip


class CharmHooks(object):
    u"""
    TODO

    **Example usage**:

    >>> print('TODO')
    TODO
    """

    def __init__(self, default_config, default_os_env):
        self.config = lambda: None
        setattr(self.config, 'verbose', False)
        try:
            self.juju_ok = True
            self.juju_log = command('juju-log')
            self.load_config(charmhelpers.get_config())
            self.env_uuid = os.environ['JUJU_ENV_UUID']
            self.name = os.environ['JUJU_UNIT_NAME']
            self.private_address = charmhelpers.unit_get('private-address')
        except subprocess.CalledProcessError:
            self.juju_ok = False
            self.juju_log = command('echo')
            if default_config is not None:
                self.load_config(default_config)
            self.env_uuid = default_os_env['JUJU_ENV_UUID']
            self.name = default_os_env['JUJU_UNIT_NAME']
            self.private_address = get_ip()
        self.debug('My __dict__ is %s' % self.__dict__)

    # ----------------------------------------------------------------------------------------------

    @property
    def id(self):
        u"""
        Returns the id extracted from the unit's name.

        **Example usage**:

        >>> hooks = CharmHooks(None, DEFAULT_OS_ENV)
        >>> hooks.name = 'oscied-storage/3'
        >>> hooks.id
        3
        """
        return int(self.name.split('/')[1])

    # Maps calls to charm helpers methods and replace them if called in standalone -----------------

    def log(self, message):
        if self.juju_ok:
            return charmhelpers.log(message, self.juju_log)
        print(message)
        return None

    def open_port(self, port, protocol='TCP'):
        if self.juju_ok:
            charmhelpers.open_port(port, protocol)
        else:
            self.debug('Open port %s (%s)' % (port, protocol))

    def close_port(self, port, protocol='TCP'):
        if self.juju_ok:
            charmhelpers.close_port(port, protocol)
        else:
            self.debug('Close port %s (%s)' % (port, protocol))

    def unit_get(self, attribute):
        if self.juju_ok:
            return charmhelpers.unit_get(attribute)
        raise NotImplementedError('FIXME unit_get not yet implemented')

    def relation_get(self, attribute=None, unit=None, rid=None):
        if self.juju_ok:
            return charmhelpers.relation_get(attribute, unit, rid)
        raise NotImplementedError('FIXME relation_get not yet implemented')

    def relation_ids(self, relation_name):
        if self.juju_ok:
            return charmhelpers.relation_ids(relation_name)
        raise NotImplementedError('FIXME relation_ids not yet implemented')

    def relation_list(self, rid=None):
        if self.juju_ok:
            return charmhelpers.relation_list
        raise NotImplementedError('FIXME relation_list not yet implemented')

    def relation_set(self, **kwargs):
        if self.juju_ok:
            charmhelpers.relation_set(kwargs)
        else:
            raise NotImplementedError('FIXME relation_set not yet implemented')

    def peer_i_am_leader(self):
        return True  # FIXME not implemented

    # Convenience methods for logging --------------------------------------------------------------

    def debug(self, message):
        u"""
        Convenience method for logging a debug-related message.
        """
        if self.config.verbose:
            return self.log('[DEBUG] %s' % message)

    def info(self, message):
        u"""
        Convenience method for logging a standard message.
        """
        return self.log('[INFO] %s' % message)

    def hook(self, message):
        u"""
        Convenience method for logging the triggering of a hook.
        """
        return self.log('[HOOK] %s' % message)

    def remark(self, message):
        u"""
        Convenience method for logging an important remark.
        """
        return self.log('[REMARK] %s !' % message)

    # ----------------------------------------------------------------------------------------------

    def load_config(self, config):
        u"""
        Updates ``config`` attribute with given configuration, ``config`` can be:

        * The filename of a charm configuration file (e.g. ``config.yaml``)
        * A dictionary containing the options names as keys and options values as values.

        **Example usage**:

        >>> hooks = CharmHooks(None, DEFAULT_OS_ENV)
        >>> hasattr(hooks.config, 'pingu') or hasattr(hooks.config, 'rabbit_password')
        False
        >>> hooks.load_config({'pingu': 'bi bi'})
        >>> print(hooks.config.pingu)
        bi bi
        >>> hooks.config.verbose = True
        >>> hooks.load_config('../oscied-orchestra/config.yaml')  # doctest: +ELLIPSIS
        [DEBUG] Load config from file ../oscied-orchestra/config.yaml
        [DEBUG] Convert boolean option verbose false -> False
        [DEBUG] Config is ...
        >>> hasattr(hooks.config, 'rabbit_password')
        True
        """
        if isinstance(config, str):
            self.debug('Load config from file %s' % config)
            with open(config) as f:
                options = yaml.load(f)['options']
                config = {}
                for option in options:
                    config[option] = options[option]['default']
        for option, value in config.iteritems():
            if str(value).lower() in ('false', 'true'):
                config[option] = True if str(value).lower() == 'true' else False
                self.debug('Convert boolean option %s %s -> %s' % (option, value, config[option]))
        self.debug('Config is %s' % config)
        self.config.__dict__.update(config)

    # ----------------------------------------------------------------------------------------------

    def cmd(self, command, input=None, cli_input=None, fail=True):
        u"""
        Calls the ``command`` and returns a dictionary with stdout, stderr, and the returncode.

        * Pipe some content to the command with ``input``.
        * Answer to interactive CLI questions with ``cli_input``.
        * Set ``fail`` to False to avoid the exception ``subprocess.CalledProcessError``.

        **Example usage**:

        >>> hooks = CharmHooks(None, DEFAULT_OS_ENV)
        >>> print(hooks.cmd(['echo', 'it seem to work'])['stdout'])
        it seem to work
        <BLANKLINE>

        >>> assert(hooks.cmd('cat missing_file', fail=False)['returncode'] != 0)

        >>> hooks.cmd('my.funny.missing.script.sh')
        Traceback (most recent call last):
        ...
        OSError: [Errno 2] No such file or directory

        >>> result = hooks.cmd('cat CharmHooks.py')
        >>> print(result['stdout'].splitlines()[0])
        #!/usr/bin/env python2
        """
        self.debug('Execute %s%s%s' % ('' if input is None else 'echo %s | ' % repr(input), command,
                   '' if cli_input is None else ' < %s' % repr(cli_input)))
        args = command
        if isinstance(command, str):
            args = shlex.split(command)
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        if cli_input is not None:
            process.stdin.write(cli_input)
        stdout, stderr = process.communicate(input=input)
        result = {'stdout': stdout, 'stderr': stderr, 'returncode': process.returncode}
        if fail and process.returncode != 0:
            self.debug(result)
            raise subprocess.CalledProcessError(process.returncode, command, stderr)
        return result

    # ----------------------------------------------------------------------------------------------

    def trigger(self, hook_name=None):
        u"""
        Triggers a hook specified in ``hook_name``, defaults to ``sys.argv[1]``.

        Hook's name is the nice hook name that one can find in official juju documentation.
        For example if ``config-changed`` is mapped to a call to ``self.hook_config_changed()``.

        A ``ValueError`` containing a usage string is raised if a bad number of argument is given.
        """
        if hook_name is None:
            if len(sys.argv) != 2:
                raise ValueError('Usage %s hook_name (e.g. config-changed)' % sys.argv[0])
            hook_name = sys.argv[1]

        if self.juju_ok:
            charmhelpers.log_entry()
        try:  # Call the function hooks_...
            self.hook('Execute %s hook %s' % (self.__class__.__name__, hook_name))
            getattr(self, 'hook_%s' % hook_name.replace('-', '_'))()
        except subprocess.CalledProcessError as e:
            self.log('Exception caught:')
            self.log(e.output)
            raise
        finally:
            if self.juju_ok:
                charmhelpers.log_exit()

if __name__ == '__main__':
    print('Testing CharmHooks with doctest')
    import doctest
    doctest.testmod(verbose=False)
    print ('OK')
