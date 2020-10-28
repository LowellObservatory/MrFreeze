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
    Device connects over just a simple socket
    CR line termination
    """
    cset = None
    term = None

    if device == 'newport_ithx':
        term = "\r"
        readtemp = "*SRTC"
        readhumi = "*SRH"
        readdewp = "*SRD"

        cset = {"readtemp": readtemp,
                "readhumi": readhumi,
                "readdewp": readdewp}
    elif device == "newport_isd-tc":
        term = "\r"
        readtemp1 = "*SRTC"
        readtemp2 = "*SRHC"
        readdiff = "*SRDC"

        cset = {"readtemp1": readtemp1,
                "readtemp2": readtemp2,
                "readdiff": readdiff}

    return cset, term


def defaultQueries(device):
    """
    First get the full command set for this particular device.

    These are stored by a key that represents the actual command,
    so I don't forget.
    """
    allCmds, term = allCommands(device=device)

    cset = None

    if device == "newport_ithx":
        cset = {"Temperature": allCmds["readtemp"] + term,
                "Humidity": allCmds["readhumi"] + term,
                "Dewpoint": allCmds["readdewp"] + term
                }

    elif device == "newport_isd-tc":
        cset = {"Temperature1": allCmds["readtemp1"] + term,
                "Temperature2": allCmds["readtemp2"] + term,
                "Difference": allCmds["readdiff"] + term
                }

    return cset


def brokerAPI(dvice, cmd, value=None):
    """
    """
    allcmds, term = allCommands(dvice)
    if cmd == 'readall':
        fcmd = defaultQueries(device=dvice)
    else:
        fcmd = allcmds[cmd] + term

    return fcmd
