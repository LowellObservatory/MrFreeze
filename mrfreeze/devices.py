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


def allCommands(device=None):
    """
    Set of specific command strings valid for specific devices.
    Specifically, these are good for:

    MKS (or Kurt J. Lesker) vacuum pressure transducers: 972B
    Sunpower CryoTel-style coolers
    Lake Shore 325, 218

    cset should be a dictionary mapping a readable description of a param
    to the actual serial command needed to get it.  Parsing the result
    occurs elsewhere.
    """

    if device == "vactransducer_mks972b":
        # NOTE: This is the command set for the gauge directly; the controller
        #  (MKS PDR900) has a *different* command set that could be used
        # 9600 baud
        # 8 data, 1 stop bit
        # no parity
        # ';FF' termination
        term = ";FF"
        mp = "@254PR1?" + term
        cc = "@254PR2?" + term
        d3 = "@254PR3?" + term
        d4 = "@254PR4?" + term

        cset = {"mp": mp,
                "cc": cc,
                "prec3": d3,
                "prec4": d4}
    elif device == "sunpowergen1":
        # NOTE A Gen 1 controller has less functionality than the Gen 2.
        #   Specifically, there's no way to get the actual/measured power!
        # 4800 baud
        # 8 data, 1 stop
        # no parity
        # CR line termination
        term = "\r"
        getctt = "TC" + term
        gettar = "SET TTARGET" + term
        getcpr = "E" + term

        cset = {"ct": getctt,
                "target": gettar,
                "cmdpower": getcpr}
    elif device == "sunpowergen2":
        # 4800 baud
        # 8 data, 1 stop
        # no parity
        # CR line termination
        term = "\r"
        cstate = "STATE" + term
        getctt = "TC" + term
        gettar = "SET TTARGET" + term
        getmpr = "P" + term
        getcpr = "E" + term

        cset = {"state": cstate,
                "ct": getctt,
                "target": gettar,
                "mpower": getmpr,
                "cmdpower": getcpr}
    elif device == "lakeshore218":
        # 9600 baud, half duplex
        # 1 start, 7 data, 1 parity, 1 stop
        # odd parity
        # CRLF line termination
        # KRDG? 0 gets all inputs, 1 thru 8
        term = "\r\n"
        gettmp = "KRDG?" + term

        cset = {"readall": gettmp}
    elif device == "lakeshore325":
        # 9600 baud, half duplex
        # 1 start, 7 data, 1 parity, 1 stop
        # odd parity
        # CRLF line termination
        # Note: NIHTS uses loop 2 for detector regulation, not loop 1.
        #  Loop 1 is ... terrifying. 25 W max compared to 2W max.
        term = "\r\n"
        gettmpA = "KRDG?A" + term
        getsetA = "SETP? 1" + term
        gethtrA = "HTR? 1" + term

        gettmpB = "KRDG?B" + term
        getsetB = "SETP? 2" + term
        gethtrB = "HTR? 2" + term

        cset = {"reada": gettmpA,
                "set1": getsetA,
                "htr1": gethtrA,
                "readb": gettmpB,
                "set2": getsetB,
                "htr2": gethtrB}
    else:
        print("INVALID DEVICE: %s" % (device))
        cset = None

    return cset


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
    # First get the full command set for this particular device
    #   These are stored by a key that represents the actual command,
    #   so I don't forget.
    allCmds = allCommands(device=device)

    if device == "vactransducer_mks972b":
        cset = {"MicroPirani": allCmds["mp"],
                "ColdCathode": allCmds["cc"],
                "CMB4Digit": allCmds["prec4"]}

    elif device == "sunpowergen1":
        cset = {"ColdTip": allCmds["ct"],
                "TargetTemp": allCmds["target"],
                "PowerCommanded": allCmds["cmdpower"]}

    elif device == "sunpowergen2":
        cset = {"CoolerState": allCmds["state"],
                "ColdTip": allCmds["ct"],
                "PowerMeasured": allCmds["p"],
                "PowerCommanded": allCmds["e"]}

    elif device == "lakeshore218":
        cset = {"SensorTemps": allCmds["krdg"]}

    elif device == "lakeshore325":
        cset = {"SensorTempA": allCmds["krdga"],
                "SetpointA": allCmds["setp1"],
                "HeaterA": allCmds["htr1"],
                "SensorTempB": allCmds["krdgb"],
                "SetpointB": allCmds["setp2"],
                "HeaterB": allCmds["htr2"]}
    else:
        print("INVALID DEVICE: %s" % (device))
        cset = None

    return cset


def remoteQueryAPI(dvice, cmd, value=None):
    """
    This defines the interface between the commands that can come in
    over the broker and those that actually get sent to the devices.

    Given a command keyword (and value, if there is one) it'll return the
    command set to be issued to a given device.  If it isn't found, it
    screams.

    The *general* commands of changing the device's hostname/port and
    enabling/disabling it are not included here, since they operate
    on all (well, almost all) device types.
    """
    # Get all the defined commands for this device
    allCmds = allCommands(device=dvice)

    if dvice.type.lower() == 'vactransducer_mks972b':
        if cmd.lower() == 'getvals':
            # This one is just the same as the default set
            cset = {"GetAllValues": cset}
        elif cmd.lower() == 'getmp':
            cset = {"MicroPirani": cset["MicroPirani"]}
        elif cmd.lower() == 'getcc':
            cset = {"ColdCathode": cset["ColdCathode"]}
        elif cmd.lower() == 'getcombo':
            cset = {"CombinedPressure": cset["CMB4Digit"]}

    elif dvice.type.lower() == "sunpowergen1":
        pass
