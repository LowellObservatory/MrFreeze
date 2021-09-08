# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 6 Jun 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

from ligmos.utils import amqListeners as amqL
from ligmos.utils import messageParsers as mP

from . import parsers
from . import publishers


def newFreezie(cmdTopic, replyTopic, dbconn=None):
    """
    """
    # Topics that can be parsed directly via XML schema
    tXML = []

    # Topics that can be parsed directly via XML schema, but require more work
    # A *dict* of special topics and their custom parser/consumer.
    #   NOTE: the special functions must all take the following arguments:
    #       headers, body, db=None, schema=None
    #   This is to ensure compatibility with the consumer provided inputs!
    tkXMLSpecial = {cmdTopic: mP.parserCmdPacket}

    # Topics that are just bare floats
    tFloat = []

    # Topics that are just words/strings
    tStr = []

    # Topics that are just bools
    tBool = []

    # A *dict* of special topics and their custom parser/consumer.
    #   NOTE: the special functions must all take the following arguments:
    #       headers, body, db=None, schema=None
    #   This is to ensure compatibility with the consumer provided inputs!
    tSpecial = {"LOUI.deveny.loisLog": temperLOIS,
                "LOUI.lemi.loisLog": temperLOIS,
                "LOUI.nihts.loisLog": temperLOIS,
                "LOUI.RC1.loisLog": temperLOIS,
                "LOUI.RC2.loisLog": temperLOIS}

    # Create our subclassed consumer with the above routes
    consumer = amqL.queueMaintainer(cmdTopic, replyTopic,
                                    dbconn=dbconn,
                                    tSpecial=tSpecial,
                                    tkXMLSpecial=tkXMLSpecial,
                                    tXML=tXML, tFloat=tFloat,
                                    tStr=tStr, tBool=tBool)

    return consumer


def temperLOIS(headers, body, db=None):
    """
    THIS IS INTENTED TO BE A STOPGAP!

    At least until I get the rest of this listener sorted out.
    """
    tname = headers['destination'].split('/')[-1].strip()
    tfields = parsers.parseLOISTemps(headers, body)
    # A little bit of hackish because it's already ugly
    #   I HATE THAT THESE ARE HARDCODED BUT IT'S FASTER
    #   AND MAYBE LOIS WILL GO AWAY SOON SO I CAN DITCH THIS.
    # I couldn't figure out a quick way to get the config
    #   sections into here, but probably could with more effort
    table = "MrFreeze"
    tags = {"Device": "arc-loisgettemp"}
    if 'lemi' in tname.lower():
        meas = ["LMI_arc-loisgettemp"]
    elif 'deveny' in tname.lower():
        meas = ["DeVeny_arc-loisgettemp"]
    elif 'nasa42' in tname.lower():
        meas = ["NASA42_arc-loisgettemp"]

    # Only store the packet if we actually have fields that
    #   were successfully parsed
    if tfields != {}:
        publishers.makeAndPublishIDB(meas, tfields, db,
                                     tags, table, debug=True)
