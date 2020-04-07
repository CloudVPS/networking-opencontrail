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

from networking_opencontrail.resources import vmi
from networking_opencontrail.resources import vpg
from networking_opencontrail.tests import base


PORT_NETWORK_1_NODE_1 = {
    "device_owner": "compute:test-nova",
    "binding:host_id": "test-node-1",
    "network_id": "test-network-1-id",
}
PORT_NETWORK_2_NODE_1 = {
    "device_owner": "compute:test-nova",
    "binding:host_id": "test-node-1",
    "network_id": "test-network-2-id",
}
PORT_NETWORK_1_NODE_2 = {
    "device_owner": "compute:test-nova",
    "binding:host_id": "test-node-2",
    "network_id": "test-network-1-id",
}
PORT_NETWORK_2_NODE_2 = {
    "device_owner": "compute:test-nova",
    "binding:host_id": "test-node-2",
    "network_id": "test-network-2-id",
}

NETWORK_1 = {
    "name": "test-network-1",
    "id": "test-network-1-id",
    "provider:segmentation_id": 1,
}
NETWORK_2 = {
    "name": "test-network-2",
    "id": "test-network-2-id",
    "provider:segmentation_id": 2,
}


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


class MakeVPGAndVMINamesFromQDataTestCase(base.TestCase):
    """Test cases for VMI and VPG name creation.

    Check if VMI and VPG names are being created properly in the following
    scenarios:
    1. There's one port on one node connected to one virtual network.
    2. There are two ports on the same node connected to different networks.
    3. There are two ports on the same node connected to the same network.
    4. There are two ports on different nodes connected to the same network.
    5. There are two ports on different nodes connected to different networks.
    6. There are two ports on each node connected to two separate networks
        (one node per network).
    7. The port has invalid device owner.
    8. The port has no host ID.
    9. The port has no network ID.
    10. The port has no VLAN ID.
    """
    def test_1_port_1_network_1_node(self):
        q_ports = [
            PORT_NETWORK_1_NODE_1,
        ]
        q_networks = [
            NETWORK_1,
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = [
            vpg.make_name(PORT_NETWORK_1_NODE_1['binding:host_id']),
        ]
        expected_vmis = [
            vmi.make_name(
                NETWORK_1['id'], PORT_NETWORK_1_NODE_1['binding:host_id'],
            )
        ]
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_2_port_2_network_1_node(self):
        q_ports = [
            PORT_NETWORK_1_NODE_1,
            PORT_NETWORK_2_NODE_1,
        ]
        q_networks = [
            NETWORK_1,
            NETWORK_2,
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = [
            vpg.make_name(PORT_NETWORK_1_NODE_1['binding:host_id']),
        ]
        expected_vmis = [
            vmi.make_name(
                NETWORK_1['id'],
                PORT_NETWORK_1_NODE_1['binding:host_id']
            ),
            vmi.make_name(
                NETWORK_2['id'],
                PORT_NETWORK_2_NODE_1['binding:host_id']
            ),
        ]
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_2_port_1_network_1_node(self):
        q_ports = [
            PORT_NETWORK_1_NODE_1,
            PORT_NETWORK_1_NODE_1,
        ]
        q_networks = [
            NETWORK_1,
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = [
            vpg.make_name(PORT_NETWORK_1_NODE_1['binding:host_id']),
        ]
        expected_vmis = [
            vmi.make_name(
                NETWORK_1['id'],
                PORT_NETWORK_1_NODE_1['binding:host_id']
            )
        ]
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_2_port_1_network_2_nodes(self):
        q_ports = [
            PORT_NETWORK_1_NODE_1,
            PORT_NETWORK_1_NODE_2,
        ]
        q_networks = [
            NETWORK_1,
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = [
            vpg.make_name(PORT_NETWORK_1_NODE_1['binding:host_id']),
            vpg.make_name(PORT_NETWORK_1_NODE_2['binding:host_id']),
        ]
        expected_vmis = [
            vmi.make_name(
                NETWORK_1['id'],
                PORT_NETWORK_1_NODE_1['binding:host_id'],
            ),
            vmi.make_name(
                NETWORK_1['id'],
                PORT_NETWORK_1_NODE_2['binding:host_id'],
            )
        ]
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_2_port_2_network_2_nodes(self):
        q_ports = [
            PORT_NETWORK_1_NODE_1,
            PORT_NETWORK_2_NODE_2,
        ]
        q_networks = [
            NETWORK_1,
            NETWORK_2,
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = [
            vpg.make_name(PORT_NETWORK_1_NODE_1['binding:host_id']),
            vpg.make_name(PORT_NETWORK_1_NODE_2['binding:host_id']),
        ]
        expected_vmis = [
            vmi.make_name(
                NETWORK_1['id'],
                PORT_NETWORK_1_NODE_1['binding:host_id'],
            ),
            vmi.make_name(
                NETWORK_2['id'],
                PORT_NETWORK_1_NODE_2['binding:host_id'],
            ),
        ]
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_4_port_2_network_2_nodes(self):
        q_ports = [
            PORT_NETWORK_1_NODE_1,
            PORT_NETWORK_1_NODE_1,
            PORT_NETWORK_2_NODE_2,
            PORT_NETWORK_2_NODE_2,
        ]
        q_networks = [
            NETWORK_1,
            NETWORK_2,
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = [
            vpg.make_name(PORT_NETWORK_1_NODE_1['binding:host_id']),
            vpg.make_name(PORT_NETWORK_1_NODE_2['binding:host_id']),
        ]
        expected_vmis = [
            vmi.make_name(
                NETWORK_1['id'],
                PORT_NETWORK_1_NODE_1['binding:host_id']
            ),
            vmi.make_name(
                NETWORK_2['id'],
                PORT_NETWORK_1_NODE_2['binding:host_id']
            ),
        ]
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_invalid_device_owner(self):
        q_ports = [
            PORT_INVALID_DEVICE_OWNER
        ]
        q_networks = [
            NETWORK_VALID
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = []
        expected_vmis = []
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_no_host_id(self):
        q_ports = [
            PORT_NO_HOST_ID
        ]
        q_networks = [
            NETWORK_VALID
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = []
        expected_vmis = []
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_no_network_id(self):
        q_ports = [
            PORT_NO_NETWORK_ID
        ]
        q_networks = [
            NETWORK_VALID
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = []
        expected_vmis = []
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)

    def test_no_vlan_id(self):
        q_ports = [
            PORT_NETWORK_1_NODE_1
        ]
        q_networks = [
            NETWORK_NO_VLAN_ID
        ]

        vpgs = vpg.make_names_from_q_data(q_ports, q_networks)
        vmis = vmi.make_names_from_q_data(q_ports, q_networks)

        expected_vpgs = []
        expected_vmis = []
        self.assertItemsEqual(vpgs, expected_vpgs)
        self.assertItemsEqual(vmis, expected_vmis)
