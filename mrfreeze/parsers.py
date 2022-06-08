# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 28 Jun 2019
#
#  @author: rhamilton

"""
"""

from __future__ import division, print_function, absolute_import

import os
import datetime as dt


def assignValueCmd(cmd, value, term, vtype=float, vterm='='):
    """
    cmd is the base/starting command string
    value is the value/argument for the given cmd
    term is the line/command ending/terminator

    vtype is the type of the value
    vterm is the separator between cmd and value
    """
    commandWithVal = None
    try:
        if isinstance(value, float):
            commandWithVal = "%s%s%.3f%s" % (cmd, vterm, float(value), term)
        elif isinstance(value, int):
            commandWithVal = "%s%s%d%s" % (cmd, vterm, int(value), term)
        elif isinstance(value, str):
            commandWithVal = "%s%s%s%s" % (cmd, vterm, str(value), term)
    except ValueError:
        print("Can't convert %s to type %s needed for command %s!" %
              (value, vtype.__name__, cmd))
        print("Ignoring the command.")

    return commandWithVal


def decode(reply):
    """
    TBD
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
    finale = {}

    if dr != '':
        if modelnum == 218:
            if cmdtype.lower() == "sensortemps":
                # Since this will ultimately end up in a dict of some sort,
                #   I want to *specifically* tag which value is which so
                #   I don't have to worry about the order getting scrambled
                #   at some point. Could also make 'labels' an input
                #   parameter, but I won't for right now.
                labels = ["Sensor1", "Sensor2", "Sensor3", "Sensor4",
                          "Sensor5", "Sensor6", "Sensor7", "Sensor8"]
                vals = [float(v) for v in dr.strip().split(',')]
                finale = dict(zip(labels, vals))
            elif cmdtype.lower() == "sensortempsohms":
                labels = ["Sensor1Ohm", "Sensor2Ohm", "Sensor3Ohm",
                          "Sensor4Ohm", "Sensor5Ohm", "Sensor6Ohm",
                          "Sensor7Ohm", "Sensor8Ohm"]
                vals = [float(v) for v in dr.strip().split(',')]
                finale = dict(zip(labels, vals))
            else:
                print("Unknown LS218 Reply!")
        elif modelnum == 325:
            # All of the commands we defined above are single-shot/answer
            #   commands, so just turn them into floats and move on.
            finale = {cmdtype: float(dr)}
        else:
            print("Unknown Lake Shore Model Number!")

    return finale


def parseSunpower(reply):
    """
    TBD
    """
    splitter = "\r\n"
    dr = decode(reply)
    finale = {}

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
        elif cmd.lower() == "set ttarget":
            finale = {"TargetTemp": float(rep[0])}
        elif cmd.lower() == "set pid":
            finale = {"PIDMode": int(rep[0])}
        else:
            print("Unknown Sunpower Response!")

    return finale


def parseLOISTemps(hed, msg):
    """
    Intended to be called from an ActiveMQ listener

    '22:26:55 Level_4:CCD Temp:-110.06 18.54 Setpoints:-109.95 0.00 '
    '22:26:55 Level_4:Telescope threads have been reactivated'
    """
    topic = os.path.basename(hed['destination'])

    # print(ts, msg)
    # Some time shenanigans; the LOIS log doesn't include date but
    #   we can assume it's referencing UT time on the same day.
    #   I suppose that there could be some ambiguity right at UT midnight
    #   ... but oh well.
    now = dt.datetime.utcnow()
    ltime = msg[0:8].split(":")
    # Bail early since this indicates it's not really a log line but
    #   some other type of message (like a LOIS startup or something)
    if msg.strip() == "Lois Log Module Initialized":
        return {}

    if len(ltime) != 3:
        print("Unknown log line!")
        print(msg)
        return {}

    now = now.replace(hour=int(ltime[0]), minute=int(ltime[1]),
                      second=int(ltime[2]), microsecond=0)

    # Get just the log level
    loglevel = msg.split(" ")[1].split(":")[0]
    # Now get the message, putting back together anything split by ":"
    #   this is so we can operate fully on the full message string
    logmsg = " ".join(msg.split(":")[3:]).strip()

    fields = {}
    if loglevel in ["Level_5", "Level_4"]:
        if logmsg.startswith("CCD sensor adus"):
            # print("Parsing: %s" % (logmsg))
            # CCD sensor adus temp1 2248 temp2 3329 set1 2249 heat1 2016'
            adutemp1 = int(logmsg.split(" ")[4])
            adutemp2 = int(logmsg.split(" ")[6])
            aduset1 = int(logmsg.split(" ")[8])
            aduheat1 = int(logmsg.split(" ")[10])

            fields = {"aduT1": adutemp1}
            fields.update({"aduT2": adutemp2})
            fields.update({"aduT2": adutemp2})
            fields.update({"aduS1": aduset1})
            fields.update({"aduH1": aduheat1})

            # print(adutemp1, adutemp2, aduset1, aduheat1)
        elif logmsg.startswith("CCD Heater"):
            # NOTE! This one will have had a ":" removed by the
            #   logmsg creation line above, so you can just split normally
            # print("Parsing: %s" % (logmsg))
            # CCD Heater Values:1.21 0.00
            heat1 = float(logmsg.split(" ")[3])
            heat2 = float(logmsg.split(" ")[4])

            fields = {"H1": heat1}
            fields.update({"H2": heat2})

            # print(heat1, heat2)
        elif logmsg.startswith("CCD Temp"):
            # Same as "CCD Heater" in that ":" have been removed by this point
            # print("Parsing: %s" % (logmsg))
            # CCD Temp -110.06 18.54 Setpoints -109.95 0.00 '
            temp1 = float(logmsg.split(" ")[2])
            temp2 = float(logmsg.split(" ")[3])
            set1 = float(logmsg.split(" ")[5])
            set2 = float(logmsg.split(" ")[6])

            fields = {"T1": temp1}
            fields.update({"T2": temp2})
            fields.update({"S1": set1})
            fields.update({"S2": set2})
            fields.update({"T1S1delta": temp1-set1})

            # print(temp1, temp2, set1, set2)
        else:
            fields = {}
            # print(loglevel, logmsg)

    return fields


def parseNewport(cmdtype, reply, debug=True):
    """
    Expect replies to be in the following possible forms, depending on
    the specific configuration:

    Xxx.xxxY,Xxx.xxxY

    Where X and Y are optional.
    X can be T/T[1...N]/H
    Y are the units, F/C
    """
    dr = decode(reply)
    if dr != '':
        if debug is True:
            print(dr)

        # Figure out our parsing path that we must take
        #   Test the first character
        if dr[0].isdigit():
            # This means there's no prefixes
            prefix = False
        else:
            # This means there are prefixes (T/H/whatever)
            #   BUT!  A negative sign isn't a prefix!
            if dr[0] == '-':
                prefix = False
            else:
                prefix = True

        #   Test the last character
        if dr[-1].isdigit():
            # This means there's no prefixes
            postfix = False
        else:
            # This means there are prefixes (T/H/whatever)
            postfix = True

        # Now figure out how many things we have
        drbits = dr.split(',')
        fields = {}
        for i, each in enumerate(drbits):
            sensNum = "Sensor%02d" % (i+1)

            trimmed = each
            if prefix is True:
                trimmed = each[1:]

            if postfix is True:
                trimmed = trimmed[:-1]

            try:
                rval = float(trimmed)
            except ValueError:
                rval = None

            if rval is not None:
                fields.update({cmdtype: rval})

    return fields
