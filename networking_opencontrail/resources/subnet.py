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


def create(q_subnet):
    cidr = IPNetwork(q_subnet["cidr"])
    pfx = str(cidr.network)
    pfx_len = int(cidr.prefixlen)
    default_gw = q_subnet["gateway_ip"]
    sn_name = q_subnet.get("name")
    subnet_id = q_subnet["id"]

    return vnc_api.IpamSubnetType(
        subnet=vnc_api.SubnetType(pfx, pfx_len),
        default_gateway=default_gw,
        subnet_name=sn_name,
        subnet_uuid=subnet_id,
    )
