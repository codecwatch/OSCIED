# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : ORCHESTRA
#
#  Project Manager  : Bram Tullemans (tullemans@ebu.ch)
#  Main Developer   : David Fischer (david.fischer.ch@gmail.com)
#  PlugIt Developer : Maximilien Cuony (maximilien@theglu.org)
#  Copyright        : Copyright (c) 2012-2013 EBU. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of EBU Technology & Innovation OSCIED + PlugIt Projects.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/ebu/OSCIED

u"""Utility methods and decorators."""

import hashlib


# Decorators -----------------------------------------------------------------------------------------------------------

def action(route, template=u'', methods=[u'GET']):
    u"""Decorator to create an action."""
    def real_decorator(function):
        function.pi_api_action = True
        function.pi_api_route = route
        function.pi_api_template = template
        function.pi_api_methods = methods
        return function
    return real_decorator


def only_logged_user():
    u"""Decorator to specify the action must only be called by logger users."""
    def real_decorator(function):
        function.pi_api_only_logged_user = True
        return function
    return real_decorator


def only_member_user():
    u"""Decorator to specify the action must only be called by users members of the project."""
    def real_decorator(function):
        function.pi_api_only_member_user = True
        return function
    return real_decorator


def only_admin_user():
    u"""Decorator to specify the action must only be called by administrator users of the project."""
    def real_decorator(function):
        function.pi_api_only_admin_user = True
        return function
    return real_decorator

def only_orga_member_user():
    u"""Decorator to specify the action must only be called by users members of the organization"""
    def real_decorator(function):
        function.pi_api_only_orga_member_user = True
        return function
    return real_decorator


def only_orga_admin_user():
    u"""Decorator to specify the action must only be called by admin users of the organization"""
    def real_decorator(function):
        function.pi_api_only_orga_admin_user = True
        return function
    return real_decorator


def cache(time=0, byUser=None):
    u"""Decorator to specify the number of seconds the result should be cached, and if the cache can be shared between
    users."""
    def real_decorator(function):
        function.pi_api_cache_time = time
        function.pi_api_cache_by_user = byUser
        return function
    return real_decorator


def user_info(props):
    u"""Decorator to specify a list of properties requested about the current user."""
    def real_decorator(function):
        function.pi_api_user_info = props
        return function
    return real_decorator


def json_only():
    u"""Decorator to specify the action return json that should be send directly to the browser."""
    def real_decorator(function):
        function.pi_api_json_only = True
        return function
    return real_decorator


# Utility methods ------------------------------------------------------------------------------------------------------

def md5Checksum(filePath):
    u"""Compute the MD5 sum of a file."""
    with open(filePath, u'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


# Classes --------------------------------------------------------------------------------------------------------------

class PlugItRedirect():
    u"""Object to perform a redirection."""
    def __init__(self, url, no_prefix=False):
        self.url = url
        self.no_prefix = no_prefix


class PlugItSendFile():
    u"""
    Object to send a file to the client browser.
    Use the flask function send_file to send the file to the PlugIt client.
    """
    def __init__(self, filename, mimetype, as_attachment=False, attachment_filename=u''):
        self.mimetype = mimetype
        self.filename = filename
        self.as_attachment = as_attachment
        self.attachment_filename = attachment_filename
