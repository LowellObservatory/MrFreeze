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
    elif device == "sunpowergen1" or device == 'sunpowergen2':
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

        cset = {"SourceTemps": gettmp}
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

        cset = {"SourceTempA": gettmpA,
                "SetpointA": getsetA,
                "HeaterA": gethtrA,
                "SourceTempB": gettmpB,
                "SetpointB": getsetB,
                "HeaterB": gethtrB}
    else:
        print("INVALID DEVICE: %s" % (device))
        cset = None

    return cset


def decode(reply):
    """
    """
    try:
        dr = reply.decode("utf-8")
    except Exception as err:
        print("Couldn't decode this ... thing! %s" % (reply))
        print(str(err))
        dr = ''

    return dr


def parseMKS(reply, debug=True):
    """
    Expect replies to be in this form:

    @<3 digit address><ACK|NAK><value|error code>;FF
    """
    dr = decode(reply)

    if dr != '':
        device = dr[1:4]
        status = dr[4:7]
        if status != 'ACK':
            print("WARNING: Reply status was not ACK!")

        val = dr.split(";FF")[0][7:]
        # In case it's a multiline response
        vals = val.split("\r")

        if debug is True:
            print("Device %s responds %s: %s" % (device, status, vals))
    else:
        if debug is True:
            print("No response from device")

    return device, status, vals


def parseLakeShore(cmdtype, reply, modelnum=218):
    """
    The Lake Shore units don't echo the command back, so that's why we need
    the commands in addition to the replies to parse things properly.
    """
    dr = decode(reply)

    if dr != '':
        if modelnum == 218:
            if cmdtype.lower() == "sourcetemps":
                finale = [float(v) for v in dr.strip().split(',')]
            else:
                print("Unknown LS218 Reply!")
        elif modelnum == 325:
            # All of the commands we defined above are single-shot/answer
            #   commands, so just turn them into floats and move on.
            finale = float(dr)
        else:
            print("Unknown Lake Shore Model Number!")

        return {cmdtype: finale}


def parseSunpower(reply):
    """
    """
    splitter = "\r\n"
    dr = decode(reply)
    retthingy = {}

    if dr != '':
        # Split the response into its parts; skip the first line
        #   since it's just a command echo but keep it for parse routing.
        splits = dr.split(splitter)
        cmd = splits[0]
        # Last one is always '' because of the ending line termination
        rep = splits[1:-1]

        if cmd.lower() == "state":
            # Multi-stage list comprehension since I can't figure out
            #   how to do it all in one go....
            alls = [v.split("=") for v in rep]
            keys = [v[0].strip() for v in alls]
            vals = [float(v[1]) for v in alls]

            # Now combine the two into a more useful dict
            finale = dict(zip(keys, vals))
        elif cmd.lower() == "tc":
            finale = {"ColdTipTemp": float(rep[0])}
        elif cmd.lower() == "p":
            finale = {"ActualPower": float(rep[0])}
        elif cmd.lower() == "e":
            keys = ["MaxPower", "MinPower", "CommandedPower"]
            vals = [float(v) for v in rep]
            finale = dict(zip(keys, vals))
        else:
            print("Unknown Sunpower Response!")
            finale = None

        # Put all of our parsing together
        retthingy = {cmd: finale}

    return retthingy
