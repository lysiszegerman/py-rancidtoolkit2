#!/usr/bin/env python
#
# Written by Marcus Stoegbauer <ms@man-da.de>

"""
Cisco specific parsing of configuration files
"""

import ipaddr
import re

def section(config, section):
    """returns a list with all configuration within section from filename"""
    ret = []
    insec = False
    spaces = ""
    secret = []

    for line in config:
        if re.match("^!", line):
            continue
        reobj = re.match("^(\s*)" + section, line, flags=re.I)
        if reobj:                       # match on section
            if insec:                     # already in section
                ret = ret + [secret]        # save the old section
            spaces = reobj.group(1)       # start a new section
            insec = True
            secret = []
        # if match
        if insec:  # already in section
            secreobj = re.match("^" + spaces + "[^\s]", line)
            # not first line of section (which always matches the pattern) and
            if len(secret) > 0 and secreobj:
                # match old section is over, save section
                ret = ret + [secret]
                insec = False
            secret = secret + [line]      # save to current section
        # if insec
    # for line
    return ret
# section

def filterSection(section, filter):
    """filters section according to regexp terms in filter and outputs a list
    of all matched entries """
    ret = []
    for sec in section:
        secret = []
        for line in sec:
            line = line.lstrip()
            if re.match(filter, line, re.I):
                secret = secret + [line]
        ret = ret + [secret]
    # for sec
    return ret
# filterSection

def filterConfig(config, secstring, filter):
    """extracts sections secstring from the entire configuration in filename
    and filters against regexp filter returns a list of all matches
    """
    return filterSection(section(config, secstring), filter)


def interfaces(config):
    """find interfaces and matching descriptions from filename and return dict
    with interface=>descr """
    parseresult = filterConfig(config, "interface","^interface|^description")
    ret = dict()
    skipdescr = False
    for sec in parseresult:
        intret = ""
        for line in sec:
            reobj = re.match("interface (.*)", line)
            if reobj:
                skipdescr = False
                if re.match("Vlan", reobj.group(1)):
                    skipdescr = True
                else:
                    intret = reobj.group(1)
            # if interface
            if not skipdescr:
                reobj = re.match("description (.*)", line)
                if reobj:
                    ret[intret] = reobj.group(1)
                else:
                    ret[intret] = ""
            # if not skipdescr
        # for line
    # for sec
    return ret
# def interfaces

def vrfs(config):
    """find interfaces and matching vrfs from filename and return dict
    with interface=>vrf """
    parseresult = filterConfig(config, "interface","^interface|^(ip )?vrf forwarding")
    ret = dict()
    skipvrf = False
    for sec in parseresult:
        intret = ""
        for line in sec:
            reobj = re.match("interface (.*)", line)
            if reobj:
                skipvrf = False
                if re.match("Vlan", reobj.group(1)):
                    skipvrf = True
                else:
                    intret = reobj.group(1)
            # if interface
            if not skipvrf:
                reobj = re.match("(ip )?vrf forwarding (.*)", line)
                if reobj:
                    ret[intret] = reobj.group(2)
                else:
                    ret[intret] = ""
            # if not skipvrf
        # for line
    # for sec
    return ret
 # def vrfs

def addresses(config, with_subnetsize=None):
    """find ip addresses configured on all interfaces from filename and return
    dict with interface=>(ip=>address, ipv6=>address)"""
    parseresult = filterConfig(config, "interface","^interface|^ip address|^ipv6 address")
    ret = dict()
    for sec in parseresult:
        intret = ""
        for line in sec:
            reobj = re.match("interface (.*)", line)
            if reobj:
                intret = reobj.group(1)
            if intret:
                # FIXME: exclude interfaces with shutdown configured
                reobj = re.match("(ip|ipv6) address (.*)", line)
                if reobj:
                    afi = reobj.group(1)
                    if afi == "ip" and with_subnetsize:
                        ip = reobj.group(2).split(" ")[0]
                        if ipaddr.IPAddress(ip).version is not 4:
                            continue
                        hostmask = reobj.group(2).split(" ")[1]
                        address = str(ipaddr.IPv4Network(ip + "/" + hostmask))
                    elif afi == "ipv6" and with_subnetsize:
                        address = re.split('[ ]', reobj.group(2))[0]
                    else:
                        address = re.split('[\/ ]', reobj.group(2))[0]
                    if not intret in ret:
                        ret[intret] = dict()
                    ret[intret].update({afi: address})
                # if match
            # if interface
        # for line
    # for sec
    return ret
# def addresses

def printSection(section):
    """prints section in a nice way"""
    if type(section) == list:
        for line in section:
            printSection(line)
    else:
        print section
# def printSection