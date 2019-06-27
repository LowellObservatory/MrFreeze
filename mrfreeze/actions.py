# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 27 Jun 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

from collections import OrderedDict

import serial
import xmltodict as xmld

from ligmos.utils import packetizer

from . import devices
from . import serialcomm as scomm


def constructXMLPacket(instrument, devicetype, fields, debug=False):
    """
    fieldset should be a dict!
    """
    if not isinstance(fields, dict):
        print("fieldset must be a dict! Aborting.")
        return None

    dPacket = OrderedDict()
    rootTag = "MrFreezeCommunique"

    restOfStuff = {instrument: {devicetype: fields}}

    dPacket.update({rootTag: restOfStuff})
    xPacket = xmld.unparse(dPacket)
    if debug is True:
        print(xmld.unparse(dPacket, pretty=True))

    return xPacket


def publish_MKS972b(dvice, replies, db=None, broker=None):
    """
    Parse our MKS specific stuff; as defined in serComm:

    reply is the "key" from devices.commandSet
    replies[reply][0] is the bytes message
    replies[reply][1] is the timestamp
    """
    # Make an InfluxDB packet
    measname = "%s_vacuum" % (dvice.instrument)
    meas = [measname]
    tags = {"Device": dvice.devtype}
    fields = {}
    for reply in replies:
        d, s, v = devices.parseMKS(replies[reply][0])
        # Check the command status (ACK == good)
        if s == 'ACK':
            fieldname = reply
            fields.update({fieldname: float(v[0])})

    xmlpkt = constructXMLPacket(dvice.instrument, dvice.devtype, fields,
                                debug=True)

    pkt = packetizer.makeInfluxPacket(meas,
                                      ts=None,
                                      tags=tags,
                                      fields=fields,
                                      debug=True)

    if db is not None and pkt is not None:
        db.singleCommit(pkt, table=dvice.tablename, close=True)


def queryAllDevices(config, idbs):
    """
    """
    # Loop thru the different instrument sets
    for vice in config:
        dvice = config[vice]
        # Get our specific database connection object
        try:
            dbObj = idbs[dvice.database]
        except KeyError:
            dbObj = None

        # Go and get commands that are valid for the device
        msgs = devices.queryCommands(device=dvice.devtype)

        # Now send the commands
        try:
            reply = scomm.serComm(dvice.devhost, dvice.devport,
                                  msgs, debug=True)
        except serial.SerialException as err:
            print("Badness 10000")
            print(str(err))
            reply = None

        if reply is not None:
            if dvice.devtype.lower() == 'vactransducer_mks972b':
                publish_MKS972b(dvice, reply, db=dbObj)
            # elif dvice.type.lower() == 'sunpowergt':
            #     ans = devices.parseSunpower(replies[reply][0])
            # elif dvice.type.lower() == 'lakeshore218':
            #     # NOTE: Need to pass in the tag/key here
            #     #   because the LS doesn't echo commands.
            #     #   No good way to determine response type
            #     #   unless the overall structure here is
            #     #   changed to parse the result immediately
            #     #   on reply rather than doing all the comms
            #     #   in one big chunk like we are right now.
            #     devices.parseLakeShore(reply,
            #                             replies[reply][0],
            #                             modelnum=218)
            # elif dvice.type.lower() == 'lakeshore325':
            #     devices.parseLakeShore(reply,
            #                             replies[reply][0],
            #                             modelnum=325)
