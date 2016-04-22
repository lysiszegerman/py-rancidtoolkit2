# Written by Marcus Stoegbauer <ms@man-da.de>

"""
Juniper specific parsing of configuration files
"""

import sys
import re


def parseFile(config):
    """ reads config file """
    flatconfig = ""
    for line in config:
        if re.match("^#", line):
            continue
        flatconfig += line
    # for line
    flatconfig = re.sub("\/\*.*?\*\/", " ", flatconfig)
    flatconfig = re.sub("\s+", " ", flatconfig)
    return parseString(flatconfig + "}")[0]
# def parseFile

def parseString(flatconfig):
    """ recursive parsing of config file """
    configtree = {}
    finished = False
    paranthesis = ""
    content = ""
    elems = []
    lastElem = ""
    elem = ""
    while not finished:
        reobj = re.search(r'^(.*?)([\{\}])(.*)$', flatconfig)
        if reobj:
            paranthesis = reobj.group(2)
            content = reobj.group(1)
            flatconfig = reobj.group(3)
        else:
            print "Unmatched configuration string"
            sys.exit(2)
        # if match
        elems = content.split(";")
        if content != "" and paranthesis == "{":
            lastElem = elems.pop()
            lastElem = re.sub(r'^\s*(.*?)\s*$', r'\1', lastElem)
            (configtree[lastElem], flatconfig) = parseString(flatconfig)
        else:
            finished = True
        # if content

        for elem in elems:
            if re.match("^\s*$", elem):
                continue
            elem = re.sub(r'^\s*(.*?)\s*$', r'\1', elem)
            configtree[elem] = "filled"
        # for elem
    # while
    return (configtree, flatconfig)
# def parseString

def section(config, section):
    """ return config starting from dict section with the desired matches """
    configtree = parseFile(config)
    return sectionRecursive(configtree, section)
# def section

def sectionRecursive(configtree, section):
    """ parse configtree recursively and return config with the desired
    matches in dict section """
    ret = dict()
    branchkeys = configtree.keys()
    if len(section) == 0:
        # no more section matches available, return whole subtree
        return configtree
    # if len(section)
    cursection = section[0]
    section = section[1:]

    for key in branchkeys:
        if re.match(cursection, key, flags=re.I):
        # first section matches
            if type(configtree[key]) != dict:
                # remaining configtree is only a string, no more matches, just return
                return configtree[key]
            else:
                # else go deeper into tree
                ret.update(sectionRecursive(configtree[key], section))
            # if not dict
        # if match
    # for key
    return ret
# def sectionRecursive

def removeEmptySections(configtree):
    """ remove empty sections from configtree """
    ret = dict()
    branchkeys = configtree.keys()
    for key in branchkeys:
        if type(configtree[key]) == dict:
            #print "+++ section[",key,"] is dict"
            if len(configtree[key]) > 0:
                #print "   +++ and > 0:",configtree[key]
                temp = removeEmptySections(configtree[key])
                if len(temp) > 0:
                    ret.update({key: temp})
                # if content in section
            # if content in section with empty sections
        else:
            ret.update({key: 'filled'})
        # if configtree dict
    # for key
    return ret
# def removeEmptySection

def filterSection(configtree, filter):
    """ filters configtree according to regexp terms in filter and outputs
    only those parts of section that contain values """
    return removeEmptySections(filterSectionRecursive(configtree, filter))
# def filterSection

def filterSectionRecursive(configtree, filter):
    """ filters configtree according to regexp terms in filter and outputs a
    dict of all matched entries """
    ret = dict()
    branchkeys = configtree.keys()
    for key in branchkeys:
        if type(configtree[key]) == dict:
            # if remaining configtree is actually still a tree
            if re.search(filter, key):
                # if the current key matches the filter, append remaining
                # configtree to return variable
                ret.update({key: configtree[key]})
            else:
                # else go deeper into tree and process
                ret.update({key: filterSectionRecursive(configtree[key],filter)})
            # if match
        else:
            if re.search(filter, key):
                ret.update({key: 'filled'})
        # if configtree match
    # for key
    return ret
# def filterSectionRecursive

def filterConfig(config, secstring, filter):
    """ get section from config and filter for regexp """
    return filterSection(section(config, secstring), filter)
# def filterConfig

def printSectionRecursive(configtree, spaces):
    """prints section recursively"""
    branchkeys = configtree.keys()
    for key in branchkeys:
        if type(configtree[key]) == dict:
            print spaces, key, "{"
            printSectionRecursive(configtree[key], spaces + "   ")
            print spaces, "}"
        else:
            print spaces, key
        # if configtree dict
    # for key
# def printSectionRecursive

def printSection(configtree):
    """ prints configtree in a nice way """
    printSectionRecursive(configtree, "")
# def printSection

def findDescription(configtree):
    """ find description in configtree and return it,
    otherwise return false """
    for key in configtree.keys():
        result = re.match("description (.*)", key)
        if result:
            return result.group(1)
    # for key
    return ""
# def findDescription

def interfaces(config):
    """ find interfaces and matching descriptions from filename and
    returns a dict interface=>description
    """
    inttree = filterSection(section(config, ["interfaces"]), "description .*")
    ret = dict()
    for interface in inttree.keys():
        intdescr = findDescription(inttree[interface])
        if intdescr:
            ret[interface] = re.sub('"', '', intdescr)
            inttree[interface].pop('description ' + intdescr)
        # if intdescr
        for unit in inttree[interface].keys():
            if not re.match("inactive: ", unit):
                unitdescr = findDescription(inttree[interface][unit])
                unitres = re.match("unit ([0-9]+)", unit)
                if unitres:
                    ret[interface + "." + unitres.group(1)] = unitdescr
                else:
                    ret[interface + "." + unitdescr] = unitdescr
                # if unit
            # if not inactive
        # for unit
    # for interface
    return ret
# def interfaces

def findAddress(configtree):
    """find description in configtree and return it, otherwise return false"""
    for key in configtree.keys():
        result = re.match("address (.*)", key)
        if result:
            return result.group(1)
    # for key
    return ""
# def findAddress

def addresses(config, with_subnetsize=None):
    """ find interfaces and matching ip addresses from filename and returns a
     dict interface=>(ip=>address, ipv6=>address)
    """
    inttree = filterSection(section(config, ["interfaces"]), "address .*")
    ret = dict()
    for interface in inttree.keys():
        for unit in inttree[interface].keys():
            if not re.match("inactive: ", unit):
                unittree = inttree[interface][unit]
                unitres = re.match("unit ([0-9]+)", unit)
                intret = ""
                if unitres:
                    intret = interface + "." + unitres.group(1)
                else:
                    intret = interface + ".unknownunit"

                if "family inet" in unittree:
                    addr = findAddress(unittree['family inet'])
                    if addr:
                        if not intret in ret:
                            ret[intret] = dict()
                        if with_subnetsize:
                            ret[intret].update({'ip': addr.split(" ")[0]})
                        else:
                            ret[intret].update({'ip': addr.split("/")[0]})
                        # if intret
                    # if addr
                # if family inet
                if "family inet6" in unittree:
                    addr = findAddress(unittree['family inet6'])
                    if addr:
                        if not intret in ret:
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
    # for interface
    return ret
# def addresses