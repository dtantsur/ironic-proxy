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

    def list_nodes(self):
        """List bare metal nodes."""
        return self.get('/v1/nodes').json().get('nodes', [])
