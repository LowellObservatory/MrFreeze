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


def allCommands(device):
    """
    This is the command set for the MKS 972b gauge itself.

    The usual controller (MKS PDR900) has a *different* command set
    that could be used if so desired.

    9600 baud
    8 data, 1 stop bit
    no parity
    ';FF' termination
    """
    cset = None
    term = None

    if device == "vactransducer_mks972b":
        term = ";FF"
        mp = "@254PR1?"
        cc = "@254PR2?"
        d3 = "@254PR3?"
        d4 = "@254PR4?"

        cset = {"micropirani": mp,
                "coldcathode": cc,
                "comboprec3": d3,
                "comboprec4": d4}

    return cset, term


def defaultQueries(device):
    """
    First get the full command set for this particular device.

    These are stored by a key that represents the actual command,
    so I don't forget.
    """
    allCmds, term = allCommands(device=device)

    cset = None

    if device == "vactransducer_mks972b":
        cset = {"MicroPirani": allCmds["micropirani"] + term,
                "ColdCathode": allCmds["coldcathode"] + term,
                "CMB4Digit": allCmds["comboprec4"] + term}

    return cset


def brokerAPI(dvice, cmd):
    """
    These are simple, since they take no arguments/values
    """
    allcmds, term = allCommands(dvice)

    if cmd == 'getvals':
        # This one is just the same as the default set
        fcmd = defaultQueries(device=dvice)
    else:
        fcmd = allcmds[cmd] + term

    return fcmd
