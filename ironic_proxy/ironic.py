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


MIN_VERSION_HEADER = 'X-OpenStack-Ironic-API-Minimum-Version'
MAX_VERSION_HEADER = 'X-OpenStack-Ironic-API-Maximum-Version'


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

    def delete(self, *args, **kwargs):
        """Issue an HTTP DELETE request."""
        kwargs.setdefault('raise_exc', True)
        return self._adapter.delete(*args, **kwargs)

    def get_microversions(self):
        """Get the supported microversions."""
        resp = self.get('/')
        version = resp.json()
        if 'default_version' in version:
            # Unversioned endpoint
            version = version['default_version']
        elif 'version' in version:
            # Versioned endpoint - new style
            version = version['version']
        else:
            # NOTE(dtantsur): old ironic did not expose the microversions
            # properly in the versioned endpoint response.
            version = {
                'version': resp.headers.get(MAX_VERSION_HEADER),
                'min_version': resp.headers.get(MIN_VERSION_HEADER),
            }

        max_version = version.get('version')
        min_version = version.get('min_version')
        if not max_version or not min_version:
            return (1, 1), (1, 1)

        try:
            min_version = tuple(int(x) for x in min_version.split('.', 1))
            max_version = tuple(int(x) for x in max_version.split('.', 1))
        except Exception as exc:
            raise RuntimeError("Cannot convert string microversions to tuples."
                               " %s: %s" % (exc.__class__.__name__, exc))

        return min_version, max_version

    def create_node(self, node):
        """Create a node."""
        return self.post('/v1/nodes', json=node).json()

    def get_node(self, node_id):
        """Get a bare metal node."""
        return self.get('/v1/nodes/%s' % urlparse.quote(node_id,
                                                        safe='')).json()

    def find_node(self, node):
        """Find a bare metal node or return None."""
        try:
            return self.get_node(node)
        except Exception:
            return None

    def list_nodes(self):
        """List bare metal nodes."""
        return self.get('/v1/nodes').json().get('nodes', [])

    def delete_node(self, node_id):
        """Delete a node."""
        self.delete('/v1/nodes/%s' % urlparse.quote(node_id, safe=''))
