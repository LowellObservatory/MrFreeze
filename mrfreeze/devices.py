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


def queryCommands(device="vactransducer_mks972b"):
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

        cset = {"MicroPirani": mp,
                "ColdCathode": cc,
                "CMB3Digit": d3,
                "CMB4Digit": d4}
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

        cset = {"ColdTip": getctt,
                "TargetTemp": gettar,
                "PowerCommanded": getcpr}
    elif device == "sunpowergen2":
        # 4800 baud
        # 8 data, 1 stop
        # no parity
        # CR line termination
        term = "\r"
        cstate = "STATE" + term
        getctt = "TC" + term
        getmpr = "P" + term
        getcpr = "E" + term

        cset = {"CoolerState": cstate,
                "ColdTip": getctt,
                "PowerMeasured": getmpr,
                "PowerCommanded": getcpr}
    elif device == "lakeshore218":
        # 9600 baud, half duplex
        # 1 start, 7 data, 1 parity, 1 stop
        # odd parity
        # CRLF line termination
        # KRDG? 0 gets all inputs, 1 thru 8
        term = "\r\n"
        gettmp = "KRDG?" + term

        cset = {"SensorTemps": gettmp}
    elif device == "lakeshore325":
        # 9600 baud, half duplex
        # 1 start, 7 data, 1 parity, 1 stop
        # odd parity
        # CRLF line termination
        # Note: NIHTS uses loop 2, not loop 1.
        #  Loop 1 is ... terrifying. 25 W max compared to 2W max
        term = "\r\n"
        gettmpA = "KRDG?A" + term
        getsetA = "SETP? 1" + term
        gethtrA = "HTR? 1" + term

        gettmpB = "KRDG?B" + term
        getsetB = "SETP? 2" + term
        gethtrB = "HTR? 2" + term

        cset = {"SensorTempA": gettmpA,
                "SetpointA": getsetA,
                "HeaterA": gethtrA,
                "SensorTempB": gettmpB,
                "SetpointB": getsetB,
                "HeaterB": gethtrB}
    else:
        print("INVALID DEVICE: %s" % (device))
        cset = None

    return cset
