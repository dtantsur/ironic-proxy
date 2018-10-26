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
_CACHE = None


def _imap_unordered(func, items):
    global _POOL
    if _POOL is None:
        _POOL = pool.ThreadPool()
    return _POOL.imap_unordered(func, items)


def _source(group):
    try:
        return conf.groups()[group]
    except IndexError:
        raise common.Error('No conductors in group {group}',
                           group=group or '<default>')


def _find_node(node_id):
    global _CACHE
    if _CACHE is None:
        _CACHE = {}

    node = None
    try:
        # Check if we already know where the node is
        group = _CACHE[node_id]
    except KeyError:
        # Node unknown, let's find it
        LOG.debug('Polling all sources to find node %s', node_id)
        for node, group in _imap_unordered(
                lambda args: (args[1].find_node(node_id), args[0]),
                conf.groups().items()):
            if node is None:
                continue

            LOG.info('Node %s found in group %s',
                     node_id, group or '<default>')
            # Remember where the node is located
            _CACHE[node['uuid']] = group
            break
    else:
        # Node is known, just fetch it
        cli = _source(group)
        node = cli.find_node(node_id)

    if node is None:
        raise common.NotFound('Node {node} was not found', node=node_id)
    return node, group


def _cache_nodes(nodes, group):
    global _CACHE
    if _CACHE is None:
        _CACHE = {}

    for node in nodes:
        if 'uuid' in node:
            LOG.info('Node %s found in group %s',
                     node['uuid'], group or '<default>')
            _CACHE[node['uuid']] = group


def create_node(node):
    group = node.get('conductor_group', '')
    cli = _source(group)
    return cli.create_node(node)


def get_node(node_id):
    return _find_node(node_id)[0]


def list_nodes():
    result = []
    for group, cli in conf.groups().items():
        LOG.debug('Loading nodes from %s', group or '<default>')
        nodes = cli.list_nodes()
        _cache_nodes(nodes, group)
        result.extend(nodes)
    return result


def delete_node(node_id):
    group = _find_node(node_id)[1]
    cli = _source(group)
    cli.delete_node(node_id)
