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

from six.moves.urllib import parse as urlparse


class Ironic(object):
    """A simple ironic client."""

    def __init__(self, adapter):
        if adapter.service_type is None:
            adapter.service_type = 'baremetal'
        self._adapter = adapter

    def get(self, *args, **kwargs):
        """Issue an HTTP GET request."""
        kwargs.setdefault('raise_exc', True)
        return self._adapter.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """Issue an HTTP POST request."""
        kwargs.setdefault('raise_exc', True)
        return self._adapter.post(*args, **kwargs)

    def create_node(self, node):
        """Create a node."""
        return self.post('/v1/nodes', json=node)

    def get_node(self, node_id):
        """Get a bare metal node."""
        return self.get('/v1/nodes/%s' % urlparse.quote(node_id, safe=''))

    def find_node(self, node):
        """Find a bare metal node or return None."""
        try:
            return self.get_node(node)
        except Exception:
            return None

    def list_nodes(self):
        """List bare metal nodes."""
        return self.get('/v1/nodes').json().get('nodes', [])
