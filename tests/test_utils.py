# Copyright (c) 2010-2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import os
import tempfile
import unittest

from StringIO import StringIO

from swiftbench import utils


class TestUtils(unittest.TestCase):

    @mock.patch.object(utils, "TRUE_VALUES")
    def test_config_true_value(self, mocked):
        utils.TRUE_VALUES = 'hello world'.split()
        for val in 'hello world HELLO WORLD'.split():
            self.assertTrue(utils.config_true_value(val) is True)
            self.assertTrue(utils.config_true_value(True) is True)
            self.assertTrue(utils.config_true_value('foo') is False)
            self.assertTrue(utils.config_true_value(False) is False)

    def test_readconf(self):
        conf = '''[section1]
foo = bar

[section2]
log_name = yarr'''
        # setup a real file
        fd, temppath = tempfile.mkstemp(dir='/tmp')
        with os.fdopen(fd, 'wb') as f:
            f.write(conf)
        make_filename = lambda: temppath
        # setup a file stream
        make_fp = lambda: StringIO(conf)
        for conf_object_maker in (make_filename, make_fp):
            conffile = conf_object_maker()
            result = utils.readconf(conffile)
            expected = {'__file__': conffile,
                        'log_name': None,
                        'section1': {'foo': 'bar'},
                        'section2': {'log_name': 'yarr'}}
            self.assertEquals(result, expected)
            conffile = conf_object_maker()
            result = utils.readconf(conffile, 'section1')
            expected = {'__file__': conffile, 'log_name': 'section1',
                        'foo': 'bar'}
            self.assertEquals(result, expected)
            conffile = conf_object_maker()
            result = utils.readconf(conffile,
                                    'section2').get('log_name')
            expected = 'yarr'
            self.assertEquals(result, expected)
            conffile = conf_object_maker()
            result = utils.readconf(conffile, 'section1',
                                    log_name='foo').get('log_name')
            expected = 'foo'
            self.assertEquals(result, expected)
            conffile = conf_object_maker()
            result = utils.readconf(conffile, 'section1',
                                    defaults={'bar': 'baz'})
            expected = {'__file__': conffile, 'log_name': 'section1',
                        'foo': 'bar', 'bar': 'baz'}
            self.assertEquals(result, expected)
        self.assertRaises(SystemExit, utils.readconf, temppath, 'section3')
        os.unlink(temppath)
        self.assertRaises(SystemExit, utils.readconf, temppath)

    def test_readconf_raw(self):
        conf = '''[section1]
foo = bar

[section2]
log_name = %(yarr)s'''
        # setup a real file
        fd, temppath = tempfile.mkstemp(dir='/tmp')
        with os.fdopen(fd, 'wb') as f:
            f.write(conf)
        make_filename = lambda: temppath
        # setup a file stream
        make_fp = lambda: StringIO(conf)
        for conf_object_maker in (make_filename, make_fp):
            conffile = conf_object_maker()
            result = utils.readconf(conffile, raw=True)
            expected = {'__file__': conffile,
                        'log_name': None,
                        'section1': {'foo': 'bar'},
                        'section2': {'log_name': '%(yarr)s'}}
            self.assertEquals(result, expected)
        os.unlink(temppath)
        self.assertRaises(SystemExit, utils.readconf, temppath)

    @mock.patch("swiftbench.utils.getproxies")
    @mock.patch("swiftbench.utils.proxy_bypass")
    def test_using_http_proxy(self, mock_proxy_bypass, mock_getproxies):
        mock_getproxies.return_value = {'http': 'proxy', 'https': 'proxy'}

        def fake_proxy_bypass(url):
            return url == "localhost"
        mock_proxy_bypass.side_effect = fake_proxy_bypass

        self.assertTrue(utils.using_http_proxy("http://host1/"))
        self.assertFalse(utils.using_http_proxy("http://localhost/"))
        self.assertTrue(utils.using_http_proxy("https://host1/"))
        self.assertFalse(utils.using_http_proxy("https://localhost/"))
        self.assertFalse(utils.using_http_proxy("dummy://localhost/"))
        self.assertFalse(utils.using_http_proxy("dummy://host1/"))

if __name__ == '__main__':
    unittest.main()
