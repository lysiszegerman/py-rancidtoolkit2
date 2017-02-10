#!/usr/bin/env python
"""
rancidtoolkit2
by Marcus Stoegbauer <ms@man-da.de>
"""

import re
from rancidtoolkit2 import cisco, juniper


class RtConfig(object):

    __method = ""
    __base_url = ""
    __locations = []
    __rancid_base = ""

    def __init__(self, *kwargs):
        raise NotImplementedError()

    # overwrite with functions from implementations
    def get_all_devices(self):
        raise NotImplementedError()

    def get_device(self, device):
        raise NotImplementedError()

    def get_config(self, device):
        raise NotImplementedError()

    # generic functions, implement here

    def __str__(self):
        return "configuration\nmethod:\t{0}\nbase url:\t{1}\nlocations:\t{2}" \
               "\nrancid base:\t{3}".format(self.__method,
                                            self.__base_url,
                                            str(self.__locations),
                                            self.__rancid_base)

    def filter_active_devices(self, pattern=None):
        devices = self.get_all_devices()
        if isinstance(pattern, dict):
            if 'vendor' in pattern:
                filterdev = devices.copy()
                for dev in devices:
                    if devices[dev].lower() != pattern['vendor'].lower():
                        filterdev.pop(dev)

                devices = filterdev.copy()

            if 'name' in pattern:
                filterdev = devices.copy()
                for dev in devices:
                    if not re.search(pattern['name'], dev):
                        filterdev.pop(dev)

                devices = filterdev.copy()

        else:
            raise TypeError("filter is not a dict")

        return devices.keys()

    def printable_interfaces(self, device):
        intlist = self.get_interface_descriptions(device)

        result = []
        for interface in intlist:
            unit = ""
            unit_match = re.search(r"(\.[0-9]+)$", interface)
            inttemp = interface
            if unit_match:
                unit = unit_match.group(1)
                inttemp = re.sub(r".[0-9]+$", "", interface)

            lastintid_match = re.search(r"^(.*)/([0-9])$", inttemp)
            if lastintid_match:
                intstr = "{0}/{1}".format(lastintid_match.group(1),
                                          lastintid_match.group(2))
            else:
                intstr = inttemp

            if unit:
                intstr += unit

            result.append("{0}: {1}".format(intstr, intlist[interface]))

        result.sort()
        return result

    def get_interface_descriptions(self, device):
        devinfo = self.get_device(device)
        if not devinfo:
            raise LookupError(u"Could not find device {0:s}".format(device))

        devconfig = self.get_config(devinfo.Hostname)
        routertype = devinfo.ConfigType.lower()
        if routertype == 'cisco' or routertype == 'force10':
            return cisco.get_interfaces(devconfig)
        elif routertype == 'juniper':
            return juniper.get_interfaces(devconfig)
        else:
            raise ValueError(
                u"Cannot handle device type {0:s} for device {1:s}.".format(
                    routertype, device))

    def get_interface_addresses(self, device, with_subnetsize=None):
        devinfo = self.get_device(device)
        if not devinfo:
            raise LookupError(u"Could not find device {0:s}".format(device))

        devconfig = self.get_config(devinfo[0])
        routertype = devinfo.ConfigType.lower()
        if routertype == 'cisco' or routertype == 'force10':
            return cisco.get_addresses(devconfig, with_subnetsize)
        elif routertype == 'juniper':
            return juniper.get_addresses(devconfig, with_subnetsize)
        else:
            raise ValueError(
                u"Cannot handle device type {0:s} for device {1:s}.".format(
                    routertype, device))

    def get_interface_vrfs(self, device):
        devinfo = self.get_device(device)
        if not devinfo:
            raise LookupError(u"Could not find device {0:s}".format(device))

        devconfig = self.get_config(devinfo.Hostname)
        routertype = devinfo.ConfigType.lower()
        if routertype == 'cisco' or routertype == 'force10':
            return cisco.get_vrfs(devconfig)  # with_subnetsize
        else:
            raise ValueError(
                u"Cannot handle device type {0:s} for device {1:s}.".format(
                    routertype, device))

    def print_filter_section(self, device, pattern):
        devinfo = self.get_device(device)
        if not devinfo:
            raise LookupError(u"Could not find device {0:s}".format(device))

        devconfig = self.get_config(devinfo.Hostname)
        routertype = devinfo.ConfigType.lower()
        if routertype == 'cisco' or routertype == 'force10':
            sections = cisco.get_section(devconfig, ".* ".join(pattern))
            cisco.print_section(sections)
        elif routertype == 'juniper':
            sections = juniper.get_section(devconfig, pattern)
            juniper.print_section(sections)
        else:
            raise ValueError(
                u"Cannot handle device type {0:s} for device {1:s}.".format(
                    routertype, device))

    def print_section(self, vendor, sectionconfig):
        if vendor in ('cisco', 'force10'):
            cisco.print_section(sectionconfig)
        elif vendor == 'juniper':
            juniper.print_section(sectionconfig)
        else:
            raise ValueError(
                u"Cannot handle device type {0:s}".format(vendor))
