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
    A Gen 1 controller has less functionality than the Gen 2.

    Specifically, there's no way to get the actual/measured power!

    4800 baud
    8 data, 1 stop
    no parity
    CR line termination
    """
    cset = None
    term = None

    if device in ['sunpowergen1', 'sunpowergen2']:
        term = "\r"
        coldtip = "TC"
        target = "SET TTARGET"
        cmdpower = "E"

        cset = {"coldtip": coldtip,
                "target": target,
                "cmdpower": cmdpower}

        # NOTE a Gen. 2 type is a subset of the above!
        if device == "sunpowergen2":
            stopmode = "SET SSTOPM"
            stop = "SET SSTOP"

            minpwr = "SET MIN"
            maxpwr = "SET MAX"

            state = "STATE"

            mpower = "P"

            g2cset = {"stopmode": stopmode,
                      "stop": stop,
                      "minpwr": minpwr,
                      "maxpwr": maxpwr,
                      "state": state,
                      "mpower": mpower}

            # Add to the gen1 command set
            cset.update(g2cset)

    return cset, term


def defaultQueries(device):
    """
    First get the full command set for this particular device.

    These are stored by a key that represents the actual command,
    so I don't forget.
    """
    allCmds, term = allCommands(device=device)

    cset = None

    if device == "sunpowergen1":
        cset = {"ColdTip": allCmds["coldtip"] + term,
                "TargetTemp": allCmds["target"] + term,
                "PowerCommanded": allCmds["cmdpower"] + term}

    elif device == "sunpowergen2":
        cset = {"CoolerState": allCmds["state"] + term,
                "ColdTip": allCmds["coldtip"] + term,
                "PowerMeasured": allCmds["mpower"] + term,
                "PowerCommanded": allCmds["cmdpower"] + term}

    return cset


def brokerAPI(dvice, cmd, value=None):
    """
    """
    allcmds, term = allCommands(dvice)

    #   If there's no value given, we can assume it's just a query so
    #   that lets us take an immediate shortcut!
    if value is None:
        # Could technically have an error here if the command
        #   is for a Gen. 2 controller but dvtype is a Gen. 1.
        #
        # If that does occur, I'm pretty sure the controller's response
        #   will just be b'' so the parser will catch/ignore that.
        fcmd = allcmds[cmd] + term
    else:
        if cmd == 'target':
            fcmd = assignValueCmd(allcmds[cmd], value, term,
                                  vtype=float, vterm='=')

        if dvice == "sunpowergen2":
            if cmd == 'stopmode':
                if value.lower() == 'enable':
                    # This means that we want to *enable* the ability
                    #   to turn off the cooler via software.
                    # Yes, it's confusing.
                    pval = 0
                elif value.lower() == 'disable':
                    # Opposite of the above
                    pval = 1
                else:
                    pval = None
                    print("Unknown value %s for command %s!" %
                          (value, cmd))

                if pval is not None:
                    fcmd = assignValueCmd(allcmds[cmd], pval, term,
                                          vtype=int, vterm='=')

            elif cmd == 'stop':
                # Could have nanny code here to combine with 'stopmode'
                if value.lower() == 'off':
                    # 'stop off' means literally turn the stop off,
                    #   i.e. start the cooler
                    pval = 0
                elif value.lower() == 'on':
                    # 'stop on' means literally turn the stop on,
                    #   i.e. stop the cooler
                    pval = 1
                else:
                    pval = None

                if pval is not None:
                    fcmd = assignValueCmd(allcmds[cmd], pval, term,
                                          vtype=int, vterm='=')

            elif cmd in ['minpwr', 'maxpwr']:
                fcmd = assignValueCmd(allcmds[cmd], value, term,
                                      vtype=float, vterm='=')

    return fcmd
