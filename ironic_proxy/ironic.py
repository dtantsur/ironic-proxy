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
from six.moves.urllib import parse as urlparse


VERSION_HEADER = 'X-OpenStack-Ironic-API-Version'
MIN_VERSION_HEADER = 'X-OpenStack-Ironic-API-Minimum-Version'
MAX_VERSION_HEADER = 'X-OpenStack-Ironic-API-Maximum-Version'


class Ironic(object):
    """A simple ironic client."""

    def __init__(self, adapter):
        if adapter.service_type is None:
            adapter.service_type = 'baremetal'
        self._adapter = adapter

    def request(self, url, *args, **kwargs):
        """Issue a request."""
        kwargs.setdefault('raise_exc', True)
        if url != '/':
            headers = kwargs.setdefault('headers', {})
            try:
                mversion = getattr(flask.request, 'microversion', None)
            except RuntimeError:
                pass
            else:
                if mversion is not None:
                    headers.setdefault(VERSION_HEADER, '%s.%s' % mversion)
        return self._adapter.request(url, *args, **kwargs)

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

    def get_node(self, node_id):
        """Get a bare metal node."""
        url = '/v1/nodes/%s' % urlparse.quote(node_id, safe='')
        return self.request(url, 'GET').json()

    def find_node(self, node):
        """Find a bare metal node or return None."""
        try:
            return self.get_node(node)
        except Exception:
            return None

    def list_nodes(self):
        """List bare metal nodes."""
        return self.request('/v1/nodes', 'GET').json().get('nodes', [])

    def delete_node(self, node_id):
        """Delete a node."""
        url = '/v1/nodes/%s' % urlparse.quote(node_id, safe='')
        self.request(url, 'DELETE')
