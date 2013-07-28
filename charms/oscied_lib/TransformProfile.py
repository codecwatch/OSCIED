#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : COMMON LIBRARY
#
#  Authors   : David Fischer
#  Contact   : david.fischer.ch@gmail.com
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
# Retrieved from https://github.com/ebu/OSCIED

import uuid
from pyutils.py_serialization import json2object, object2json
from pyutils.py_validation import valid_uuid

ENCODERS_NAMES = ('copy', 'ffmpeg', 'dashcast')


class TransformProfile(object):

    def __init__(self, _id, title, description, encoder_name, encoder_string):
        if not _id:
            _id = str(uuid.uuid4())
        self._id = _id
        self.title = title
        self.description = description
        self.encoder_name = encoder_name
        self.encoder_string = encoder_string

    @property
    def is_dash(self):
        u"""
        >>> import copy
        >>> profile = copy.copy(TRANSFORM_PROFILE_TEST)
        >>> assert(not profile.is_dash)
        >>> profile.encoder_name = 'dashcast'
        >>> assert(profile.is_dash)
        """
        return self.encoder_name in ('dashcast')

    # FIXME test other fields
    def is_valid(self, raise_exception):
        if not valid_uuid(self._id, none_allowed=False):
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : _id is not a valid uuid string')
            return False
        if not self.title or not self.title.strip():
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : title is required')
            return False
        if not self.encoder_name in ENCODERS_NAMES:
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : encoder_name is not a valid encoder')
            return False
        return True

    @staticmethod
    def load(json):
        profile = TransformProfile(None, None, None, None, None)
        json2object(json, profile)
        return profile

TRANSFORM_PROFILE_TEST = TransformProfile(None, 'HD 1080p', 'MP4 H.264 1080p, audio copy', 'ffmpeg',
                                          '-c:a copy ...')

# Main ---------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print object2json(TRANSFORM_PROFILE_TEST, True)
    TRANSFORM_PROFILE_TEST.is_valid(True)
    print str(TransformProfile.load(object2json(TRANSFORM_PROFILE_TEST, False)))
    print('Testing TransformProfile with doctest')
    import doctest
    assert(doctest.testmod(verbose=False))
    print('OK')
