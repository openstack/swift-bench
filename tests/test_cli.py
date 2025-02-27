# Copyright (c) 2022 NVIDIA
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
import unittest
from unittest import mock
from swiftbench import cli


class TestCli(unittest.TestCase):

    def setUp(self):
        self.container_options = None
        self.delete_options = None

    def fake_create_containers(self, logger, options):
        self.container_options = options

    def fake_delete_containers(self, logger, options):
        self.delete_options = options

    def run_main(self, args):
        mock_controller = mock.Mock()

        with mock.patch('swiftbench.cli.create_containers',
                        self.fake_create_containers), \
                mock.patch('swiftbench.cli.delete_containers',
                           self.fake_delete_containers), \
                mock.patch('swiftbench.cli.BenchController',
                           mock_controller), \
                mock.patch('swiftbench.cli.DistributedBenchController',
                           mock_controller):
            cli.main(args)
        return (mock_controller.call_args[0][-1], self.container_options,
                self.delete_options)

    def test_defaults(self):
        controller_opts, container_opts, del_opts = self.run_main([])
        self.assertFalse(controller_opts.saio)
        self.assertEqual(controller_opts.auth, '')
        self.assertEqual(controller_opts.user, '')
        self.assertEqual(controller_opts.key, '')
        self.assertEqual(controller_opts.url, '')
        self.assertIsNone(controller_opts.concurrency)
        self.assertEqual(controller_opts.get_concurrency, 10)
        self.assertEqual(controller_opts.put_concurrency, 10)
        self.assertEqual(controller_opts.lower_object_size, 10)
        self.assertEqual(controller_opts.upper_object_size, 10)
        self.assertEqual(controller_opts.num_objects, 1000)
        self.assertEqual(controller_opts.num_gets, 10000)
        self.assertEqual(controller_opts.num_containers, 20)
        self.assertEqual(len(controller_opts.containers), 20)
        self.assertTrue(controller_opts.delete)
        self.assertEqual(controller_opts.auth_version, '1.0')
        self.assertEqual(controller_opts.delay, 0)
        self.assertIsNone(controller_opts.policy_name)
        self.assertTrue(controller_opts.use_proxy)
        self.assertEqual(controller_opts.del_concurrency, 10)
        self.assertEqual(controller_opts.object_sources, '')
        self.assertEqual(controller_opts.account, '')
        self.assertEqual(controller_opts.container_name, mock.ANY)
        self.assertEqual(controller_opts.devices, 'sdb1')
        self.assertEqual(controller_opts.log_level, 'INFO')
        self.assertEqual(controller_opts.timeout, 10)
        self.assertEqual(controller_opts.bench_clients, [])
        self.assertTrue(controller_opts.containers)

    def test_defaults_with_saio(self):
        controller_opts, container_opts, del_opts = self.run_main(['--saio'])
        self.assertTrue(controller_opts.saio)
        self.assertEqual(controller_opts.auth,
                         'http://localhost:8080/auth/v1.0')
        self.assertEqual(controller_opts.user, 'test:tester')
        self.assertEqual(controller_opts.key, 'testing')
        self.assertEqual(controller_opts.url, '')
        self.assertIsNone(controller_opts.concurrency)
        self.assertEqual(controller_opts.get_concurrency, 10)
        self.assertEqual(controller_opts.put_concurrency, 10)
        self.assertEqual(controller_opts.lower_object_size, 10)
        self.assertEqual(controller_opts.upper_object_size, 10)
        self.assertEqual(controller_opts.num_objects, 1000)
        self.assertEqual(controller_opts.num_gets, 10000)
        self.assertEqual(controller_opts.num_containers, 20)
        self.assertEqual(len(controller_opts.containers), 20)
        self.assertTrue(controller_opts.delete)
        self.assertEqual(controller_opts.auth_version, '1.0')
        self.assertEqual(controller_opts.delay, 0)
        self.assertIsNone(controller_opts.policy_name)
        self.assertTrue(controller_opts.use_proxy)
        self.assertEqual(controller_opts.del_concurrency, 10)
        self.assertEqual(controller_opts.object_sources, '')
        self.assertEqual(controller_opts.account, '')
        self.assertEqual(controller_opts.container_name, mock.ANY)
        self.assertEqual(controller_opts.devices, 'sdb1')
        self.assertEqual(controller_opts.log_level, 'INFO')
        self.assertEqual(controller_opts.timeout, 10)
        self.assertEqual(controller_opts.bench_clients, [])
        self.assertTrue(controller_opts.containers)

    def test_cli_options(self):
        controller_opts, container_opts, del_opts = self.run_main(
            [
                '--auth', 'http://some_url/auth/v1.0',
                '-U', 'other:user',
                '--key', 'my_key',
                '--bench-clients', '1.2.3.4:1234',
                '--url', 'http://storage.url/v1/AUTH_user',
                '--get-concurrency', '9',
                '--put-concurrency', '8',
                '--delete-concurrency', '7',
                '--object-size', '999',
                '--lower-object-size', '1',
                '--num-objects', '5000',
                '--num-gets', '4000',
                '--num-containers', '4',
                '--container-name', 'foo',
                '-x',
                '--auth_version', '2.0',
                '--delay', '10',
                '--policy-name', 'gold'])
        self.assertFalse(controller_opts.saio)
        self.assertEqual(controller_opts.auth, 'http://some_url/auth/v1.0')
        self.assertEqual(controller_opts.user, 'other:user')
        self.assertEqual(controller_opts.key, 'my_key')
        self.assertEqual(controller_opts.bench_clients, ['1.2.3.4:1234'])
        self.assertEqual(controller_opts.url,
                         'http://storage.url/v1/AUTH_user')
        self.assertEqual(controller_opts.get_concurrency, 9)
        self.assertEqual(controller_opts.put_concurrency, 8)
        self.assertEqual(controller_opts.del_concurrency, 7)
        self.assertEqual(controller_opts.object_size, 999)
        self.assertEqual(controller_opts.lower_object_size, 1)
        self.assertEqual(controller_opts.num_objects, 5000)
        self.assertEqual(controller_opts.num_gets, 4000)
        self.assertEqual(controller_opts.num_containers, 4)
        self.assertEqual(len(controller_opts.containers), 4)
        self.assertEqual([
            c.startswith('foo_') for c in controller_opts.containers
        ], [True] * 4)
        self.assertFalse(controller_opts.delete)
        self.assertEqual(controller_opts.auth_version, '2.0')
        self.assertEqual(controller_opts.delay, 10)
        self.assertEqual(controller_opts.policy_name, 'gold')
        self.assertTrue(controller_opts.use_proxy)
        self.assertEqual(controller_opts.object_sources, '')
        self.assertEqual(controller_opts.account, '')
        self.assertEqual(controller_opts.container_name, mock.ANY)
        self.assertEqual(controller_opts.devices, 'sdb1')
        self.assertEqual(controller_opts.log_level, 'INFO')
        self.assertEqual(controller_opts.timeout, 10)
        self.assertTrue(controller_opts.containers)

    def test_single_container(self):
        controller_opts, container_opts, del_opts = self.run_main([
            '--container-name', 'bar', '--num-containers', '1'])
        self.assertEqual(controller_opts.num_containers, 1)
        self.assertEqual(controller_opts.containers, ['bar'])

    def test_concurrency_overrides_get_put_delete(self):
        controller_opts, container_opts, del_opts = self.run_main(
            [
                '--concurrency', '5',
                '--get-concurrency', '9',
                '--put-concurrency', '8',
                '--delete-concurrency', '7'])
        self.assertEqual(controller_opts.concurrency, 5)
        self.assertEqual(controller_opts.get_concurrency, 5)
        self.assertEqual(controller_opts.put_concurrency, 5)
        self.assertEqual(controller_opts.del_concurrency, 5)
