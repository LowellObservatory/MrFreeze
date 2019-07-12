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

import datetime as dt
from collections import OrderedDict

import xmltodict as xmld

from ligmos.utils import packetizer

from . import parsers


def constructXMLPacket(measurement, fields, rootTag="MrFreezeCommunique",
                       debug=False):
    """
    measurement should be a string describing the thing
    fields should be a dict!
    """
    if not isinstance(fields, dict):
        print("fields must be a dict! Aborting.")
        return None

    dPacket = OrderedDict()

    restOfStuff = {measurement: fields}

    dPacket.update({rootTag: restOfStuff})
    xPacket = xmld.unparse(dPacket)
    if debug is True:
        print(xmld.unparse(dPacket, pretty=True))

    return xPacket


def makeAndPublishAMQ(measname, fields, ts, broker, topic, debug=False):
    """
    Since I repeat this ad-nauseum I figured I'd break it out

    measname should be a string, but if it's a list the first entry will be
      automagically grabbed for you

    fields should be a (flat!!) dict

    ts should be a datetime object
    """
    # Since I combined everything, measname will probably be a list at this
    #   point because the influxdb packetizer requires one; take a quick
    #   and dirty shortcut to get the actual string we need for the XML packet
    if isinstance(measname, list):
        measname = measname[0]

    if ts is None:
        # Don't know why this would happen, but it seems prudent to just
        #   take care of it if it ever does
        ts = dt.datetime.utcnow()
        print("WARNING: Passed in an EMPTY timestamp!")

    # Stuff in our timestamp manually. Since a dict is mutable, this will
    #   filter back down to the caller and it'll appear there too.  That's fine
    #   and it keeps me from having to duplicate all of this in each
    #   publishing function :)
    tsstr = ts.strftime("%Y-%m-%dT%H:%M:%S.%f")
    fields.update({"TimestampUTC": tsstr})

    xmlpkt = constructXMLPacket(measname, fields, debug=debug)

    if broker is not None and xmlpkt is not None:
        broker.publish(topic, xmlpkt, debug=True)


def makeAndPublishIDB(measname, fields, db, tags, table, debug=False):
    """
    Same as above! Often repeated so now it's a function
    """
    pkt = packetizer.makeInfluxPacket(measname, ts=None,
                                      tags=tags, fields=fields,
                                      debug=debug)

    if db is not None and pkt is not None:
        db.singleCommit(pkt, table=table, close=True)


def publish_LSThing(dvice, replies, db=None, broker=None, debug=False):
    """
    as defined in serComm:

    reply is the "key" from devices.queryCommands
    replies[reply][0] is the bytes message
    replies[reply][1] is the timestamp
    """
    # Check what kind of lakeshore thing we have here
    lakeshorething = dvice.devtype.lower()
    if lakeshorething == 'lakeshore218':
        modelno = 218
    elif lakeshorething == 'lakeshore325':
        modelno = 325
    else:
        modelno = None

    measname = ["%s_%s" % (dvice.instrument, dvice.devtype)]
    tags = {"Device": dvice.devtype}
    fields = {}
    for reply in replies:
        ans = parsers.parseLakeShore(reply, replies[reply][0],
                                     modelnum=modelno)

        if ans != {}:
            fields.update(ans)
            lastTS = replies[reply][1]

    if fields != {}:
        makeAndPublishAMQ(measname, fields, lastTS, broker, dvice.brokertopic,
                          debug=debug)
        makeAndPublishIDB(measname, fields, db, tags, dvice.tablename,
                          debug=debug)


def publish_Sunpower(dvice, replies, db=None, broker=None, debug=False):
    """
    Parse our Sunpower stuff; as defined in serComm:

    reply is the "key" from devices.queryCommands
    replies[reply][0] is the bytes message
    replies[reply][1] is the timestamp
    """
    # Since it's possible to have multiple of these on a single instrument
    #   (a la NIHTS) we use the extratag property if it was defined.
    if dvice.extratag is None:
        measname = "%s_%s" % (dvice.instrument, dvice.devtype)
    else:
        measname = "%s_%s_%s" % (dvice.instrument, dvice.devtype,
                                 dvice.extratag)

    measname = [measname]
    tags = {"Device": dvice.devtype}
    fields = {}

    lastTS = None
    for reply in replies:
        ans = parsers.parseSunpower(replies[reply][0])
        if ans != {}:
            fields.update(ans)
            lastTS = replies[reply][1]

    if fields != {}:
        makeAndPublishAMQ(measname, fields, lastTS, broker, dvice.brokertopic,
                          debug=debug)
        makeAndPublishIDB(measname, fields, db, tags, dvice.tablename,
                          debug=debug)


def publish_MKS972b(dvice, replies, db=None, broker=None, debug=False):
    """
    Parse our MKS specific stuff; as defined in serComm:

    reply is the "key" from devices.queryCommands
    replies[reply][0] is the bytes message
    replies[reply][1] is the timestamp
    """
    # Make an InfluxDB packet
    measname = ["%s_%s" % (dvice.instrument, dvice.devtype)]
    tags = {"Device": dvice.devtype}
    fields = {}
    for reply in replies:
        d, s, v = parsers.parseMKS(replies[reply][0])
        # Check the command status (ACK == good)
        if s == 'ACK':
            fieldname = reply
            fields.update({fieldname: float(v[0])})
            lastTS = replies[reply][1]

    if fields != {}:
        makeAndPublishAMQ(measname, fields, lastTS, broker, dvice.brokertopic,
                          debug=debug)
        makeAndPublishIDB(measname, fields, db, tags, dvice.tablename,
                          debug=debug)
