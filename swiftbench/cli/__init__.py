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

import argparse
import copy
import logging
import os
import sys
import signal
import uuid

from swiftbench.bench import (BenchController, DistributedBenchController,
                              create_containers, delete_containers)
from swiftbench.utils import readconf, config_true_value, get_size_bytes

# The defaults should be sufficient to run swift-bench on a SAIO
CONF_DEFAULTS = {
    'auth': os.environ.get('ST_AUTH', ''),
    'user': os.environ.get('ST_USER', ''),
    'key': os.environ.get('ST_KEY', ''),
    'auth_version': '1.0',
    'use_proxy': 'yes',
    'put_concurrency': 10,
    'get_concurrency': 10,
    'del_concurrency': 10,
    'object_sources': '',  # set of file contents to read and use for PUTs
    'lower_object_size': 10,  # bounded random size used if these differ
    'upper_object_size': 10,
    'object_size': 1,  # only if not object_sources and lower == upper
    'num_objects': 1000,
    'num_gets': 10000,
    'delete': 'yes',
    'container_name': uuid.uuid4().hex,  # really "container name base"
    'num_containers': 20,
    'url': '',  # used when use_proxy = no or overrides auth X-Storage-Url
    'account': '',  # used when use_proxy = no
    'devices': 'sdb1',  # space-sep list
    'log_level': 'INFO',
    'timeout': 10,
    'delay': 0,
    'bench_clients': [],
}

SAIO_DEFAULTS = {
    'auth': 'http://localhost:8080/auth/v1.0',
    'user': 'test:tester',
    'key': 'testing',
}


def main(argv):
    usage = "usage: %(prog)s [OPTIONS] [CONF_FILE]"
    usage += """\n\nConf file with SAIO defaults:

    [bench]
    auth = http://localhost:8080/auth/v1.0
    user = test:tester
    key = testing
    concurrency = 10
    object_size = 1
    num_objects = 1000
    num_gets = 10000
    delete = yes
    auth_version = 1.0
    policy_name = gold
    """
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('--saio', action='store_true',
                        help='Run benchmark with SAIO defaults')
    parser.add_argument('-A', '--auth',
                        help='URL for obtaining an auth token')
    parser.add_argument('-U', '--user',
                        help='User name for obtaining an auth token')
    parser.add_argument('-K', '--key',
                        help='Key for obtaining an auth token')
    parser.add_argument('-b', '--bench-clients', action='append',
                        metavar='<ip>:<port>',
                        help=('A string of the form "<ip>:<port>" which '
                              'matches the arguments supplied to a '
                              'swift-bench-client process.  This argument '
                              'must be specified once per swift-bench-client '
                              'you want to utilize.'))
    parser.add_argument('-u', '--url',
                        help='Storage URL')
    parser.add_argument('-c', '--concurrency', type=int,
                        help=('Number of concurrent connections to use. For '
                              'finer-grained control, see --get-concurrency, '
                              '--put-concurrency, and --delete-concurrency.'))
    parser.add_argument('--get-concurrency', type=int,
                        help='Number of concurrent GET requests')
    parser.add_argument('--put-concurrency', type=int,
                        help='Number of concurrent PUT requests')
    parser.add_argument('--delete-concurrency', type=int,
                        dest="del_concurrency",
                        help='Number of concurrent DELETE requests')
    parser.add_argument('-s', '--object-size', type=get_size_bytes,
                        help='Size of objects to PUT (in bytes)')
    parser.add_argument('-l', '--lower-object-size', type=get_size_bytes,
                        help=('Lower size of objects (in bytes); '
                              '--object-size will be upper-object-size'))
    parser.add_argument('-n', '--num-objects', type=int,
                        help='Number of objects to PUT')
    parser.add_argument('-g', '--num-gets', type=int,
                        help='Number of GET operations to perform')
    parser.add_argument('-C', '--num-containers', type=int,
                        help='Number of containers to distribute objects '
                             'among')
    parser.add_argument('--container-name',
                        help='Set the base container_name')
    parser.add_argument('-x', '--no-delete',
                        dest='delete', action='store_false',
                        help='If set, will not delete the objects created')
    parser.add_argument('-V', '--auth_version',
                        help='Authentication version')
    parser.add_argument('-d', '--delay', type=int,
                        help='Delay before delete requests in seconds')
    parser.add_argument('-P', '--policy-name',
                        help='Specify which policy to use when creating '
                             'containers')
    parser.add_argument('conf_file', nargs="?",
                        help='config file')

    args = parser.parse_args(argv)
    parser_defaults = copy.deepcopy(CONF_DEFAULTS)
    if args.saio:
        parser_defaults.update(SAIO_DEFAULTS)
    if getattr(args, 'lower_object_size', None):
        if args.object_size <= args.lower_object_size:
            raise ValueError('--lower-object-size (%s) must be '
                             '< --object-size (%s)' %
                             (args.lower_object_size, args.object_size))
        parser_defaults['upper_object_size'] = args.object_size
    if args.conf_file:
        if not os.path.exists(args.conf_file):
            sys.exit("No such conf file: %s" % args.conf_file)
        conf = readconf(args.conf_file, 'bench', log_name='swift-bench',
                        defaults=parser_defaults)
        conf['bench_clients'] = []
    else:
        conf = parser_defaults
    parser.set_defaults(**conf)
    options = parser.parse_args(argv)

    if options.concurrency:
        options.put_concurrency = options.concurrency
        options.get_concurrency = options.concurrency
        options.del_concurrency = options.concurrency
    if options.num_containers == 1:
        options.containers = [options.container_name]
    else:
        options.containers = ['%s_%d' % (options.container_name, i)
                              for i in range(int(options.num_containers))]

    # Turn "yes"/"no"/etc. strings to booleans
    options.use_proxy = config_true_value(options.use_proxy)
    options.delete = config_true_value(options.delete)

    def sigterm(signum, frame):
        sys.exit('Termination signal received.')
    signal.signal(signal.SIGTERM, sigterm)

    logger = logging.getLogger('swift-bench')
    logger.propagate = False
    logger.setLevel({
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL}.get(
            options.log_level.lower(), logging.INFO))
    loghandler = logging.StreamHandler()
    logger.addHandler(loghandler)
    logformat = logging.Formatter(
        'swift-bench %(asctime)s %(levelname)s %(message)s')
    loghandler.setFormatter(logformat)

    if options.use_proxy:
        create_containers(logger, options)

    controller_class = DistributedBenchController if options.bench_clients \
        else BenchController
    controller = controller_class(logger, options)
    controller.run()

    if options.use_proxy and options.delete:
        delete_containers(logger, options)
