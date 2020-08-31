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

from oslo_log import log as logging

from networking_opencontrail.l3.service_provider import validate_flavor
from networking_opencontrail.neutron import neutron_client
from networking_opencontrail import repository
from networking_opencontrail.repository.utils.client import tf_client
from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.repository.utils.utils import request_node
from networking_opencontrail import resources
from networking_opencontrail.resources import utils
from networking_opencontrail.sync import base

LOG = logging.getLogger(__name__)
L3_SERVICE_PROVIDER_NAME = \
    'networking_opencontrail.l3.service_provider.TFL3ServiceProvider'


class NetworkSynchronizer(base.OneToOneResourceSynchronizer):
    """A Network Synchronizer class.

    Provides methods used to synchronize networks.
    """
    LOG_RES_NAME = "Network"

    def _get_tf_resources(self):
        return repository.tf_client.list_networks()

    def _get_neutron_resources(self):
        return neutron_client.list_networks(self._context)

    def _create_resource(self, resource):
        repository.network.create(resource)

    def _delete_resource(self, resource_id):
        repository.network.delete({"id": resource_id})

    def _ignore_non_ntf_resource(self, resource):
        return (resource.get_fq_name()[1] == "default-project")

    def _ignore_neutron_resource(self, resource):
        return "_snat_" in resource["name"]


class VPGSynchronizer(base.ResourceSynchronizer):
    """A Virtual Portgroup Synchronizer class.

    Provides methods used to synchronize Virtual Portgroups (VPGs).
    """

    LOG_RES_NAME = "VPG"

    def calculate_create_diff(self):
        vpg_names_from_q_data, vpg_names_from_tf_data = \
            self._load_resource_names()
        return vpg_names_from_q_data - vpg_names_from_tf_data

    def calculate_delete_diff(self):
        vpg_names_from_q_data, vpg_names_from_tf_data = \
            self._load_resource_names()
        return vpg_names_from_tf_data - vpg_names_from_q_data

    def _load_resource_names(self):
        q_networks = neutron_client.list_networks(self._context)
        q_ports = neutron_client.list_ports(self._context)
        vpg_names_from_q_data = \
            resources.vpg.make_names_from_q_data(q_ports, q_networks)
        vpgs = repository.tf_client.list_vpgs()
        vpg_names_from_tf_data = self._make_vpg_names_from_tf_data(vpgs)
        return vpg_names_from_q_data, vpg_names_from_tf_data

    def _create_resources(self, to_create):
        for vpg_name in to_create:
            node_name, network_name = resources.vpg.unzip_name(vpg_name)

            node = request_node(node_name)

            if network_name is None:
                repository.vpg.create_for_node(node)
            else:
                repository.vpg.create_for_physical_network(node, network_name)

    def _delete_resources(self, to_delete):
        for vpg_name in to_delete:
            vpg_uuid = resources.utils.make_uuid(vpg_name)
            repository.tf_client.delete_vpg(uuid=vpg_uuid)

    @staticmethod
    def _make_vpg_names_from_tf_data(vpgs):
        return set(vpg.name for vpg in vpgs if tagger.belongs_to_ntf(vpg))


class VMISynchronizer(base.ResourceSynchronizer):
    """A Virtual Machine Interface Synchronizer class.

    Provides methods used to synchronize Virtual Machine Interfaces (VMIs).
    """
    LOG_RES_NAME = "VMI"

    def calculate_create_diff(self):
        vmi_names_from_q_data, vmi_names_from_tf_data = \
            self._load_resource_names()
        return vmi_names_from_q_data - vmi_names_from_tf_data

    def calculate_delete_diff(self):
        vmi_names_from_q_data, vmi_names_from_tf_data = \
            self._load_resource_names()
        return vmi_names_from_tf_data - vmi_names_from_q_data

    def _load_resource_names(self):
        q_networks = neutron_client.list_networks(self._context)
        q_ports = neutron_client.list_ports(self._context)
        vmi_names_from_q_data = \
            resources.vmi.make_names_from_q_data(q_ports, q_networks)
        vmis = [vmi for vmi in repository.tf_client.list_vmis()
                if not vmi.get_logical_router_back_refs()]
        vmi_names_from_tf_data = self._make_vmi_names_from_tf_data(vmis)
        return vmi_names_from_q_data, vmi_names_from_tf_data

    def _create_resources(self, to_create):
        vmi_names = to_create

        nodes = self._get_vmi_nodes(vmi_names)

        if len(vmi_names) > 0 and nodes is None:
            return

        for vmi_name in vmi_names:
            self._create_vmi_in_tf(vmi_name, nodes)

    def _get_vmi_nodes(self, vmi_names):
        nodes = {}
        for vmi_name in vmi_names:
            _, node_name = resources.vmi.unzip_name(vmi_name)
            if node_name in nodes.keys():
                continue

            nodes[node_name] = request_node(node_name)

            if nodes[node_name] is None:
                LOG.error("Couldn't find node %s for VMI %s",
                          node_name, vmi_name)
                return None
        return nodes

    def _delete_resources(self, to_delete):
        for vmi_name in to_delete:
            vmi_uuid = resources.utils.make_uuid(vmi_name)

            vmi = repository.tf_client.read_vmi(uuid=vmi_uuid)
            if vmi is None:
                LOG.debug("Couldn't delete VMI %s - not found", vmi_uuid)
                return

            repository.vmi.detach_from_vpg(vmi)
            repository.tf_client.delete_vmi(uuid=vmi_uuid)

    def _create_vmi_in_tf(self, vmi_name, nodes):
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

        q_networks = neutron_client.list_networks(self._context)
        q_network = next((q_network for q_network in q_networks
                          if q_network['id'] == network_uuid), None)
        if not q_network:
            LOG.error("Couldn't find q-network for VMI %s", vmi_name)
            return

        node = nodes.get(node_name)
        if node is None:
            LOG.error("Couldn't find node %s for VMI %s", node_name, vmi_name)
            return

        if utils.is_sriov_node(node):
            physical_network = q_network[repository.vpg.PHYSICAL_NETWORK]
            vpg_name = resources.vpg.make_name(node_name, physical_network)
        else:
            vpg_name = resources.vpg.make_name(node_name)

        vpg_uuid = utils.make_uuid(vpg_name)
        if tf_client.read_vpg(uuid=vpg_uuid) is None:
            LOG.warning(
                "Couldn't find VPG %s for VMI %s. Skipping",
                vpg_name,
                vmi_name
            )
            return

        vlan_id = q_network.get('provider:segmentation_id')
        repository.vmi.create_from_tf_data(
            project, network, node_name, vlan_id, vpg_name)

    @staticmethod
    def _make_vmi_names_from_tf_data(vmis):
        return set(vmi.name for vmi in vmis if tagger.belongs_to_ntf(vmi))


class SubnetSynchronizer(base.OneToOneResourceSynchronizer):
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
        return neutron_client.list_subnets(self._context)

    def _create_resource(self, resource):
        repository.subnet.create(resource)

    def _delete_resource(self, resource_id):
        repository.subnet.delete({"id": resource_id})


class RouterSynchronizer(base.OneToOneResourceSynchronizer):
    """A Router Synchronizer class.

    Provides methods used to synchronize Logical Routers.
    """
    LOG_RES_NAME = "Logical Router"

    def _get_tf_resources(self):
        return repository.router.list_all()

    def _get_neutron_resources(self):
        return neutron_client.list_routers(self._context)

    def _create_resource(self, resource):
        repository.router.create(resource)

    def _delete_resource(self, resource_id):
        repository.router.delete(resource_id)

    def _ignore_non_ntf_resource(self, resource):
        return not tagger.belongs_to_ntf(resource)

    def _ignore_neutron_resource(self, resource):
        return not validate_flavor(
            L3_SERVICE_PROVIDER_NAME, resource, self._context)


class RouterInterfaceSynchronizer(base.OneToOneResourceSynchronizer):
    """A Router Interface Synchronizer class.

    Provides methods used to synchronize VMIs for LR Interfaces.
    """
    LOG_RES_NAME = "Logical Router Interface"

    def _get_tf_resources(self):
        return repository.tf_client.list_vmis()

    def _get_neutron_resources(self):
        return neutron_client.list_router_interfaces(self._context)

    def _create_resource(self, resource):
        router_id = resource['device_id']
        repository.router.add_interface(router_id, resource)

    def _delete_resource(self, resource_id):
        lr_vmi = repository.tf_client.read_vmi(resource_id)
        router_id = lr_vmi.get_logical_router_back_refs()[0]['uuid']
        repository.router.remove_interface(router_id, resource_id)

    def _ignore_non_ntf_resource(self, resource):
        return (not tagger.belongs_to_ntf(resource)
                or not resource.get_logical_router_back_refs())

    def _ignore_neutron_resource(self, resource):
        router = neutron_client.get_router(
            self._context,
            resource['device_id'],
        )
        return not validate_flavor(
            L3_SERVICE_PROVIDER_NAME, router, self._context)
