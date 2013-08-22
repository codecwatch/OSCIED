#!/usr/bin/env python
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

import sys
from os.path import abspath, dirname, join
from requests import get, post
sys.path.append(abspath(dirname(dirname(__file__))))
sys.path.append(abspath(join(dirname(dirname(__file__)), u'pyutils')))

from mock import call
from nose.tools import assert_equal, assert_raises
from oscied_lib.oscied_client import OsciedCRUDMapper, OrchestraAPIClient
from oscied_lib.oscied_models import User
from pyutils.py_mock import mock_cmd


class FakeAPIClient(object):
    def __init__(self, api_url, environment='maas'):
        self.api_url = api_url
        self.environment = environment
        self.do_request = mock_cmd()


class TestOsciedCRUDMapper(object):

    def test_get_url_without_environment(self):
        client = FakeAPIClient('http://test.com:5000')
        mapper = OsciedCRUDMapper(client, id_prefix='id')
        assert_equal(mapper.get_url(), u'http://test.com:5000')
        assert_equal(mapper.get_url(extra='extra_value'), u'http://test.com:5000/extra_value')
        assert_equal(mapper.get_url(index='index_value'), u'http://test.com:5000/id/index_value')
        assert_equal(mapper.get_url(index='index_value', extra='extra_value'),
                     u'http://test.com:5000/id/index_value/extra_value')

    def test_get_url_with_environment(self):
        client = FakeAPIClient('http://test.com:5000')
        mapper = OsciedCRUDMapper(client, id_prefix='id', environment=True)
        assert_equal(mapper.get_url(), u'http://test.com:5000/environment/maas')
        assert_equal(mapper.get_url(extra='extra_value'), u'http://test.com:5000/environment/maas/extra_value')
        assert_equal(mapper.get_url(index='index_value'), u'http://test.com:5000/environment/maas/id/index_value')
        assert_equal(mapper.get_url(index='index_value', extra='extra_value'),
                     u'http://test.com:5000/environment/maas/id/index_value/extra_value')

    def test_add_cls_none(self):
        client = FakeAPIClient('http://test.com:5000')
        mapper = OsciedCRUDMapper(client, 'method')
        assert_raises(ValueError, mapper.add)
        assert_raises(ValueError, mapper.add, 10, arg=20)
        mapper.add('hello')
        mapper.add(arg1=0)
        assert_equal(client.do_request.call_args_list, [
            call(post, u'http://test.com:5000/method', data='"hello"'),
            call(post, u'http://test.com:5000/method', data='{"arg1": 0}')])

    def test_add_cls_user(self):
        client = FakeAPIClient('http://test.com:5000')
        mapper = OsciedCRUDMapper(client, 'method', User, environment=True)
        user = User(first_name='Tabby', last_name='Fischer', mail='t@f.com', secret='mia0w_mia0w')
        user._id = '3959e400-94b0-49f7-8b0f-fd168b7c90e3'
        user.is_valid(True)
        mapper.add(user)
        assert_equal(client.do_request.call_args_list, [
            call(post, u'http://test.com:5000/method/environment/maas',
                 data='{"first_name": "Tabby", "last_name": "Fischer", "admin_platform": false, "secret": "mia0w_mia0w"'
                      ', "mail": "t@f.com", "_id": "3959e400-94b0-49f7-8b0f-fd168b7c90e3"}')])


def assert_len(client, mapper, expected):
    client.do_request = mock_cmd()
    try:
        len(mapper)
    except:
        pass
    assert_equal(client.do_request.call_args_list, expected)


class TestOrchestraAPIClient(object):

    def test_len(self):
        client = OrchestraAPIClient('http://a.ch', 6000, auth=('username', 'password'))
        assert_equal(client.users.get_url(), 'http://a.ch:6000/user')
        assert_len(client, client.users, [call(get, u'http://a.ch:6000/user/count')])
        assert_len(client, client.medias, [call(get, u'http://a.ch:6000/media/count')])
        assert_len(client, client.environments, [call(get, u'http://a.ch:6000/environment/count')])
        assert_len(client, client.transform_profiles, [call(get, u'http://a.ch:6000/transform/profile/count')])
        #assert_len(client, client.transform_units, [call(get, u'http://a.ch:6000/transform/unit/count')])
        assert_len(client, client.transform_tasks, [call(get, u'http://a.ch:6000/transform/task/count')])


if __name__ == u'__main__':
    import nose
    nose.runmodule(argv=[__file__], exit=False)
