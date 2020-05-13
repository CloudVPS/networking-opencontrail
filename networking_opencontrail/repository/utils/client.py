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

from networking_opencontrail.repository.utils import tagger

LOG = logging.getLogger(__name__)


# TODO(Ignacy): Convert this class to singleton.
class TFClient(object):
    session = None

    @classmethod
    def connect(cls):
        """Create new session with the contrail API.

        If previously session was created, reuse exising session.
        A special NTF Tag is created as well if doesn't exist.
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

        cls._create_tag()

    @classmethod
    def _create_tag(cls):
        try:
            cls.session.tag_read(fq_name=tagger.identifier_tag().fq_name)
        except vnc_api.NoIdError:
            return cls.session.tag_create(tagger.identifier_tag())

    def read_project(self, uuid=None, fq_name=None):
        """Gets Project with spedified uuid or FQ NAME.

        If certain Project does not exist it returns None value.
        """
        try:
            project = self.session.project_read(id=uuid, fq_name=fq_name)
            return project
        except vnc_api.NoIdError:
            return None

    def list_networks(self, tagged_only=True):
        """Gets the list of Virtual Networks.

        By default it returns only Virtual Networks that were created
        by this client.
        """
        objs = self.session.virtual_networks_list(detail=True)
        if tagged_only:
            return self._filter_tagged_resources(objs)
        return objs

    def read_network(self, uuid=None, fq_name=None):
        """Gets Virtual Network with spedified uuid or FQ NAME.

        If certain Virtual Network does not exist it returns None
        value.
        """
        try:
            return self.session.virtual_network_read(id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def create_network(self, network):
        """Creates Virtual Network with NTF Tag."""
        tagger.assign_to_ntf(network)
        self.session.virtual_network_create(network)

    def update_network(self, network):
        """Updates Virtual Network."""
        self.session.virtual_network_update(network)

    def delete_network(self, uuid=None, fq_name=None):
        """Deletes Virtual Network."""
        self.session.virtual_network_delete(id=uuid, fq_name=fq_name)

    def list_vmis(self, tagged_only=True):
        """Gets the list of Virtual Machine Interfaces.

        By default it returns only Virtual Machine Interfaces that
        were created by this client.
        """
        objs = self.session.virtual_machine_interfaces_list(detail=True)
        if tagged_only:
            return self._filter_tagged_resources(objs)
        return objs

    def read_vmi(self, uuid=None, fq_name=None):
        """Gets Virtual Machine Interface with spedified uuid/FQ NAME.

        If certain Virtual Machine Interface does not exist it returns
        None value.
        """
        try:
            return self.session.virtual_machine_interface_read(
                id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def create_vmi(self, vmi):
        """Creates Virtual Machine Interface with NTF Tag."""
        tagger.assign_to_ntf(vmi)
        self.session.virtual_machine_interface_create(vmi)

    def update_vmi(self, vmi):
        """Updates Virtual Machine Interface."""
        self.session.virtual_machine_interface_update(vmi)

    def delete_vmi(self, uuid=None, fq_name=None):
        """Deletes Virtual Machine Interface."""
        self.session.virtual_machine_interface_delete(id=uuid, fq_name=fq_name)

    def list_vpgs(self, tagged_only=True):
        """Gets the list of Virtual Port Groups.

        By default it returns only Virtual Port Groups that were
        created by this client.
        """
        objs = self.session.virtual_port_groups_list(detail=True)
        if tagged_only:
            return self._filter_tagged_resources(objs)
        return objs

    def read_vpg(self, uuid=None, fq_name=None):
        """Gets Virtual Port Group with spedified uuid or FQ NAME.

        If certain Virtual Port Group does not exist it returns None
        value.
        """
        try:
            return self.session.virtual_port_group_read(
                id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def create_vpg(self, vpg):
        """Creates Virtual Port Group with NTF Tag."""
        tagger.assign_to_ntf(vpg)
        self.session.virtual_port_group_create(vpg)

    def update_vpg(self, vpg):
        """Updates Virtual Port Group."""
        self.session.virtual_port_group_update(vpg)

    def delete_vpg(self, uuid=None, fq_name=None):
        """Deletes Virtual Port Group."""
        self.session.virtual_port_group_delete(id=uuid, fq_name=fq_name)

    def read_port(self, uuid=None, fq_name=None):
        """Gets Port with spedified uuid or FQ NAME.

        If certain Port does not exist it returns None value.
        """
        try:
            return self.session.port_read(
                id=uuid, fq_name=fq_name
            )
        except vnc_api.NoIdError:
            return None

    def read_physical_interface(self, uuid=None, fq_name=None):
        """Gets Physical Interface with spedified uuid or FQ NAME.

        If certain Physical Interface does not exist it returns None
        value.
        """
        try:
            return self.session.physical_interface_read(
                id=uuid, fq_name=fq_name
            )
        except vnc_api.NoIdError:
            return None

    def read_physical_router(self, uuid=None, fq_name=None):
        """Gets Physical Router with spedified uuid or FQ NAME.

        If certain Physical Router does not exist it returns None
        value.
        """
        try:
            return self.session.physical_router_read(id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def list_physical_routers(self):
        """Gets the list of Physical Routers."""
        return self.session.physical_routers_list(detail=True)

    def read_node(self, uuid=None, fq_name=None):
        """Gets Node with spedified uuid or FQ NAME.

        If certain Node does not exist it returns None value.
        """
        try:
            return self.session.node_read(id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def read_fabric(self, uuid=None, fq_name=None):
        """Gets Fabric with spedified uuid or FQ NAME.

        If certain Fabric does not exist it returns None value.
        """
        try:
            return self.session.fabric_read(id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def read_network_ipam(self, uuid=None, fq_name=None):
        """Gets Network IPAM with spedified uuid or FQ NAME.

        If certain Network IPAM does not exist it returns None value.
        """
        try:
            return self.session.network_ipam_read(id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def create_network_ipam(self, ipam):
        """Creates Network IPAM with NTF Tag."""
        tagger.assign_to_ntf(ipam)
        self.session.network_ipam_create(ipam)

    def read_logical_router(self, uuid=None, fq_name=None):
        """Gets Logical Router with spedified uuid or FQ NAME.

        If certain Logical Router does not exist it returns None
        value.
        """
        try:
            return self.session.logical_router_read(id=uuid, fq_name=fq_name)
        except vnc_api.NoIdError:
            return None

    def create_logical_router(self, router):
        """Creates Logical Router with NTF Tag."""
        tagger.assign_to_ntf(router)
        self.session.logical_router_create(router)

    def update_logical_router(self, router):
        """Updates Logical Router."""
        self.session.logical_router_update(router)

    def delete_logical_router(self, uuid=None, fq_name=None):
        """Deletes Logical Router."""
        self.session.logical_router_delete(id=uuid, fq_name=fq_name)

    def _filter_tagged_resources(self, objs):
        tagged_objs = []
        for o in objs:
            if tagger.belongs_to_ntf(o):
                tagged_objs.append(o)
        return tagged_objs

tf_client = TFClient()
