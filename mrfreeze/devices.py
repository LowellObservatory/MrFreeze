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


def commandSet(device="vactransducer_mks972b"):
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
    elif device == "sunpowergt":
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
                "RealPower": getmpr,
                "CalcPower": getcpr}
    elif device == "lakeshore218":
        # 9600 baud, half duplex
        # 1 start, 7 data, 1 parity, 1 stop
        # odd parity
        # CRLF line termination
        # KRDG? 0 gets all inputs, 1 thru 8
        term = "\r\n"
        gettmp = "KRDG?" + term
        getitp = "TEMP?" + term

        cset = {"SourceTemps": gettmp,
                "InternalTemp": getitp}
    elif device == "lakeshore325":
        # 9600 baud, half duplex
        # 1 start, 7 data, 1 parity, 1 stop
        # odd parity
        # CRLF line termination
        # Note: NIHTS uses loop 2, not loop 1.
        #  Loop 1 is ... terrifying. 25 W max compared to 2W max
        term = "\r\n"
        gettmp = "KRDG?" + term
        getset = "SETP?" + term
        gethtr = "HTR?" + term
        getitp = "TEMP?" + term

        cset = {"SourceTemp": gettmp,
                "Setpoint": getset,
                "Heater": gethtr,
                "InternalTemp": getitp}
    else:
        print("INVALID DEVICE: %s" % (device))
        cset = None

    return cset


def MKSchopper(reply):
    """
    """
    # Regular format:
    #   @<3 digit address><ACK|NAK><value|error code>;FF
    try:
        dr = reply.decode("utf-8")
    except Exception as err:
        print("WTF?")
        print(str(err))

    if dr != '':
        device = dr[1:4]
        status = dr[4:7]
        if status != 'ACK':
            print("ERROR!!!!!")

        val = dr.split(";FF")[0][7:]
        # In case it's a multiline response
        vals = val.split("\r")

        print("Device %s responds %s: %s" % (device, status, vals))
    else:
        print("No response from device")

    # Newline to seperate things while I'm debugging here
    print()

    return device, status, vals
