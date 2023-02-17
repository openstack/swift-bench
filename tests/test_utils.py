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

import io

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
        fd, temppath = tempfile.mkstemp(dir='/tmp')
        with os.fdopen(fd, 'w') as f:
            f.write(conf)
        # Test both a real file and a file-like object
        for conffile in (temppath, io.StringIO(conf)):
            result = utils.readconf(conffile)
            expected = {'__file__': conffile,
                        'log_name': None,
                        'section1': {'foo': 'bar'},
                        'section2': {'log_name': 'yarr'}}
            self.assertEqual(result, expected)

            result = utils.readconf(conffile, 'section1')
            expected = {'__file__': conffile, 'log_name': 'section1',
                        'foo': 'bar'}
            self.assertEqual(result, expected)

            result = utils.readconf(conffile,
                                    'section2').get('log_name')
            expected = 'yarr'
            self.assertEqual(result, expected)

            result = utils.readconf(conffile, 'section1',
                                    log_name='foo').get('log_name')
            expected = 'foo'
            self.assertEqual(result, expected)

            result = utils.readconf(conffile, 'section1',
                                    defaults={'bar': 'baz'})
            expected = {'__file__': conffile, 'log_name': 'section1',
                        'foo': 'bar', 'bar': 'baz'}
            self.assertEqual(result, expected)
        self.assertRaises(SystemExit, utils.readconf, temppath, 'section3')
        os.unlink(temppath)
        self.assertRaises(SystemExit, utils.readconf, temppath)

    def test_readconf_raw(self):
        conf = '''[section1]
foo = bar

[section2]
log_name = %(yarr)s'''
        fd, temppath = tempfile.mkstemp(dir='/tmp')
        with os.fdopen(fd, 'w') as f:
            f.write(conf)
        # Test both a real file and a file-like object
        for conffile in (temppath, io.StringIO(conf)):
            result = utils.readconf(conffile, raw=True)
            expected = {'__file__': conffile,
                        'log_name': None,
                        'section1': {'foo': 'bar'},
                        'section2': {'log_name': '%(yarr)s'}}
            self.assertEqual(result, expected)
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

    def test_get_size_bytes(self):
        self.assertEqual(utils.get_size_bytes('10M'), 10 * 1024 * 1024)
        self.assertEqual(utils.get_size_bytes('4k'), 4096)
        self.assertEqual(utils.get_size_bytes('5G'), 5 * 1024 * 1024 * 1024)
        self.assertEqual(utils.get_size_bytes('1234'), 1234)
        self.assertEqual(utils.get_size_bytes('1 k'), 1024)
        self.assertEqual(utils.get_size_bytes(' 1k'), 1024)
        self.assertEqual(utils.get_size_bytes('1k '), 1024)

        with self.assertRaises(ValueError):
            utils.get_size_bytes('1K')
        with self.assertRaises(ValueError):
            utils.get_size_bytes('1m')
        with self.assertRaises(ValueError):
            utils.get_size_bytes('1g')

        with self.assertRaises(ValueError):
            utils.get_size_bytes('1kb')
        with self.assertRaises(ValueError):
            utils.get_size_bytes('1kB')

        with self.assertRaises(ValueError):
            utils.get_size_bytes('1T')
        with self.assertRaises(ValueError):
            utils.get_size_bytes('1P')
        with self.assertRaises(ValueError):
            utils.get_size_bytes('1E')
        with self.assertRaises(ValueError):
            utils.get_size_bytes('1Y')
        with self.assertRaises(ValueError):
            utils.get_size_bytes('asdf')

        self.assertEqual(utils.get_size_bytes(1), 1)
        with self.assertRaises(TypeError):
            utils.get_size_bytes(1.0)


if __name__ == '__main__':
    unittest.main()
