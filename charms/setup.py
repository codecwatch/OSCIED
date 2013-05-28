#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : COMMON LIBRARIE
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

from setuptools import setup

setup(name='oscied-lib',
      version='1.0',
      author='David Fischer',
      author_email='david.fischer.ch@gmail.com',
      install_requires=['argparse', 'configobj', 'celery', 'flask', 'hashlib', 'ipaddr', 'mock',
                        'passlib', 'pymongo', 'requests', 'six'],
      dependency_links=['https://github.com/davidfischer-ch/pyutils/tarball/master#egg=pyutils-1.0'],
      tests_require=['mock', 'nose'],
      license='GPLv3',
      url='https://github.com/EBU-TI/OSCIED',
      packages=['oscied_lib'],
      test_suite="tests")
