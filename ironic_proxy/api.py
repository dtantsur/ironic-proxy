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
from oslo_log import log
from six.moves.urllib import parse as urlparse

from ironic_proxy import conf


app = flask.Flask('ironic-proxy')
LOG = log.getLogger(__name__)


@app.errorhandler(Exception)
def handle_error(exc):
    code = getattr(exc, 'code', 500)
    if code < 500:
        LOG.debug('Client error %d: %s', exc.code, exc)
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
    return {
        "id": "v1",
        "status": "CURRENT",
        "min_version": "1.1",
        "version": "1.46",
        "links": [{'href': _url(path), 'rel': 'self'}]
    }


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


@app.route('/v1/nodes')
def nodes():
    result = []
    for group, adapter in conf.groups().items():
        LOG.debug('Loading nodes from %s', group or '<default>')
        nodes = adapter.get('/v1/nodes', raise_exc=True)
        result.extend(nodes.json().get('nodes') or ())
    return flask.jsonify(nodes=result)


def main(argv):
    conf.load_config(sys.argv[1:])
    app.run(debug=conf.CONF.api.debug)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
