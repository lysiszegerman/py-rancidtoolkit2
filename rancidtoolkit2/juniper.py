# Written by Marcus Stoegbauer <ms@man-da.de>

"""
Juniper specific parsing of configuration files
"""

import re


def config_from_list(config_list):
    """ reads config file """
    flatconfig = ""
    for line in config_list:
        if line.startswith('#'):
            # skip comments
            continue
        flatconfig += line.replace("## SECRET-DATA", "")

    flatconfig = re.sub(r'/\*.*?\*/', " ", flatconfig)
    flatconfig = re.sub(r'\s+', " ", flatconfig)
    return parse_string(flatconfig + "}")[0]


def parse_string(flatconfig):
    """ recursive parsing of config file """
    configtree = {}
    finished = False
    while not finished:
        match = re.search(r'^(.*?)([\{\}])(.*)$', flatconfig)
        if match:
            parenthesis = match.group(2)
            content = match.group(1)
            flatconfig = match.group(3)
        else:
            raise ValueError('Unmatched configuration string')

        elems = content.split(";")
        if content != "" and parenthesis == "{":
            last_elem = elems.pop()
            last_elem = re.sub(r'^\s*(.*?)\s*$', r'\1', last_elem)
            (configtree[last_elem], flatconfig) = parse_string(flatconfig)
        else:
            finished = True

        for elem in elems:
            if re.match(r'^\s*$', elem):
                continue
            elem = re.sub(r'^\s*(.*?)\s*$', r'\1', elem)
            configtree[elem] = "filled"

    return configtree, flatconfig


def get_section(config, section):
    """
    return config starting from dict section with the desired matches
    """
    configtree = config_from_list(config)
    return get_section_recursive(configtree, section)


def get_section_recursive(configtree, sections):
    """
    parse configtree recursively and return config with the desired
    matches in dict section
    """
    if not sections:
        # no more section matches available, return whole subtree
        return configtree

    ret = {}
    branch = configtree

    current_section = sections[0]
    remaining_sections = sections[1:]

    for key in branch.keys():
        if re.match(current_section, key, flags=re.I):
            # first section matches
            if not isinstance(configtree[key], dict):
                # remaining configtree is only a string, no more matches,
                # just return
                return configtree[key]
            else:
                # else go deeper into tree
                ret.update(get_section_recursive(
                    configtree[key], remaining_sections)
                )
                # if not dict
                # if match
    # for key
    return ret


def discard_empty_sections(configtree):
    """ remove empty sections from configtree """
    ret = dict()
    branchkeys = configtree.keys()
    for key in branchkeys:
        if isinstance(configtree[key], dict):
            # print "+++ section[",key,"] is dict"
            if configtree[key]:
                # print "   +++ and > 0:",configtree[key]
                temp = discard_empty_sections(configtree[key])
                if temp:
                    ret.update({key: temp})
                    # if content in section
                    # if content in section with empty sections
        else:
            ret.update({key: 'filled'})
            # if configtree dict
    # for key
    return ret


def filter_section(configtree, pattern):
    """ filters configtree according to regexp terms in filter and outputs
    only those parts of section that contain values """
    return discard_empty_sections(filter_section_recursive(configtree, pattern))


def filter_section_recursive(configtree, pattern):
    """ filters configtree according to regexp terms in filter and outputs a
    dict of all matched entries """
    ret = dict()
    branchkeys = configtree.keys()
    for key in branchkeys:
        if isinstance(configtree[key], dict):
            # if remaining configtree is actually still a tree
            if re.search(pattern, key):
                # if the current key matches the filter, append remaining
                # configtree to return variable
                ret.update({key: configtree[key]})
            else:
                # else go deeper into tree and process
                ret.update(
                    {key: filter_section_recursive(configtree[key], pattern)})
                # if match
        else:
            if re.search(pattern, key):
                ret.update({key: 'filled'})
                # if configtree match
    # for key
    return ret


def filter_config(config, section, pattern):
    """ get section from config and filter for regexp """
    config_section = get_section(config, section)
    return filter_section(config_section, pattern)


def print_section_recursive(configtree, spaces):
    """prints section recursively"""
    for key in configtree:
        if isinstance(configtree[key], dict):
            print("%s%s%s" % (spaces, key, "{"))
            print_section_recursive(configtree[key], spaces + "   ")
            print("%s%s" % (spaces, "}"))
        else:
            print("%s%s" % (spaces, key + ";"))
            # if configtree dict
            # for key


def print_section(configtree):
    """ prints configtree in a nice way """
    print_section_recursive(configtree, "")


def find_description(configtree):
    """ find description in configtree and return it,
    otherwise return false """
    try:
        for key in configtree.keys():
            # try with quotes first
            result = re.match(r"description \"(.*)\"", key)
            if not result:
                # if that doesn't match, try without
                result = re.match(r"description (.*)", key)
            if result:
                return result.group(1), key
    except AttributeError:
        pass

    return "", None


def get_interfaces(config):
    """ find interfaces and matching descriptions from filename and
    returns a dict interface=>description
    """
    inttree = filter_section(
        get_section(config, ["interfaces"]),
        "description .*"
    )
    ret = dict()
    for interface in inttree:
        intdescr, intdesckey = find_description(inttree[interface])
        if intdescr:
            ret[interface] = intdescr
            inttree[interface].pop(intdesckey)
        # if intdescr
        for unit in inttree[interface]:
            if not re.match(r'inactive: ', unit):
                unitdescr = find_description(inttree[interface][unit])
                unitres = re.match(r'unit ([\d]+)', unit)
                if unitres:
                    ret["{}.{}".format(interface, unitres.group(1))] = unitdescr
                else:
                    ret[interface] = unitdescr
                    # if unit
                    # if not inactive
                    # for unit
    # for interface
    return ret


def find_address(configtree):
    """find description in configtree and return it, otherwise return false"""
    for key in configtree.keys():
        result = re.match("address (.*)", key)
        if result:
            return result.group(1)
    return ""


def get_addresses(config, with_subnetsize=None):
    """ find interfaces and matching ip addresses from filename and returns a
     dict interface=>(ip=>address, ipv6=>address)
    """
    inttree = filter_section(get_section(config, ["interfaces"]), "address .*")
    ret = dict()
    for interface in inttree:
        for unit in inttree[interface].keys():
            if not re.match("inactive: ", unit):
                unittree = inttree[interface][unit]
                unitres = re.match("unit ([0-9]+)", unit)
                if unitres:
                    intret = interface + "." + unitres.group(1)
                else:
                    intret = interface + ".unknownunit"

                if "family inet" in unittree:
                    addr = find_address(unittree['family inet'])
                    if addr:
                        if intret not in ret:
                            ret[intret] = dict()
                        if with_subnetsize:
                            ret[intret].update({'ip': addr.split(" ")[0]})
                        else:
                            ret[intret].update({'ip': addr.split("/")[0]})
                            # if intret
                            # if addr
                # if family inet
                if "family inet6" in unittree:
                    addr = find_address(unittree['family inet6'])
                    if addr:
                        if intret not in ret:
                            ret[intret] = dict()
                        if with_subnetsize:
                            ret[intret].update({'ipv6': addr.split(" ")[0]})
                        else:
                            ret[intret].update({'ipv6': addr.split("/")[0]})
                            # if intret
                            # if addr
                            # if family inet6
                            # if not inactive
                            # for unit
    return ret
