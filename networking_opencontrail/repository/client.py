# Copyright (c) 2019 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from oslo_config import cfg
from oslo_log import log as logging

from vnc_api import vnc_api

LOG = logging.getLogger(__name__)


class TFClient(object):
    DEFAULT_GLOBAL_CONF = "default-global-system-config"
    ID_PERMS = vnc_api.IdPermsType(
        creator="networking-opencontrail", enable=True)

    session = None

    @classmethod
    def connect(cls):
        """Create new session with the contrail API.

        If previously session was created, reuse exising session.
        """
        if cls.session:
            return

        config = {
            "api_server_host": cfg.CONF.APISERVER.api_server_ip,
            "api_server_port": cfg.CONF.APISERVER.api_server_port,
            "api_server_use_ssl": cfg.CONF.APISERVER.use_ssl,
            "apicertfile": cfg.CONF.APISERVER.certfile,
            "apikeyfile": cfg.CONF.APISERVER.keyfile,
            "apicafile": cfg.CONF.APISERVER.cafile,
            "apiinsecure": cfg.CONF.APISERVER.insecure,
            "auth_type": cfg.CONF.auth_strategy,
            "auth_host": cfg.CONF.keystone_authtoken.auth_host,
            "auth_port": cfg.CONF.keystone_authtoken.auth_port,
            "auth_protocol": cfg.CONF.keystone_authtoken.auth_protocol,
            "tenant_name": cfg.CONF.keystone_authtoken.admin_tenant_name,
            "kscertfile": cfg.CONF.keystone_authtoken.certfile,
            "kskeyfile": cfg.CONF.keystone_authtoken.keyfile,
            "ksinsecure": cfg.CONF.keystone_authtoken.insecure
        }

        session = vnc_api.VncApi(**config)

        cls.session = session

    def read_project(self, uuid=None, fq_name=None):
        try:
            project = self.session.project_read(id=uuid, fq_name=fq_name)
            return project
        except vnc_api.NoIdError:
            return None

    def create_tag(self, tag):
        self.session.tag_create(tag)

    def read_tag(self, uuid=None, fq_name=None):
        try:
            tag = self.session.tag_read(id=uuid, fq_name=fq_name)
            return tag
        except vnc_api.NoIdError:
            return None

    def list_networks(self):
        return self.session.virtual_networks_list(detail=True)

    def read_network(self, network_id):
        try:
            return self.session.virtual_network_read(id=network_id)
        except vnc_api.NoIdError:
            return None

    def create_network(self, network):
        self.session.virtual_network_create(network)

    def update_network(self, network):
        self.session.virtual_network_update(network)

    def delete_network(self, network_id):
        self.session.virtual_network_delete(id=network_id)

    def read_vmi(self, vmi_id):
        try:
            return self.session.virtual_machine_interface_read(id=vmi_id)
        except vnc_api.NoIdError:
            return None

    def create_vmi(self, vmi):
        self.session.virtual_machine_interface_create(vmi)

    def delete_vmi(self, vmi_id):
        self.session.virtual_machine_interface_delete(id=vmi_id)

    def read_vpg(self, vpg_id):
        try:
            return self.session.virtual_port_group_read(id=vpg_id)
        except vnc_api.NoIdError:
            return None

    def update_vpg(self, vpg):
        self.session.virtual_port_group_update(vpg)

    @property
    def connected(self):
        return self.session is not None

tf_client = TFClient()
