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

from kitchen.text.converters import to_bytes
from Media import MEDIA_TEST
from OsciedDBTask import OsciedDBTask
from TransformProfile import TRANSFORM_PROFILE_TEST
from User import USER_TEST
from pyutils.py_validation import valid_uuid


class TransformTask(OsciedDBTask):

    def __init__(self, user_id=None, media_in_id=None, media_out_id=None, profile_id=None, **kwargs):
        super(TransformTask, self).__init__(**kwargs)
        self.user_id = user_id
        self.media_in_id = media_in_id
        self.media_out_id = media_out_id
        self.profile_id = profile_id

    def is_valid(self, raise_exception):
        if not super(TransformTask, self).is_valid(raise_exception):
            return False
        if hasattr(self, u'user_id') and not valid_uuid(self.user_id, none_allowed=False):
            self._E(raise_exception, u'user_id is not a valid uuid string')
        # FIXME check user if loaded
        if hasattr(self, u'media_in_id') and not valid_uuid(self.media_in_id, none_allowed=False):
            self._E(raise_exception, u'media_in_id is not a valid uuid string')
        # FIXME check media_in if loaded
        if hasattr(self, u'media_out_id') and not valid_uuid(self.media_out_id, none_allowed=False):
            self._E(raise_exception, u'media_out_id is not a valid uuid string')
        # FIXME check media_out if loaded
        if hasattr(self, u'profile_id') and not valid_uuid(self.profile_id, none_allowed=False):
            self._E(raise_exception, u'profile_id is not a valid uuid string')
        # FIXME check profile if loaded
        return True

    def load_fields(self, user, media_in, media_out, profile):
        self.user = user
        self.media_in = media_in
        self.media_out = media_out
        self.profile = profile
        delattr(self, u'user_id')
        delattr(self, u'media_in_id')
        delattr(self, u'media_out_id')
        delattr(self, u'profile_id')

    @staticmethod
    def validate_task(media_in, profile, media_out):
        if not media_in.status in (u'READY', u'PUBLISHED'):
            raise NotImplementedError(to_bytes(u'Cannot launch the task, input media status is {0}.'.format(
                                      media_in.status)))
        if media_in.is_dash and profile.encoder_name != u'copy':
            raise NotImplementedError(to_bytes(u'Cannot launch the task, input media is MPEG-DASH content and encoder '
                                      'is not copy.'))
        if profile.is_dash and not media_out.is_dash:
            raise ValueError(to_bytes(u'Cannot launch the task, output media is not a MPD but task is based on a '
                             'MPEG-DASH encoder called {0}.'.format(profile.encoder_name)))
        if not profile.is_dash and media_out.is_dash:
            raise ValueError(to_bytes(u'Cannot launch the task, output media is a MPD but task is not based on a '
                             'MPEG-DASH encoder called {0}.'.format(profile.encoder_name)))

TRANSFORM_JOB_TEST = TransformTask(user_id=USER_TEST._id, media_in_id=MEDIA_TEST._id, media_out_id=MEDIA_TEST._id,
                                   profile_id=TRANSFORM_PROFILE_TEST._id)
