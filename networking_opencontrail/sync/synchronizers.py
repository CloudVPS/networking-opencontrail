# Copyright (c) 2020 OpenStack Foundation
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

from neutron_lib import context
from neutron_lib.plugins import directory
from oslo_log import log as logging

from networking_opencontrail.common import utils
from networking_opencontrail import repository
from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.repository.utils.utils import (
    request_node_from_host)
from networking_opencontrail import resources
from networking_opencontrail.sync.base import OneToOneResourceSynchronizer
from networking_opencontrail.sync.base import ResourceSynchronizer


LOG = logging.getLogger(__name__)


def list_q_ports():
    core_plugin = directory.get_plugin()
    admin_context = context.get_admin_context()
    filters = {'device_owner': ['compute:nova']}
    q_ports = core_plugin.get_ports(admin_context, filters=filters)
    return q_ports


def list_q_networks():
    core_plugin = directory.get_plugin()
    admin_context = context.get_admin_context()
    q_networks = core_plugin.get_networks(admin_context)
    return q_networks


class NetworkSynchronizer(OneToOneResourceSynchronizer):
    """A Network Synchronizer class.

    Provides methods used to synchronize networks.
    """
    LOG_RES_NAME = "Network"

    def _get_tf_resources(self):
        return repository.tf_client.list_networks()

    def _get_neutron_resources(self):
        return self._core_plugin.get_networks(self._context)

    def _create_resource(self, resource):
        repository.network.create(resource)

    def _delete_resource(self, resource_id):
        repository.network.delete({"id": resource_id})

    def _ignore_non_ntf_resource(self, resource):
        return (resource.get_fq_name()[1] == "default-project")

    def _ignore_neutron_resource(self, resource):
        return "_snat_" in resource["name"]


class VPGSynchronizer(ResourceSynchronizer):
    """A Virtual Portgroup Synchronizer class.

    Provides methods used to synchronize Virtual Portgroups (VPGs).
    """
    LOG_RES_NAME = "VPG"

    def synchronize(self):
        raise Exception(
            "Synchronisation should be run through VPGAndVMISynchronizer")

    def calculate_diff(self):
        q_networks = list_q_networks()
        q_ports = list_q_ports()
        vpg_names_from_q_data = \
            resources.vpg.make_names_from_q_data(q_ports, q_networks)

        vpgs = repository.tf_client.list_vpgs()
        vpg_names_from_tf_data = self._make_vpg_names_from_tf_data(vpgs)

        vpg_names_to_create = vpg_names_from_q_data - vpg_names_from_tf_data
        vpg_names_to_delete = vpg_names_from_tf_data - vpg_names_from_q_data

        return vpg_names_to_create, vpg_names_to_delete

    @staticmethod
    def _make_vpg_names_from_tf_data(vpgs):
        return set(vpg.name for vpg in vpgs if tagger.belongs_to_ntf(vpg))

    def create_vpgs_in_tf(self, vpg_names):
        for vpg_name in vpg_names:
            self._create_vpg_in_tf(vpg_name)

    @staticmethod
    def delete_vpgs_from_tf(vpg_names):
        for vpg_name in vpg_names:
            vpg_uuid = utils.make_uuid(vpg_name)

            vpg = repository.tf_client.read_vpg(uuid=vpg_uuid)
            if vpg is None:
                LOG.debug("Couldn't delete VPG %s - not found", vpg_uuid)
                return

            repository.tf_client.delete_vpg(uuid=vpg_uuid)

    @staticmethod
    def _create_vpg_in_tf(vpg_name):
        node_name = resources.vpg.unzip_name(vpg_name)
        node = request_node_from_host(node_name)

        vpg = repository.vpg.create_from_node(node)
        VPGSynchronizer._attach_existing_vmis(vpg)

    @staticmethod
    def _attach_existing_vmis(vpg):
        vmis = repository.tf_client.list_vmis()
        node_name = resources.vpg.unzip_name(vpg.name)

        for vmi in vmis:
            _, vmi_node_name = resources.vmi.unzip_name(vmi.name)
            if vmi_node_name == node_name:
                vpg.add_virtual_machine_interface(vmi)

        repository.tf_client.update_vpg(vpg)


class VMISynchronizer(ResourceSynchronizer):
    """A Virtual Machine Interface Synchronizer class.

    Provides methods used to synchronize Virtual Machine Interfaces (VMIs).
    """
    LOG_RES_NAME = "VMI"

    def synchronize(self):
        raise Exception(
            "Synchronisation should be run through VPGAndVMISynchronizer")

    def calculate_diff(self):
        q_networks = list_q_networks()
        q_ports = list_q_ports()
        vmi_names_from_q_data = \
            resources.vmi.make_names_from_q_data(q_ports, q_networks)

        vmis = repository.tf_client.list_vmis()
        vmi_names_from_tf_data = self._make_vmi_names_from_tf_data(vmis)

        vmi_names_to_create = vmi_names_from_q_data - vmi_names_from_tf_data
        vmi_names_to_delete = vmi_names_from_tf_data - vmi_names_from_q_data

        return vmi_names_to_create, vmi_names_to_delete

    @staticmethod
    def _make_vmi_names_from_tf_data(vmis):
        return set(vmi.name for vmi in vmis if tagger.belongs_to_ntf(vmi))

    def create_vmis_in_tf(self, vmi_names):
        for vmi_name in vmi_names:
            self._create_vmi_in_tf(vmi_name)

    @staticmethod
    def delete_vmis_from_tf(vmi_names):
        for vmi_name in vmi_names:
            vmi_uuid = utils.make_uuid(vmi_name)

            vmi = repository.tf_client.read_vmi(uuid=vmi_uuid)
            if vmi is None:
                LOG.debug("Couldn't delete VMI %s - not found", vmi_uuid)
                return

            repository.vmi.detach_from_vpg(vmi)
            repository.tf_client.delete_vmi(uuid=vmi_uuid)

    def _create_vmi_in_tf(self, vmi_name):
        network_uuid, node_name = resources.vmi.unzip_name(vmi_name)

        network = repository.tf_client.read_network(uuid=network_uuid)
        if not network:
            LOG.error("Couldn't find virtual-network for VMI %s", vmi_name)
            return

        project_uuid = network.parent_uuid
        project = repository.tf_client.read_project(uuid=project_uuid)
        if not project:
            LOG.error("Couldn't find project for VMI %s", vmi_name)
            return

        q_networks = self._core_plugin.get_networks(self._context)
        q_network = next((q_network for q_network in q_networks
                          if q_network['id'] == network_uuid), None)
        if not q_network:
            LOG.error("Couldn't find q-network for VMI %s", vmi_name)
            return

        vlan_id = q_network.get('provider:segmentation_id')
        repository.vmi.create_from_tf_data(
            project, network, node_name, vlan_id)


class VPGAndVMISynchronizer(ResourceSynchronizer):
    """A VPG/VMI Synchronizer class.

    Since VPGs and VMIs are closely related in VNC, this class is used to
    conduct the synchronization process of both resource types based on
    information provided by VPG and VMI synchronizers.
    """
    LOG_RES_NAME = "VPGAndVMI"

    def __init__(self):
        self.vpg_synchronizer = VPGSynchronizer()
        self.vmi_synchronizer = VMISynchronizer()

    def synchronize(self):
        vmi_names_to_create, vmi_names_to_delete = \
            self.vmi_synchronizer.calculate_diff()
        vpg_names_to_create, vpg_names_to_delete = \
            self.vpg_synchronizer.calculate_diff()

        self.vpg_synchronizer.create_vpgs_in_tf(vpg_names_to_create)
        self.vmi_synchronizer.create_vmis_in_tf(vmi_names_to_create)

        self.vmi_synchronizer.delete_vmis_from_tf(vmi_names_to_delete)
        self.vpg_synchronizer.delete_vpgs_from_tf(vpg_names_to_delete)


class SubnetSynchronizer(OneToOneResourceSynchronizer):
    """A Subnet Synchronizer class.

    Provides methods used to synchronize subnets.
    """
    LOG_RES_NAME = "Subnet"

    def _get_tf_resources(self):
        """Get a list of subnets used by TF.

        Since there's no way of getting TF subnets directly, this method
        iterates over all virtual networks to create a list of subnets that are
        being used by them.

        :return: list of TF subnets
        :rtype: list
        """
        networks = repository.network.list_all()
        subnets = set()
        for network in networks:
            ipam_refs = network.get_network_ipam_refs()
            if not ipam_refs:
                continue
            vn_subnets = ipam_refs[0]['attr']
            for subnet in vn_subnets.ipam_subnets:
                subnet.get_uuid = subnet.get_subnet_uuid
                subnets.add(subnet)
        return subnets

    def _get_neutron_resources(self):
        return self._core_plugin.get_subnets(self._context)

    def _create_resource(self, resource):
        repository.subnet.create(resource)

    def _delete_resource(self, resource_id):
        repository.subnet.delete({"id": resource_id})
