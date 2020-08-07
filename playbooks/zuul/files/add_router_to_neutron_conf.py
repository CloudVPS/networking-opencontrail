#!/usr/bin/env python3

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

# This file is a workaround for adding L3RouterPlugin to service plugins.
# Right now CI neutron configuration file contains opencontrail-router
# which is an alias to different plugin. After changing this to
# L3RouterPlugin this script can be removed.

import configparser


def remove_leading_ending_whitespaces(values):
    for i in range(len(values)):
        values[i] = values[i].strip()


FILENAME = "/etc/neutron/neutron.conf"

DEFAULT_SECTION = "DEFAULT"
PLUGINS_KEY = "service_plugins"
ROUTER_PLUGIN = "neutron.services.l3_router.l3_router_plugin.L3RouterPlugin"
CONTRAIL_ROUTER_PLUGIN = "opencontrail-router"

LIST_DELIMETER = ","

parser = configparser.ConfigParser()

parser.read(FILENAME)

if PLUGINS_KEY in parser[DEFAULT_SECTION]:
    plugins = parser[DEFAULT_SECTION][PLUGINS_KEY].split(LIST_DELIMETER)
    remove_leading_ending_whitespaces(plugins)
    if ROUTER_PLUGIN not in plugins:
        plugins.append(ROUTER_PLUGIN)
    if CONTRAIL_ROUTER_PLUGIN in plugins:
        plugins.remove(CONTRAIL_ROUTER_PLUGIN)
    parser[DEFAULT_SECTION][PLUGINS_KEY] = LIST_DELIMETER.join(plugins)
else:
    parser[DEFAULT_SECTION][PLUGINS_KEY] = ROUTER_PLUGIN

with open(FILENAME, 'w') as inifile:
        parser.write(inifile)
