# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 29 May 2018
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

from . import mks_kjl
from . import sunpower
from . import lakeshore


def allCommands(device=None):
    """
    Set of specific command strings valid for specific devices.
    Specifically, these are good for:

    MKS (or Kurt J. Lesker) vacuum pressure transducers: 972B
    Sunpower CryoTel-style coolers
    Lake Shore 325, 218

    cset should be a dictionary mapping a semi-readable key to the
    actual serial command for the particular device.
    Parsing the result occurs elsewhere.

    The command terminator is *returned* and needs to be combined with
    the values in cset before use; that allows somewhat easier adjustments
    of commands that pull double-duty, such as 'SET TTARGET' for the Sunpower
    Cryotel units as well as the Lake Shore devices.
    """
    # Because I'm paranoid
    device = device.lower()

    if device == "vactransducer_mks972b":
        cset, term = mks_kjl.allCommands(device)

    elif device in ["sunpowergen1", "sunpowergen2"]:
        cset, term = sunpower.allCommands(device)

    elif device in ["lakeshore218", "lakeshore325"]:
        cset, term = lakeshore.allCommands(device)

    else:
        print("INVALID DEVICE: %s" % (device))

    return cset, term


def defaultQueryCommands(device=None):
    """
    Downselect from allCommands to a set of specific command strings
    valid for specific devices. Specifically, these are good for:

    MKS (or Kurt J. Lesker) vacuum pressure transducers: 972B
    Sunpower CryoTel-style coolers
    Lake Shore 325, 218

    cset should be a dictionary mapping a readable description of a param
    to the actual serial command needed to get it.  Parsing the result
    occurs elsewhere.
    """

    if device == "vactransducer_mks972b":
        cset = mks_kjl.defaultQueries(device)
    elif device in ['sunpowergen1', 'sunpowergen2']:
        cset = sunpower.defaultQueries(device)
    elif device in ['lakeshore218', 'lakeshore325']:
        cset = lakeshore.defaultQueries(device)
    else:
        print("INVALID DEVICE: %s" % (device))
        cset = None

    return cset


def translateRemoteAPI(dvice, cmd, value=None):
    """
    Given a device and a command string, and optionally a value, return the
    constructed dict of actual device commands that corresponds to the given
    command string. If it isn't found, it screams.

    The *general* commands of changing the device's hostname/port and
    enabling/disabling it are not included here, since they operate
    on all (well, almost all) device types.
    """
    # More paranoia!
    try:
        cmd = cmd.lower()
        dvtype = dvice.type.lower()
        value = value.lower()
    except ValueError:
        # This means something has gone very, very wrong.
        #   Take a shortcut to the exit
        dvtype = None

    # Set our default/fail value
    fcmd = None
    cset = {}

    if dvtype == 'vactransducer_mks972b':
        fcmd = mks_kjl.brokerAPI(dvtype, cmd)

    elif dvtype in ["sunpowergen1", "sunpowergen2"]:
        fcmd = sunpower.brokerAPI(dvtype, cmd, value=None)

    elif dvtype in ["lakeshore218", "lakeshore325"]:
        fcmd = lakeshore.brokerAPI(dvtype, cmd, value=None)

    # Package it up for returning
    if fcmd is None:
        print("Unknown command %s!" % (cmd))
    else:
        cset = {cmd: fcmd}

    return cset
