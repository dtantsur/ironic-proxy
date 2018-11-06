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

import flask
from oslo_log import log
from six.moves.urllib import parse as urlparse


VERSION_HEADER = 'X-OpenStack-Ironic-API-Version'
MIN_VERSION_HEADER = 'X-OpenStack-Ironic-API-Minimum-Version'
MAX_VERSION_HEADER = 'X-OpenStack-Ironic-API-Maximum-Version'
LOG = log.getLogger(__name__)


class Ironic(object):
    """A simple ironic client."""

    def __init__(self, adapter):
        if adapter.service_type is None:
            adapter.service_type = 'baremetal'
        self._adapter = adapter

    def request(self, url, method, microversion=None, **kwargs):
        """Issue a request."""
        kwargs.setdefault('raise_exc', True)
        if url != '/' and not microversion:
            try:
                mversion = getattr(flask.request, 'microversion', None)
            except RuntimeError:
                pass
            else:
                if mversion is not None:
                    microversion = '%s.%s' % mversion
        LOG.debug('%s %s (API version %s) %s', method, url, microversion,
                  kwargs.get('params', {}))
        return self._adapter.request(url, method, microversion=microversion,
                                     **kwargs)

    def get_microversions(self):
        """Get the supported microversions."""
        data = self._adapter.get_endpoint_data()

        if data.min_microversion and data.max_microversion:
            return data.min_microversion, data.max_microversion
        else:
            return (1, 1), (1, 1)

    def create_node(self, node):
        """Create a node."""
        return self.request('/v1/nodes', 'POST', json=node).json()

    def get_node(self, node_id, microversion=None):
        """Get a bare metal node."""
        url = '/v1/nodes/%s' % urlparse.quote(node_id, safe='')
        return self.request(url, 'GET', microversion=microversion).json()

    def list_nodes(self, params=None, microversion=None):
        """List bare metal nodes."""
        params = params or {}
        if params.pop('detail', False):
            url = '/v1/nodes/detail'
        else:
            url = '/v1/nodes'
        return self.request(url, 'GET', params=params,
                            microversion=microversion).json().get('nodes', [])
