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

from keystoneauth1 import loading
from oslo_config import cfg
from oslo_log import log

from ironic_proxy import ironic


CONF = cfg.CONF
LOG = log.getLogger(__name__)
_GROUPS = None

default_opts = [
    cfg.DictOpt('groups',
                default={},
                help='Mapping of conductor groups to source names'),
]

api_opts = [
    cfg.BoolOpt('debug',
                default=False,
                help='Enable API-level debugging (dangerous!)'),
]


opt_group = cfg.OptGroup(name='api',
                         title='Options for the ironic-proxy API service')


def register_opts():
    log.register_options(CONF)
    CONF.register_opts(default_opts)
    CONF.register_group(opt_group)
    CONF.register_opts(api_opts, group=opt_group)


def load_config(argv):
    CONF(argv)
    log.setup(CONF, 'ironic-proxy')
    if not CONF.groups:
        LOG.critical('No groups defined, plese set [DEFAULT]groups')
    for source in CONF.groups.values():
        conf_group = 'group:%s' % source
        loading.register_auth_conf_options(CONF, conf_group)
        loading.register_session_conf_options(CONF, conf_group)
        loading.register_adapter_conf_options(CONF, conf_group)


def _load_adapter(source):
    conf_group = 'group:%s' % source
    auth = loading.load_auth_from_conf_options(CONF, conf_group)
    sess = loading.load_session_from_conf_options(CONF, conf_group)
    return loading.load_adapter_from_conf_options(CONF, conf_group,
                                                  session=sess, auth=auth)


def groups():
    global _GROUPS
    if _GROUPS is None:
        _GROUPS = {'' if group == '_' else group:
                   ironic.Ironic(_load_adapter(source))
                   for group, source in CONF.groups.items()}
        LOG.info('Loaded groups: %s', ', '.join(_GROUPS))
    return _GROUPS


register_opts()
