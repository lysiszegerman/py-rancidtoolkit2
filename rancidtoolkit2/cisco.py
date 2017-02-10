#!/usr/bin/env python
"""
rancidtoolkit2
by Marcus Stoegbauer <ms@man-da.de>

Cisco specific parsing of configuration files
"""

import re
from collections import defaultdict
from ipaddress import ip_address, ip_network


def get_section(config, _section):
    """returns a list with all configuration within section from filename"""
    result = []
    insecure = False
    spaces = ""
    secret = []

    for line in config:
        if line.startswith('!'):
            continue

        match = re.match(r'^(\s*)' + _section, line, flags=re.I)
        if match:                           # match on section
            if insecure:                    # already in section
                result.append(secret)       # save the old section
            spaces = match.group(1)         # start a new section
            insecure = True
            secret = []

        if insecure:  # already in section
            match = re.match(r"^{}[^\s]".format(spaces), line)
            # not first line of section (which always matches the pattern) and
            if secret and match:
                # match old section is over, save section
                result.append(secret)
                insecure = False
            secret.append(line)  # save to current section

    return result


def filter_section(section, pattern):
    """filters section according to regexp terms in filter and outputs a list
    of all matched entries """
    result = []
    for entry in section:
        secret = []
        for line in entry:
            line = line.lstrip()
            if re.match(pattern, line, re.I):
                secret.append(line)
        result.append(secret)
    return result


def filter_config(config, secstring, pattern):
    """extracts sections secstring from the entire configuration in filename
    and filters against regexp filter returns a list of all matches
    """
    return filter_section(get_section(config, secstring), pattern)


def get_interfaces(config):
    """find interfaces and matching descriptions from filename and return dict
    with interface=>descr """
    interface_config = filter_config(config, 'interface',
                                     '^interface|^description')
    result = dict()
    skip_description = False
    for section in interface_config:
        ifname = ""
        for line in section:
            match = re.match(r"interface (.*)", line)
            if match:
                skip_description = False
                if re.match(r"Vlan", match.group(1)):
                    skip_description = True
                else:
                    ifname = match.group(1)

            if not skip_description:
                match = re.match(r"description (.*)", line)
                if match:
                    result[ifname] = match.group(1)
                else:
                    result[ifname] = ""
    return result


def get_vrfs(config):
    """find interfaces and matching vrfs from filename and return dict
    with interface=>vrf """
    interface_config = filter_config(config, "interface",
                                     "^interface|^(ip )?vrf forwarding")
    result = dict()
    skipvrf = False
    for section in interface_config:
        ifname = ""
        for line in section:
            match = re.match(r"interface (.*)", line)
            if match:
                skipvrf = False
                if 'vlan' in match.group(1).lower():
                    skipvrf = True
                else:
                    ifname = match.group(1)

            if not skipvrf:
                match = re.match(r"(ip )?vrf forwarding (.*)", line)
                if match:
                    result[ifname] = match.group(2)
                else:
                    result[ifname] = ""

    return result


def get_addresses(config, with_subnetsize=None):
    """find ip addresses configured on all interfaces from filename and return
    dict with interface=>(ip=>address, ipv6=>address)"""
    interface_config = filter_config(config, "interface",
                                     "^interface|^ip address|^ipv6 address")
    result = defaultdict(dict)
    for section in interface_config:
        ifname = ""
        for line in section:
            match = re.match(r"interface (.*)", line)
            if match:
                ifname = match.group(1)
            if ifname:
                # FIXME: exclude interfaces with shutdown configured
                match = re.match(r"(ip|ipv6) address (.*)", line)
                if match:
                    af = match.group(1)
                    if af == 'ip' and with_subnetsize:
                        ipaddr = match.group(2).split(" ")[0]
                        if ip_address(ipaddr).version is not 4:
                            continue
                        hostmask = match.group(2).split()[1]
                        address = str(ip_network("{0}/{1}".format(ipaddr,
                                                                  hostmask)))
                    elif af == 'ipv6' and with_subnetsize:
                        address = re.split(r'[ ]', match.group(2))[0]
                    else:
                        address = re.split(r'[/ ]', match.group(2))[0]

                    result[ifname].update({af: address})
    return result


def print_section(section):
    """prints section in a nice way"""
    if isinstance(section, list):
        for line in section:
            print_section(line)
    else:
        print(section)
