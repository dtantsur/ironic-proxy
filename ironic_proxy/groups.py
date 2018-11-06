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

import flask
from oslo_log import log

from ironic_proxy import common
from ironic_proxy import conf


LOG = log.getLogger(__name__)
_POOL = None
_CACHE = None
_MVERSIONS = None


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

        # NOTE(dtantsur): we're using threads, so flask.request won't be
        # available. Pass the microversion explicitly.
        microversion = getattr(flask.request, 'microversion', None)

        def _find(args):
            group, cli = args
            try:
                node = cli.get_node(node_id, microversion=microversion)
            except Exception:
                node = None
            return node, group

        for node, group in _imap_unordered(_find, conf.groups().items()):
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
        node = cli.get_node(node_id)

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


def microversions():
    global _MVERSIONS
    if _MVERSIONS is None:
        curr_min = (1, 1)
        curr_max = (1, 999)
        for minv, maxv in _imap_unordered(
                lambda cli: cli.get_microversions(),
                conf.groups().values()):
            curr_min = max(curr_min, minv)
            curr_max = min(curr_max, maxv)
        LOG.info('Will support microversion range %s to %s',
                 curr_min, curr_max)
        _MVERSIONS = curr_min, curr_max
    return _MVERSIONS


def create_node(node):
    group = node.get('conductor_group', '')
    cli = _source(group)
    return cli.create_node(node)


def get_node(node_id):
    return _find_node(node_id)[0]


def list_nodes(params=None):
    if params is None:
        params = flask.request.args
    result = []
    for group, cli in conf.groups().items():
        LOG.debug('Loading nodes from %s', group or '<default>')
        nodes = cli.list_nodes(params=params)
        _cache_nodes(nodes, group)
        result.extend(nodes)
    return result


def proxy_request(node_id, url=None, method=None, params=None, body=None,
                  json_response=True):
    group = _find_node(node_id)[1]
    cli = _source(group)

    if url is None:
        url = flask.request.path
    if method is None:
        method = flask.request.method
    if params is None:
        params = flask.request.args
    if body is None:
        body = flask.request.get_json(force=True, silent=True)

    resp = cli.request(url, method, params=params, json=body)
    if json_response:
        return resp.json()
