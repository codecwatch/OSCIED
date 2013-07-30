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

import requests
from urlparse import urlparse, ParseResult
from pyutils.py_serialization import JsoneableObject


class Callback(JsoneableObject):
    def __init__(self, url=None, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password

    def is_valid(self, raise_exception):
        # FIXME check fields
        return True

    def replace_netloc(self, netloc):
        u"""
        Replace network location of the media URI.

        **Example usage**:

        >>> import copy
        >>> callback = copy.copy(CALLBACK_TEST)
        >>> callback.is_valid(True)
        True
        >>> print(callback.url)
        http://127.0.0.1:5000/media
        >>> callback.replace_netloc(u'129.194.185.47:5003')
        >>> print(callback.url)
        http://129.194.185.47:5003/media
        """
        url = urlparse(self.url)
        url = ParseResult(url.scheme, netloc, url.path, url.params, url.query, url.fragment)
        self.url = url.geturl()

    def post(self, data_json):
#       return requests.post(self.url, data_json, auth=(self.username, self.password))
        headers = {u'Content-type': u'application/json', u'Accept': u'text/plain'}
        return requests.post(self.url, headers=headers, data=data_json, auth=(self.username, self.password))

CALLBACK_TEST = Callback(u'http://127.0.0.1:5000/media', u'toto', u'1234')
