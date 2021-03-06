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

import sys

import flask
from keystonemiddleware import auth_token
from oslo_log import log
from six.moves.urllib import parse as urlparse

from ironic_proxy import common
from ironic_proxy import conf
from ironic_proxy import groups
from ironic_proxy import ironic


app = flask.Flask('ironic-proxy')
app.url_map.strict_slashes = False
LOG = log.getLogger(__name__)


@app.errorhandler(Exception)
def handle_error(exc):
    code = getattr(exc, 'code', getattr(exc, 'http_status', 500))
    if code < 500:
        LOG.debug('Client error %d: %s', code, exc)
        body = {
            'faultstring': str(exc),
            'faultcode': 'Client',
            'debuginfo': None,
        }
    else:
        LOG.exception('Internal server error')
        body = {
            'faultstring': 'Internal server error',
            'faultcode': 'Server',
            'debuginfo': None,
        }

    resp = flask.jsonify(error_message=body)
    resp.status_code = code
    return resp


def _url(path):
    return urlparse.urljoin(flask.request.script_root, path)


def _api_version(path):
    minv, maxv = groups.microversions()
    return {
        "id": "v1",
        "status": "CURRENT",
        "min_version": "%d.%d" % minv,
        "version": "%d.%d" % maxv,
        "links": [{'href': _url(path), 'rel': 'self'}]
    }


@app.before_request
def check_auth():
    if flask.request.path.rstrip('/') in ('', '/v1'):
        return

    if conf.CONF.api.auth_strategy == 'none':
        return

    if flask.request.headers.get('X-Identity-Status', '').lower() == 'invalid':
        return handle_error(common.Error('Authentication required', code=401))


@app.before_request
def check_microversion():
    if flask.request.path == '/':
        return

    mversion = flask.request.headers.get(ironic.VERSION_HEADER)
    if not mversion:
        return

    try:
        mversion = tuple(int(x) for x in mversion.split('.', 1))
    except Exception:
        LOG.debug('Invalid microversion requested: %s',
                  mversion, exc_info=True)
        return handle_error(common.Error('Invalid microversion requested'))

    minv, maxv = groups.microversions()
    if mversion < minv or mversion > maxv:
        return handle_error(common.Error(
            'Incompatible microversion: %s not between %s and %s' %
            (mversion, minv, maxv), code=406))

    flask.request.microversion = mversion


@app.after_request
def report_microversions(resp):
    if flask.request.path == '/':
        return resp

    minv, maxv = groups.microversions()
    resp.headers.add(ironic.MIN_VERSION_HEADER, "%s.%s" % minv)
    resp.headers.add(ironic.MAX_VERSION_HEADER, "%s.%s" % maxv)
    return resp


@app.route('/')
def root():
    v1 = _api_version('v1')
    return flask.jsonify(
        default_version=v1,
        versions=[v1],
    )


@app.route('/v1')
def versioned_root():
    v1 = _api_version('')
    return flask.jsonify(id=v1['id'], version=v1)


@app.route('/v1/nodes', methods=['GET', 'POST'])
def nodes():
    if flask.request.method == 'GET':
        nodes = groups.list_nodes()
        return flask.jsonify(nodes=nodes)
    else:
        body = flask.request.get_json(force=True)
        node = groups.create_node(body)
        return flask.jsonify(node)


@app.route('/v1/nodes/<node>', methods=['GET', 'PATCH', 'DELETE'])
def node(node):
    if flask.request.method == 'GET':
        if node == 'detail':
            params = dict(flask.request.args, detail=True)
            nodes = groups.list_nodes(params)
            return flask.jsonify(nodes=nodes)

        result = groups.get_node(node)
        if result is None:
            raise common.NotFound("Node {node} was not found", node=node)

        return flask.jsonify(result)
    else:
        has_body = flask.request.method == 'PATCH'
        body = groups.proxy_request(node, json_response=has_body)
        if body:
            return flask.jsonify(body)
        else:
            return '', 204


@app.route('/v1/nodes/<node>/<path:path>',
           methods=['GET', 'PUT', 'POST', 'DELETE'])
def node_action(node, path):
    has_body = flask.request.method == 'GET'
    body = groups.proxy_request(node, json_response=has_body)
    if body:
        return flask.jsonify(body)
    else:
        return '', 204


def init(argv):
    conf.load_config(sys.argv[1:])
    if conf.CONF.api.auth_strategy == 'keystone':
        app.wsgi_app = auth_token.AuthProtocol(app.wsgi_app,
                                               {'delay_auth_decision': True})


def main(argv):
    init(argv)
    app.run(debug=conf.CONF.api.debug)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
