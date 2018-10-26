# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from multiprocessing import pool

from oslo_log import log

from ironic_proxy import common
from ironic_proxy import conf


LOG = log.getLogger(__name__)
_POOL = None


def _imap_unordered(func, items):
    global _POOL
    if _POOL is None:
        _POOL = pool.ThreadPool()
    return _POOL.imap_unordered(func, items)


def create_node(node):
    group = node.get('conductor_group', '')
    try:
        cli = conf.groups()[group]
    except IndexError:
        raise common.Error('No conductors in group {group}',
                           group=group or '<default>')
    return cli.create_node(node)


def get_node(node_id):
    for result in _imap_unordered(lambda cli: cli.find_node(node_id),
                                  conf.groups().values()):
        if result is not None:
            return result


def list_nodes():
    result = []
    for group, cli in conf.groups().items():
        LOG.debug('Loading nodes from %s', group or '<default>')
        result.extend(cli.list_nodes())
    return result
