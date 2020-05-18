# Copyright (c) 2020 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from retrying import retry

from networking_opencontrail.common import utils
from networking_opencontrail import resources
from networking_opencontrail.tests.base import FabricTestCase

from vnc_api import vnc_api


def retry_if_none(result):
    return result is None


def retry_if_not_none(result):
    return result is not None


class SynchronizationTestCase(FabricTestCase):
    def setUp(self):
        super(SynchronizationTestCase, self).setUp()
        self.ml2_tag = self.tf_list(
            'tag', detail=True, fq_names=[["label=__ML2__"]]
        )[0]

    @retry(
        retry_on_result=retry_if_none,
        wait_fixed=1000,
        stop_max_delay=10000
    )
    def _get_recreated_resource(self, res_type, res_id):
        return self.tf_get(res_type, res_id)

    @retry(
        retry_on_result=retry_if_not_none,
        wait_fixed=1000,
        stop_max_delay=10000,
    )
    def _get_redeleted_resource(self, res_type, res_id):
        return self.tf_get(res_type, res_id)


class TestNetworkSynchronization(SynchronizationTestCase):
    """Following scenarios are tested:

    1. Test if network is recreated properly:
        - Create a test network in Neutron.
        - Corresponding network should be created in TF.
        - Delete the network from TF manually.
        - Check if the network was recreated in TF.

    2. Test if stale network is deleted properly:
        - Create a test network in TF.
        - Since it doesn't correspond to any network in Neutron, it will be
            considered 'stale' by the Synchronizer.
        - Check if the network was deleted in TF.
    """
    def test_recreate(self):
        net = {
            "name": "test_vlan_network",
            "provider:network_type": "vlan",
            'provider:segmentation_id': 20,
            "provider:physical_network": self.provider,
            "admin_state_up": True,
        }
        q_net = self.q_create_network(**net)

        self.tf_delete("virtual-network", q_net["network"]["id"])

        self.assertIsNotNone(
            self._get_recreated_resource(
                "virtual-network", q_net["network"]["id"]))

    def test_redelete(self):
        tagged_network = vnc_api.VirtualNetwork(
            name="test_network_1", parent_obj=self.tf_project)
        tagged_network.add_tag(self.ml2_tag)
        tagged_network_uuid = self.tf_create(tagged_network)

        untagged_network = vnc_api.VirtualNetwork(
            name="test_network_2", parent_obj=self.tf_project)
        untagged_network_uuid = self.tf_create(untagged_network)

        self.assertIsNone(
            self._get_redeleted_resource(
                "virtual-network", tagged_network_uuid))
        self.assertIsNotNone(
            self.tf_get("virtual-network", untagged_network_uuid))


class TestVPGSynchronization(SynchronizationTestCase):
    """Following scenarios are tested:

    1. Test if VPG is recreated properly:
        - Create a test port in Neutron.
        - Corresponding VPG should be created in TF.
        - Delete the VPG from TF manually.
        - Check if the VPG was recreated in TF.

    2. Test if stale VPG is deleted properly:
        - Create a test VPG in TF.
        - Since it doesn't correspond to any port in Neutron, it will be
            considered 'stale' by the Synchronizer.
        - Check if the VPG was deleted in TF.
    """
    def test_recreate(self):
        port = {
            "name": "test_fabric_port",
            "network_id": self.test_network["network"]["id"],
            "binding:host_id": "compute-node",
            "device_owner": "compute:nova"
        }
        self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network["network"]["id"],
            'compute-node')
        vmi_uuid = self._find_vmi(vmi_name)
        vmi = self.tf_get("virtual-machine-interface", vmi_uuid)
        vpg = self.tf_get(
            "virtual-port-group",
            vmi.get_virtual_port_group_back_refs()[0]["uuid"])
        vpg_uuid = utils.make_uuid(vpg.name)

        vpg.del_virtual_machine_interface(vmi)
        self.tf_update(vpg)
        self.tf_delete("virtual-port-group", vpg_uuid)

        vpg = self._get_recreated_resource(
            "virtual-port-group", vpg_uuid)
        self.assertIsNotNone(vpg)

        vmi_refs = vpg.get_virtual_machine_interface_refs()
        self.assertEqual(1, len(vmi_refs))
        self.assertEqual(vmi_uuid, vmi_refs[0]["uuid"])

    def test_redelete(self):
        tagged_vpg_name = resources.vpg.make_name('compute-node')
        tagged_vpg = vnc_api.VirtualPortGroup(
            name=tagged_vpg_name, parent_obj=self.tf_project)
        tagged_vpg.add_tag(self.ml2_tag)
        tagged_vpg.set_uuid(utils.make_uuid(tagged_vpg_name))
        self.tf_create(tagged_vpg)

        untagged_vpg_name = resources.vpg.make_name('compute-2')
        untagged_vpg = vnc_api.VirtualPortGroup(
            name=untagged_vpg_name, parent_obj=self.tf_project)
        untagged_vpg.set_uuid(utils.make_uuid(untagged_vpg_name))
        self.tf_create(untagged_vpg)

        self.assertIsNone(
            self._get_redeleted_resource(
                "virtual-port-group", tagged_vpg.uuid))
        self.assertIsNotNone(
            self.tf_get(
                "virtual-port-group", untagged_vpg.uuid))


class TestVMISynchronization(SynchronizationTestCase):
    """Following scenarios are tested:

    1. Test if VMI is recreated properly:
        - Create a test port in Neutron.
        - Corresponding VMI should be created in TF.
        - Delete the VMI from TF manually.
        - Check if the VMI was recreated in TF.

    2. Test if stale VMI is deleted properly:
        - Create a test VMI in TF.
        - Since it doesn't correspond to any port in Neutron, it will be
            considered 'stale' by the Synchronizer.
        - Check if the VMI was deleted in TF.
    """
    def test_recreate(self):
        port = {
            "name": "test_fabric_port",
            "network_id": self.test_network["network"]["id"],
            "binding:host_id": "compute-node",
            "device_owner": "compute:nova"
        }
        self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network["network"]["id"],
            'compute-node')
        vmi_uuid = self._find_vmi(vmi_name)
        vmi = self.tf_get("virtual-machine-interface", vmi_uuid)
        vpg = self.tf_get(
            "virtual-port-group",
            vmi.get_virtual_port_group_back_refs()[0]["uuid"])

        vpg.del_virtual_machine_interface(vmi)
        self.tf_update(vpg)
        self.tf_delete("virtual-machine-interface", vmi_uuid)

        vmi = self._get_recreated_resource(
            "virtual-machine-interface", vmi_uuid)
        self.assertIsNotNone(vmi)
        self._assert_dm_vmi(
            vmi_uuid, self.test_network['network']['id'], self.vlan_id)

    def test_redelete(self):
        network = vnc_api.VirtualNetwork(
            name="test_network", parent_obj=self.tf_project)
        self.tf_create(network)

        tagged_vmi_name = resources.vmi.make_name(network.uuid, 'compute-node')
        tagged_vmi = vnc_api.VirtualMachineInterface(
            name=tagged_vmi_name, parent_obj=self.tf_project)
        tagged_vmi.add_tag(self.ml2_tag)
        tagged_vmi.set_uuid(utils.make_uuid(tagged_vmi_name))
        tagged_vmi.add_virtual_network(network)
        self.tf_create(tagged_vmi)

        untagged_vmi_name = resources.vmi.make_name(network.uuid, 'compute-2')
        untagged_vmi = vnc_api.VirtualMachineInterface(
            name=untagged_vmi_name, parent_obj=self.tf_project)
        untagged_vmi.set_uuid(utils.make_uuid(untagged_vmi_name))
        untagged_vmi.add_virtual_network(network)
        self.tf_create(untagged_vmi)

        self.assertIsNone(
            self._get_redeleted_resource(
                "virtual-machine-interface", tagged_vmi.uuid))
        self.assertIsNotNone(
            self.tf_get(
                "virtual-machine-interface", untagged_vmi.uuid))


class TestVPGAndVMISynchronization(SynchronizationTestCase):
    """Following scenarios are tested:

    1. Test if VPG/VMI pair is recreated properly:
        - Create a test port in Neutron.
        - Corresponding VPG/VMI pair should be created in TF.
        - Delete the VPG/VMI pair from TF manually.
        - Check if the VPG/VMI pair was recreated in TF.

    2. Test if stale VPG/VMI pair is deleted properly:
        - Create a test VPG/VMI pair in TF.
        - Since it doesn't correspond to any port in Neutron, it will be
            considered 'stale' by the Synchronizer.
        - Check if the VPG/VMI pair was deleted in TF.
    """
    def test_recreate(self):
        port = {
            "name": "test_fabric_port",
            "network_id": self.test_network["network"]["id"],
            "binding:host_id": "compute-node",
            "device_owner": "compute:nova"
        }
        self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network["network"]["id"], 'compute-node')
        vmi_uuid = self._find_vmi(vmi_name)
        vmi = self.tf_get("virtual-machine-interface", vmi_uuid)
        vpg = self.tf_get(
            "virtual-port-group",
            vmi.get_virtual_port_group_back_refs()[0]["uuid"])
        vpg_uuid = utils.make_uuid(vpg.name)

        vpg.del_virtual_machine_interface(vmi)
        self.tf_update(vpg)
        self.tf_delete("virtual-port-group", vpg_uuid)
        self.tf_delete("virtual-machine-interface", vmi_uuid)

        vmi = self._get_recreated_resource(
            "virtual-machine-interface", vmi_uuid)
        self.assertIsNotNone(vmi)

        vpg = self._get_recreated_resource(
            "virtual-port-group", vpg_uuid)
        self.assertIsNotNone(vpg)
        vmi_refs = vpg.get_virtual_machine_interface_refs()
        self.assertEqual(1, len(vmi_refs))
        self.assertEqual(vmi_uuid, vmi_refs[0]["uuid"])
        self._assert_dm_vmi(
            vmi_uuid, self.test_network['network']['id'], self.vlan_id)

    def test_redelete(self):
        network = vnc_api.VirtualNetwork(
            name="test_network", parent_obj=self.tf_project)
        self.tf_create(network)

        vmi_name = resources.vmi.make_name(network.uuid, 'compute-node')
        vmi = vnc_api.VirtualMachineInterface(
            name=vmi_name, parent_obj=self.tf_project)
        vmi.add_tag(self.ml2_tag)
        vmi.set_uuid(utils.make_uuid(vmi_name))
        vmi.add_virtual_network(network)
        self.tf_create(vmi)

        vpg_name = resources.vpg.make_name('compute-node')
        vpg = vnc_api.VirtualPortGroup(
            name=vpg_name, parent_obj=self.tf_project)
        vpg.add_tag(self.ml2_tag)
        vpg.add_virtual_machine_interface(vmi)
        vpg.set_uuid(utils.make_uuid(vpg_name))
        self.tf_create(vpg)

        self.assertIsNone(
            self._get_redeleted_resource(
                "virtual-machine-interface", vmi.uuid))
        self.assertIsNone(
            self._get_redeleted_resource("virtual-port-group", vpg.uuid))


class TestSubnetSynchronization(SynchronizationTestCase):
    """Following scenarios are tested:

    1. Test if subnet is recreated properly:
        - Create a test subnet in Neutron.
        - Corresponding subnet should be created in TF.
        - Delete the subnet from TF manually.
        - Check if the subnet was recreated in TF.

    2. Test if stale subnet is deleted properly:
        - Create a test subnet in TF.
        - Since it doesn't correspond to any subnet in Neutron, it will be
            considered 'stale' by the Synchronizer.
        - Check if the subnet was deleted in TF.
    """
    def test_recreate(self):
        subnet = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
        }
        q_subnet = self.q_create_subnet(**subnet)["subnet"]

        self.tf_delete_subnet(q_subnet)

        self.assertIsNotNone(
            self._get_recreated_resource(
                q_subnet["id"], q_subnet["network_id"]
            )
        )

    def test_redelete(self):
        subnet_dict = {
            'name': 'test_subnet',
            'id': '8bf2f40d-9b2c-473d-a980-1356bf1a6a69',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
        }

        network = self.tf_get("virtual-network",
                              self.test_network["network"]["id"])
        subnet = resources.subnet.create(subnet_dict)

        self._create_tf_subnet(network, subnet)

        self.assertIsNone(
            self._get_redeleted_resource(
                subnet_dict["id"], subnet_dict["network_id"]
            )
        )

    def _create_tf_subnet(self, network, subnet):
        ipam = vnc_api.NetworkIpam(parent_obj=self.tf_project)
        self.contrail_api.network_ipam_create(ipam)
        ipam = self.contrail_api.network_ipam_read(
            self.tf_project.fq_name + ["default-network-ipam"])
        vn_subnets = vnc_api.VnSubnetsType([subnet])
        network.add_network_ipam(ipam, vn_subnets)
        self.contrail_api.virtual_network_update(network)

    @retry(
        retry_on_result=retry_if_none,
        wait_fixed=1000,
        stop_max_delay=10000
    )
    def _get_recreated_resource(self, subnet_id, network_id):
        network = self.tf_get("virtual-network", network_id)
        ipam_refs = network.get_network_ipam_refs()
        vn_subnets = ipam_refs[0]['attr']
        for subnet in list(vn_subnets.ipam_subnets):
            if subnet.subnet_uuid == subnet_id:
                return subnet
        return None

    @retry(
        retry_on_result=retry_if_not_none,
        wait_fixed=1000,
        stop_max_delay=10000,
    )
    def _get_redeleted_resource(self, subnet_id, network_id):
        network = self.tf_get("virtual-network", network_id)
        ipam_refs = network.get_network_ipam_refs()
        vn_subnets = ipam_refs[0]['attr']
        for subnet in list(vn_subnets.ipam_subnets):
            if subnet.subnet_uuid == subnet_id:
                return subnet
        return None
