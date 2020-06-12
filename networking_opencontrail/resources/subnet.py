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

from netaddr import IPNetwork
from vnc_api import vnc_api

DHCP_OPTION = '6'


def create(q_subnet):
    """Create subnet with properties"""
    cidr = IPNetwork(q_subnet["cidr"])
    pfx = str(cidr.network)
    pfx_len = int(cidr.prefixlen)
    default_gw = q_subnet["gateway_ip"]
    sn_name = q_subnet.get("name")
    subnet_id = q_subnet["id"]
    dhcp_config = q_subnet.get("enable_dhcp")
    allocation_pools = q_subnet.get("allocation_pools")
    dns_nameservers = q_subnet.get("dns_nameservers")
    dhcp_option_list = get_dhcp_option_list(dns_nameservers)
    host_routes_config = q_subnet.get("host_routes")
    host_routes = get_host_routes(host_routes_config)
    return vnc_api.IpamSubnetType(
        subnet=vnc_api.SubnetType(pfx, pfx_len),
        default_gateway=default_gw,
        subnet_name=sn_name,
        subnet_uuid=subnet_id,
        enable_dhcp=dhcp_config,
        allocation_pools=allocation_pools,
        addr_from_start=False,
        dhcp_option_list=dhcp_option_list,
        host_routes=host_routes,
        dns_nameservers=None
    )


def get_dhcp_option_type(dns_servers):
    """Get and return DHCP option type"""
    return vnc_api.DhcpOptionType(dhcp_option_name=DHCP_OPTION,
                                  dhcp_option_value=dns_servers)


def get_dhcp_option_list(dns_nameservers):
    """Get and return DHCP options"""
    dhcp_option_list = None
    if dns_nameservers:
        dhcp_options = []
        dns_servers = " ".join(dns_nameservers)
        dhcp_option_type = get_dhcp_option_type(dns_servers)
        dhcp_options.append(dhcp_option_type)
        dhcp_option_list = vnc_api.DhcpOptionsListType(dhcp_options)
    return dhcp_option_list


def get_host_routes_type(host_routes):
    """Get and return host routes type"""
    host_routes_type = []
    for host_route in host_routes:
        prefix = host_route['destination']
        next_hop = host_route['nexthop']
        host_route_type = vnc_api.RouteType(prefix=prefix, next_hop=next_hop)
        host_routes_type.append(host_route_type)
    return host_routes_type


def get_host_routes(host_routes_config):
    """Get and return host routes"""
    host_route_type = get_host_routes_type(host_routes_config)
    host_routes = None
    if host_route_type:
        host_routes = vnc_api.RouteTableType(host_route_type)
    return host_routes
