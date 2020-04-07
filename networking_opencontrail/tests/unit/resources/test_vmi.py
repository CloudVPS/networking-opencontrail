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
import ddt

from networking_opencontrail.tests import base
from vnc_api import vnc_api

from networking_opencontrail.resources.vmi import create
from networking_opencontrail.resources.vmi import make_name
from networking_opencontrail.resources.vmi import unzip_name
from networking_opencontrail.resources.vmi import validate


PORT_VALID = {
    "device_owner": "compute:test-nova",
    "binding:host_id": "compute-node",
    "network_id": "test-valid-net-id"
}
PORT_INVALID_DEVICE_OWNER = {
    "device_owner": "not-compute:test-nova",
    "binding:host_id": "compute-node",
    "network_id": "test-valid-net-id"
}
PORT_NO_HOST_ID = {
    "device_owner": "compute:test-nova",
    "network_id": "test-valid-net-id"
}
PORT_NO_NETWORK_ID = {
    "device_owner": "compute:test-nova",
    "binding:host_id": "compute-node",
}

NETWORK_VALID = {
    "name": "test-valid-net",
    "id": "test-valid-net-id",
    "provider:segmentation_id": 5,
}
NETWORK_NO_VLAN_ID = {
    "name": "test-net-no-vlan",
    "id": "test-net-no-vlan-id",
}


@ddt.ddt
class VMIResourceTestCase(base.TestCase):
    def test_create(self):
        project = vnc_api.Project(name="project_name")
        project.set_uuid("project-uuid")
        node_name = "compute-node"
        network = vnc_api.VirtualNetwork(name="test-net", parent_obj=project)
        network.set_uuid("test-net-id")

        vmi = create(project, network, node_name, 5)

        self.assertEqual(vmi.name, "vmi#test-net-id#compute-node")
        self.assertEqual(vmi.uuid, "e208b554-1147-38d3-870e-92a22dab524c")
        self.assertEqual(vmi.parent_name, project.name)
        self.assertEqual(
            vmi.virtual_machine_interface_properties.sub_interface_vlan_tag, 5
        )
        self.assertEqual(len(vmi.virtual_network_refs), 1)
        self.assertEqual(vmi.virtual_network_refs[0]["uuid"], "test-net-id")
        self.assertEqual(
            vmi.id_perms,
            vnc_api.IdPermsType(creator=project.uuid, enable=True),
        )

    @ddt.data(
        (PORT_INVALID_DEVICE_OWNER, NETWORK_VALID),
        (PORT_NO_HOST_ID, NETWORK_VALID),
        (PORT_NO_NETWORK_ID, NETWORK_VALID),
        (PORT_VALID, NETWORK_NO_VLAN_ID)
    )
    @ddt.unpack
    def test_validate_error(self, port, network):
        self.assertRaises(ValueError, validate, port, network)

    def test_validate(self):
        self.assertIsNone(validate(PORT_VALID, NETWORK_VALID))

    def test_unzip_name(self):
        expected_network_uuid = 'my_n3twork-id'
        expected_node_name = 'my-n0de'

        vmi_name = make_name(
            expected_network_uuid, expected_node_name)
        network_uuid, node_name = unzip_name(vmi_name)

        self.assertEqual(network_uuid, expected_network_uuid)
        self.assertEqual(node_name, expected_node_name)
