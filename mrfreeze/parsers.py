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
        else:
            print("Unknown Sunpower Response!")

    return finale
