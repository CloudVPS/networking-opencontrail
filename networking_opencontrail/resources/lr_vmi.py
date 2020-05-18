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
from vnc_api import vnc_api


def create(port_id, project, network, router_name):
    name = make_name(network.name, router_name)
    vmi = vnc_api.VirtualMachineInterface(name=name, parent_obj=project)
    vmi.set_uuid(port_id)

    vmi.set_virtual_network(network)

    return vmi


def make_name(network_name, router_name):
    return 'vmi#{}#{}'.format(network_name, router_name)
