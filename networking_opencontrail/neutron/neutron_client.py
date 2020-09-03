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

from neutron_lib.plugins import constants as plugin_constants
from neutron_lib.plugins import directory


def list_ports(context, fields=None, filters=None):
    core_plugin = directory.get_plugin()
    ports = core_plugin.get_ports(context, fields=fields, filters=filters)
    return ports


def list_networks(context):
    core_plugin = directory.get_plugin()
    networks = core_plugin.get_networks(context)
    return networks


def list_router_interfaces(context):
    filters = {'device_owner': ['network:router_interface']}
    ports = list_ports(context, filters=filters)
    return ports


def list_routers(context):
    router_plugin = directory.get_plugin(plugin_constants.L3)
    routers = router_plugin.get_routers(context)
    return routers


def list_subnets(context):
    core_plugin = directory.get_plugin()
    return core_plugin.get_subnets(context)


def get_router(context, router_id):
    router_plugin = directory.get_plugin(plugin_constants.L3)
    router = router_plugin.get_router(context, router_id)
    return router


def get_port(context, port_id):
    core_plugin = directory.get_plugin()
    return core_plugin.get_port(context, port_id)


def get_provider(context, flavor_id):
    flavor_plugin = directory.get_plugin(plugin_constants.FLAVORS)
    provider = flavor_plugin.get_flavor_next_provider(
        context, flavor_id)[0]
    return provider
