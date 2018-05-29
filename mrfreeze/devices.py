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
    """

    if device == "vactransducer_mks972b":
        mp = "@254PR1?;FF"
        cc = "@254PR2?;FF"
        d3 = "@254PR3?;FF"
        d4 = "@254PR4?;FF"

        cset = {"MicroPirani": mp,
                "ColdCathode": cc,
                "CMB3Digit": d3,
                "CMB4Digit": d4}
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
