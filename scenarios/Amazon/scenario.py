#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : SCENARIOS
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

from library.oscied_lib.pyutils.py_juju import DeploymentScenario

description = u'Launch oscied (nano setup) on Amazon'

class Amazon(DeploymentScenario):

    def run(self):
        print(description)
        self.bootstrap(u'amazon', wait_started=True)
        self.deploy(u'oscied-orchestra', 1, expose=True)
        self.deploy(u'oscied-storage',   1)
        self.deploy(u'oscied-transform', 1, to=2)
        self.deploy(u'oscied-webui',     1, to=1, expose=True)
        self.deploy(u'oscied-publisher', 1, to=2, expose=True)
        has_proxy = self.deploy(u'haproxy', 1, expose=True, release=u'precise', required=False)

        for peer in (u'orchestra', u'webui', u'transform', u'publisher'):
            self.add_relation(u'oscied-storage', u'oscied-{0}'.format(peer))
        self.add_relation(u'oscied-orchestra:transform', u'oscied-transform:transform')
        self.add_relation(u'oscied-orchestra:publisher', u'oscied-publisher:publisher')
        self.add_relation(u'oscied-orchestra:api',       u'oscied-webui:api')
        if has_proxy:
            if self.add_relation(u'haproxy', u'oscied-webui'):
                self.unexpose_service(u'oscied-webui')

if __name__ == u'__main__':
    Amazon().main()
