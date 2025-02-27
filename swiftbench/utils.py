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

import sys
import configparser
from urllib.parse import urlparse
from urllib.request import getproxies, proxy_bypass

# Used when reading config values
TRUE_VALUES = set(('true', '1', 'yes', 'on', 't', 'y'))


# NOTE(chmouel): Imported from swift without the modular directory feature.
def readconf(conf_path, section_name=None, log_name=None, defaults=None,
             raw=False):
    """
    Read config file(s) and return config items as a dict

    :param conf_path: path to config file, or a file-like object
                     (hasattr readline)
    :param section_name: config section to read (will return all sections if
                     not defined)
    :param log_name: name to be used with logging (will use section_name if
                     not defined)
    :param defaults: dict of default values to pre-populate the config with
    :returns: dict of config items
    """
    if defaults is None:
        defaults = {}
    if raw:
        c = configparser.RawConfigParser(defaults)
    else:
        c = configparser.ConfigParser(defaults)
    if hasattr(conf_path, 'readline'):
        # make sure filelike is at the start of the file
        if hasattr(conf_path, "seekable"):
            conf_path.seek(0)
        c.read_file(conf_path)
    else:
        success = c.read(conf_path)
        if not success:
            print("Unable to read config from %s" % conf_path)
            sys.exit(1)
    if section_name:
        if c.has_section(section_name):
            conf = dict(c.items(section_name))
        else:
            print("Unable to find %s config section in %s" %
                  (section_name, conf_path))
            sys.exit(1)
        if "log_name" not in conf:
            if log_name is not None:
                conf['log_name'] = log_name
            else:
                conf['log_name'] = section_name
    else:
        conf = {}
        for s in c.sections():
            conf.update({s: dict(c.items(s))})
        if 'log_name' not in conf:
            conf['log_name'] = log_name
    conf['__file__'] = conf_path
    return conf


def config_true_value(value):
    """
    Returns True if the value is either True or a string in TRUE_VALUES.
    Returns False otherwise.
    """
    return value is True or \
        (isinstance(value, str) and value.lower() in TRUE_VALUES)


def using_http_proxy(url):
    """
    Return True if the url will use HTTP proxy.
    Returns False otherwise.
    """
    up = urlparse(url)
    return up.scheme.lower() in getproxies() and not proxy_bypass(up.netloc)


def get_size_bytes(value):
    """
    Expand suffixes for object sizes.

    For example, '10k' becomes 10240, and '2M' becomes 2097152.
    """
    if not isinstance(value, str):
        raise TypeError
    value = value.strip()
    multiple = {
        'G': 1024 ** 3,
        'M': 1024 ** 2,
        'k': 1024,
    }.get(value[-1])
    if multiple is None:
        return int(value)
    return multiple * int(value[:-1])
