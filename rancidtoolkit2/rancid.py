#!/usr/bin/env python
# Written by Marcus Stoegbauer <ms@man-da.de>
import os.path
import re
import sys

from rancidtoolkit2.rtconfig import RtConfig


class Rancid(RtConfig):
    __locations = []
    __rancid_base = ""
    __separator = ":"

    # pylint: disable=super-init-not-called
    def __init__(self, locations=None, rancid_base=""):
        if locations is None and rancid_base == "":
            if sys.platform == "darwin":
                locations = ["darmstadt", "frankfurt", "wiesbaden",
                             "amsterdam", "momus", "test", "hmwk",
                             "tiz"]
                rancid_base = "/Users/lysis/share/rancid"
            else:
                locations = ["darmstadt", "frankfurt", "wiesbaden",
                             "amsterdam", "momus", "tiz"]
                rancid_base = "/home/rancid/var"
        else:
            if isinstance(locations, str):
                locations = [locations]
            if not isinstance(locations, list):
                raise TypeError("locations is not list or string")

            if not isinstance(rancid_base, str):
                raise TypeError("rancid_base is not string")

        self.__method = "rancid"
        self.__locations = locations
        self.__rancid_base = rancid_base
        self.__set_separator()

    def __read_router_database(self):
        """ reads all available router.db files and returns result as list """
        ret = list()
        for loc in self.__locations:
            routerdb = self.__rancid_base + "/" + loc + "/" + "/router.db"
            try:
                hand = open(routerdb)
            except IOError:
                continue
            for line in hand:
                line = line[:-1].lower()
                if not line or line.startswith('#') or re.match(r'^\s+$', line):
                    continue
                ret.append(line + self.__separator + loc)
        return ret

    def __set_separator(self):
        routerdb = "{0}/{1}/router.db".format(self.__rancid_base,
                                              self.__locations[0])
        try:
            hand = open(routerdb)
        except:
            raise Exception("Cannot determine separator, cannot open "+routerdb)

        devs = hand.readlines()
        if devs[1].find(";") > 0:
            self.__separator = ";"

    def get_all_devices(self):
        ret = {}
        devs = self.__read_router_database()
        for dev in devs:
            linesplit = dev.split(self.__separator)
            if len(linesplit) < 2:
                raise ValueError(
                    u"separator `{0:s}` in router.db entry not found:\n{1:s} "
                    u"".format(self.__separator, dev))
            if linesplit[2] == 'up':
                ret.update({linesplit[0]: linesplit[1]})
        return ret

    def get_device(self, device):
        devs = self.__read_router_database()
        for dev in devs:
            if re.match("^"+device, dev):
                ret = dev.split(self.__separator)
                return ret[0:2] + [ret[3]]
        return []

    def get_filename(self, device):
        rancidentry = self.get_device(device)
        if len(rancidentry) == 0:
            raise ValueError(
                u"Could not find device {0:s} in rancid config".format(device))

        filename = "{0}/{1}/configs/{2}".format(self.__rancid_base,
                                                rancidentry[2], rancidentry[0])
        if os.path.isfile(filename):
            with open(filename) as handle:
                firstline = handle.readline()
        else:
            raise IOError(
                u"Filename {0:s} for device {1:s} is no file".format(filename,
                                                                     device))

        typere = re.search(r'RANCID-CONTENT-TYPE: (\w+)', firstline)
        if typere:
            routertype = typere.group(1)
        else:
            raise ValueError(
                "Filename {} is not a saved configuration from rancid".format(
                    filename))
        return filename, routertype

    def get_config(self, device):
        filename = self.get_filename(device)
        with open(filename[0]) as handle:
            lines = [line.rstrip('\n') for line in handle]
        return lines
