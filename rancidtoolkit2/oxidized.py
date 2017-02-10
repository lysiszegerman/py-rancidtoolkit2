#!/usr/bin/env python
# Written by Marcus Stoegbauer <ms@man-da.de>
import sys
from collections import namedtuple

import requests
from requests.compat import urljoin
from rancidtoolkit2.rtconfig import RtConfig

Device = namedtuple('Device', ['Hostname', 'Group', 'ConfigType'])


class Oxidized(RtConfig):

    os_to_configtype = {'ios': 'cisco',
                        'junos': 'juniper',
                        'screenos': 'netscreen',
                        'ftos': 'force10'}

    # pylint: disable=super-init-not-called
    def __init__(self, oxidized_url=None):
        if not oxidized_url:
            if sys.platform == "darwin":
                oxidized_url = "http://dazzle.office.man-da.de:8888"
        self.__method = "oxidized"
        self.__base_url = oxidized_url

    def configtype_from_os(self, operating_system):
        """
        Lookup configuration type by device operating system
        :param operating_system:
        :return:
        """
        operating_system = operating_system.lower()
        try:
            return self.os_to_configtype[operating_system]
        except KeyError:
            return operating_system

    def get_all_devices(self):
        """
        Lookup all devices in the Oxidized instance
        :return: dict with fqdn to configtype mapping
        """
        response = requests.get(urljoin(self.__base_url, 'nodes.json'))

        if not response.ok:
            raise LookupError(
                "Error getting nodes list: {reason}".format(
                    reason=response.reason)
            )

        devices = response.json()
        return {
            device['name']: self.configtype_from_os(device['model'])
            for device in devices
        }

    def get_device(self, device_fqdn):
        """
        Fetch group information and return a Device object
        :param device_fqdn: fully-qualified hostname of a device
        :return: Device tuple
        """
        devices = self.get_all_devices()
        for fqdn, configtype in devices.items():
            if not fqdn.startswith(device_fqdn):
                continue

            response = requests.get(
                urljoin(self.__base_url,
                        "/node/show/{}.json".format(fqdn))
            )
            if response.ok:
                data = response.json()
                return Device(Hostname=fqdn,
                              Group=str(data['group']),
                              ConfigType=configtype)
        return None

    def get_config(self, device_fqdn):
        """
        Fetch and return a devices configuration
        :param device_fqdn: fully-qualified hostname of a device
        :return: list of configuration strings, separated by newlines
        """
        device = self.get_device(device_fqdn)
        if not device:
            raise ValueError("Device {} not in Oxidized config".format(
                device_fqdn))

        response = requests.get(urljoin(
            self.__base_url, "/node/fetch/{group}/{host}".format(
                group=device.Group, host=device.Hostname)))
        return [line.rstrip('\n') for line in response.iter_lines(decode_unicode=True)]
