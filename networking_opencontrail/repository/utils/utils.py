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

import uuid

from oslo_log import log as logging

from networking_opencontrail.repository.utils.client import tf_client
from networking_opencontrail.repository.utils.tagger import verify_data_port

LOG = logging.getLogger(__name__)


def request_project(q_object):
    project_id = str(uuid.UUID(q_object['tenant_id']))
    project = tf_client.read_project(uuid=project_id)
    return project


def request_network(q_object):
    network_id = q_object['network_id']
    network = tf_client.read_network(uuid=network_id)
    return network


def request_node_from_host(host_id):
    node_fq_name = [
        'default-global-system-config',
        host_id
    ]
    node = tf_client.read_node(fq_name=node_fq_name)
    return node


def request_node(q_object):
    host_id = q_object['binding:host_id']
    node = request_node_from_host(host_id)
    return node


def request_ports_from_node(node):
    port_refs = node.get_ports()

    ports = []
    for port_ref in port_refs:
        port_uuid = port_ref['uuid']
        port = tf_client.read_port(uuid=port_uuid)
        if verify_data_port(port):
            ports.append(port)

    return ports


def request_physical_interfaces_from_port(port):
    physical_interface_refs = port.get_physical_interface_back_refs()

    physical_interfaces = []
    for physical_interface_ref in physical_interface_refs:
        physical_interface_uuid = physical_interface_ref['uuid']
        physical_interface = tf_client.read_physical_interface(
            uuid=physical_interface_uuid)
        physical_interfaces.append(physical_interface)

    return physical_interfaces


def request_physical_interfaces_from_ports(ports):
    physical_interfaces = []
    for port in ports:
        port_physical_interfaces = request_physical_interfaces_from_port(port)
        physical_interfaces.extend(port_physical_interfaces)

    return list(set(physical_interfaces))  # delete repetitions


def request_physical_interfaces_from_node(node):
    ports = request_ports_from_node(node)
    physical_interfaces = request_physical_interfaces_from_ports(ports)

    return physical_interfaces


def request_fabric_from_physical_interface(physical_interface):
    physical_router_fq_name = physical_interface.fq_name[:-1]
    physical_router = tf_client.read_physical_router(
        fq_name=physical_router_fq_name)
    fabric_refs = physical_router.fabric_refs
    if not fabric_refs:
        return None

    fabric_ref = fabric_refs[0]
    fabric_uuid = fabric_ref['uuid']
    fabric = tf_client.read_fabric(uuid=fabric_uuid)

    return fabric


def request_fabric_from_node(node):
    ports = request_ports_from_node(node)
    if not ports:
        return None

    port = ports[0]
    physical_interfaces = request_physical_interfaces_from_port(port)
    if not physical_interfaces:
        return None

    physical_interface = physical_interfaces[0]
    fabric = request_fabric_from_physical_interface(physical_interface)

    return fabric
