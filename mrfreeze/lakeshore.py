# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 11 Jul 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

from .parsers import assignValueCmd


def allCommands(device):
    """
    9600 baud, half duplex
    1 start, 7 data, 1 parity, 1 stop
    odd parity
    CRLF line termination
    """
    cset = None
    term = None

    if device == 'lakeshore218':
        term = "\r\n"
        readall = "KRDG?"
        readohm = "SRDG?"

        cset = {"readall": readall,
                "readohm": readohm}
    elif device == "lakeshore325":
        # 9600 baud, half duplex
        # 1 start, 7 data, 1 parity, 1 stop
        # odd parity
        # CRLF line termination
        # Note: Instruments will typically use loop 2 for detector
        #   regulation, not loop 1. Loop 1 is ... terrifying.
        # 25 W max compared to 2W max on loop 2.
        term = "\r\n"
        reada = "KRDG?A"
        readb = "KRDG?B"

        readaohm = "SRDG?A"
        readbohm = "SRDG?B"

        getsetp1 = "SETP? 1"
        setsetp1 = "SETP 1"
        getsetp2 = "SETP? 2"
        setsetp2 = "SETP 2"

        gethtrpwr1 = "HTR? 1"
        gethtr1 = "RANGE? 1"
        sethtr1 = "RANGE 1"

        gethtrpwr2 = "HTR? 2"
        gethtr2 = "RANGE? 2"
        sethtr2 = "RANGE 2"

        cset = {"reada": reada,
                "readb": readb,
                "readaohm": readaohm,
                "readbohm": readbohm,
                "getsetp1": getsetp1,
                "setsetp1": setsetp1,
                "getsetp2": getsetp2,
                "setsetp2": setsetp2,
                "gethtrpwr1": gethtrpwr1,
                "gethtr1": gethtr1,
                "sethtr1": sethtr1,
                "gethtrpwr2": gethtrpwr2,
                "gethtr2": gethtr2,
                "sethtr2": sethtr2}
    elif device == "lakeshore331":
        # Mostly the same as the 325, but
        term = "\r\n"
        reada = "KRDG?A"
        readb = "KRDG?B"

        getsetp1 = "SETP? 1"
        setsetp1 = "SETP 1"
        getsetp2 = "SETP? 2"
        setsetp2 = "SETP 2"

        # This is different between the 325 and the 331
        gethtrpwr1 = "HTR?"
        gethtrpwr2 = "AOUT?"

        gethtr = "RANGE?"
        sethtr = "RANGE"

        cset = {"reada": reada,
                "readb": readb,
                "getsetp1": getsetp1,
                "setsetp1": setsetp1,
                "getsetp2": getsetp2,
                "setsetp2": setsetp2,
                "gethtrpwr1": gethtrpwr1,
                "gethtrpwr2": gethtrpwr2,
                "gethtr": gethtr1,
                "sethtr": sethtr1,
                }

    return cset, term


def defaultQueries(device):
    """
    First get the full command set for this particular device.

    These are stored by a key that represents the actual command,
    so I don't forget.
    """
    allCmds, term = allCommands(device=device)

    cset = None

    if device == "lakeshore218":
        cset = {"SensorTemps": allCmds["readall"] + term,
                "SensorTempsOhms": allCmds["readohm"] + term}

    elif device == "lakeshore325":
        cset = {"SensorTempA": allCmds["reada"] + term,
                "SensorTempB": allCmds["readb"] + term,
                "SensorTempAOhm": allCmds["readaohm"] + term,
                "SensorTempBOhm": allCmds["readbohm"] + term,
                "Setpoint1": allCmds["getsetp1"] + term,
                "Setpoint2": allCmds["getsetp2"] + term,
                "Heater1": allCmds["gethtrpwr1"] + term,
                "Heater2": allCmds["gethtrpwr2"] + term}

    return cset


def brokerAPI(dvice, cmd, value=None):
    """
    """
    allcmds, term = allCommands(dvice)

    #   If there's no value given, we can assume it's just a query so
    #   that lets us take an immediate shortcut!
    if value is None:
        if cmd == 'readall':
            fcmd = defaultQueries(device=dvice)
        else:
            fcmd = allcmds[cmd] + term
    else:
        if cmd in ['setsetp1', 'setsetp2']:
            fcmd = assignValueCmd(allcmds[cmd], value, term,
                                  vtype=float, vterm=',')

        elif cmd == 'sethtr1':
            if value.lower() == 'high':
                pval = 2
            elif value.lower() == 'low':
                pval = 1
            elif value.lower() == 'off':
                pval = 0
            else:
                pval = None
                print("Unknown value %s for command %s!" %
                      (value, cmd))

            if pval is not None:
                fcmd = assignValueCmd(allcmds[cmd], pval, term,
                                      vtype=int, vterm=',')

        elif cmd == 'sethtr2':
            if value.lower() == 'on':
                pval = 1
            elif value.lower() == 'off':
                pval = 0
            else:
                pval = None
                print("Unknown value %s for command %s!" %
                      (value, cmd))

            if pval is not None:
                fcmd = assignValueCmd(allcmds[cmd], pval, term,
                                      vtype=int, vterm=',')

    return fcmd
