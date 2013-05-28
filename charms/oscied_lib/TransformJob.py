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

import uuid
from celery.result import AsyncResult
from .Media import MEDIA_TEST
from .TransformProfile import TRANSFORM_PROFILE_TEST
from .User import USER_TEST
from pyutils.pyutils import json2object, object2json, valid_uuid


class TransformJob(object):

    def __init__(self, _id, user_id, media_in_id, media_out_id, profile_id, statistic={},
                 revoked=False):
        if not _id:
            _id = str(uuid.uuid4())
        self._id = _id
        self.user_id = user_id
        self.media_in_id = media_in_id
        self.media_out_id = media_out_id
        self.profile_id = profile_id
        self.statistic = statistic
        self.revoked = revoked


    def is_valid(self, raise_exception):
        if not valid_uuid(self._id, False):
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : _id is not a valid uuid string')
            return False
        if hasattr(self, 'user_id') and not valid_uuid(self.user_id, False):
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : user_id is not a valid uuid string')
            return False
        # FIXME check user if loaded
        if hasattr(self, 'media_in_id') and not valid_uuid(self.media_in_id, False):
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : media_in_id is not a valid uuid string')
            return False
        # FIXME check media_in if loaded
        if hasattr(self, 'media_out_id') and not valid_uuid(self.media_out_id, False):
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : media_out_id is not a valid uuid string')
            return False
        # FIXME check media_out if loaded
        if hasattr(self, 'profile_id') and not valid_uuid(self.profile_id, False):
            if raise_exception:
                raise TypeError(self.__class__.__name__ + ' : profile_id is not a valid uuid string')
            return False
        # FIXME check profile if loaded
        # FIXME check statistic
        # FIXME check revoked
        return True

    def add_statistic(self, key, value, overwrite):
        if overwrite or not key in self.statistic:
            self.statistic[key] = value

    def get_statistic(self, key):
        return self.statistic[key] if key in self.statistic else None

    def append_async_result(self):
        async_result = AsyncResult(self._id)
        if async_result:
            self.status = async_result.status
            try:
                self.statistic.update(async_result.result)
            except:
                self.statistic['error'] = str(async_result.result)
        else:
            self.status = 'UNDEF'

    def load_fields(self, user, media_in, media_out, profile):
        self.user = user
        self.media_in = media_in
        self.media_out = media_out
        self.profile = profile
        delattr(self, 'user_id')
        delattr(self, 'media_in_id')
        delattr(self, 'media_out_id')
        delattr(self, 'profile_id')

    @staticmethod
    def load(json):
        job = TransformJob(None, None, None, None, None)
        json2object(json, job)
        return job

TRANSFORM_JOB_TEST = TransformJob(None, USER_TEST._id, MEDIA_TEST._id, MEDIA_TEST._id,
                                  TRANSFORM_PROFILE_TEST._id)

# --------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print object2json(TRANSFORM_JOB_TEST, True)
    TRANSFORM_JOB_TEST.is_valid(True)
    print str(TransformJob.load(object2json(TRANSFORM_JOB_TEST, False)))
