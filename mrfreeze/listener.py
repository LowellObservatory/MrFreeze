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

import os
import copy
import uuid
from collections import OrderedDict, MutableMapping

import xmltodict as xmld
import xmlschema as xmls

from stomp.listener import ConnectionListener

from ligmos import utils

from . import parsers
from . import publishers


class MrFreezeCommandConsumer(ConnectionListener):
    def __init__(self, db=None):
        """
        This is just to route the messages to the right parsers
        """
        # Grab all the schemas that are in the ligmos library
        self.schemaDict = utils.amq.schemaDicter()
        self.brokerQueue = OrderedDict()

        # This assumes that the database object was set up elsewhere
        self.db = db

    def on_message(self, headers, body):
        """
        Basically subclassing stomp.listener.ConnectionListener
        """
        badMsg = False
        tname = headers['destination'].split('/')[-1].strip()
        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
        except UnicodeDecodeError as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        if badMsg is False:
            try:
                xml = xmld.parse(body)
                # If we want to have the XML as a string:
                # res = {tname: [headers, dumpPacket(xml)]}
                # If we want to have the XML as an object:
                res = {tname: [headers, xml]}
            except xmld.expat.ExpatError:
                # This means that XML wasn't found, so it's just a string
                #   packet with little/no structure. Attach the sub name
                #   as a tag so someone else can deal with the thing
                res = {tname: [headers, body]}
            except Exception as err:
                # This means that there was some kind of transport error
                #   or it couldn't figure out the encoding for some reason.
                #   Scream into the log but keep moving
                print("="*42)
                print(headers)
                print(body)
                print(str(err))
                print("="*42)
                badMsg = True

        # Now send the packet to the right place for processing.
        #   These need special parsing because they're just straight text
        cmddict = {}
        if badMsg is False:
            try:
                if tname == 'lig.MrFreeze.cmd':
                    # TODO: Wrap this in a proper try...except
                    #   As of right now, it'll be caught in the "WTF!!!"
                    schema = self.schemaDict[tname]
                    cmddict = parserCmdPacket(headers, body,
                                              schema=schema,
                                              debug=True)
                elif tname.endswith("loisLog"):
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

                    # Only store the packet if we actually have fields that
                    #   were successfully parsed
                    if tfields != {}:
                        publishers.makeAndPublishIDB(meas, tfields, self.db,
                                                     tags, table, debug=True)
                else:
                    # Intended to be the endpoint of the auto-XML publisher
                    #   so I can catch most of them rather than explicitly
                    #   check in the if/elif block above
                    print("Orphan topic: %s" % (tname))
                    print(headers)
                    print(body)
                    print(res)
            except Exception as err:
                # This is a catch-all to help find parsing errors that need
                #   to be fixed since they're not caught in a parser* func.
                print("="*11)
                print("WTF!!!")
                print(str(err))
                print(headers)
                print(body)
                print("="*11)
            if cmddict != {}:
                # This lets us make sure that we remove the right one from
                #   the queue when it's processed
                # UUID4 is just a random UUID
                cmduuid = str(uuid.uuid4())
                self.brokerQueue.update({cmduuid: cmddict})

    def emptyQueue(self):
        # We NEED deepcopy() here to prevent the loop from being
        #   confused by a mutation/addition from the listener
        checkQueue = copy.deepcopy(self.brokerQueue)
        print("%d items in the queue" % len(checkQueue.items()))

        newactions = []

        if checkQueue != {}:
            for uuid in checkQueue:
                print("Processing command %s" % (uuid))
                print(checkQueue[uuid])
                print("Removing it from the queue...")
                action = self.brokerQueue.pop(uuid)
                newactions.append(action)

        return newactions


def parserCmdPacket(hed, msg, schema=None, debug=False):
    """
    """
    # print(msg)
    # This is really the topic name, so we'll make that the measurement name
    #   for the sake of clarity. It NEEDS to be a list until I fix packetizer!
    meas = [os.path.basename(hed['destination'])]

    # Bail if there's a schema not found; needs expansion here
    if schema is None:
        print("No schema found for topic %s!" % (meas[0]))
        return None

    # In this house, we only store valid packets!
    good = schema.is_valid(msg)

    # A DIRTY DIRTY HACK
    try:
        xmlp = schema.to_dict(msg, decimal_type=float, validation='lax')
        # print(xmlp)
        good = True
    except xmls.XMLSchemaValidationError:
        good = False

    fields = {}
    if good is True:
        # print("Packet good!")
        try:
            xmlp = schema.to_dict(msg, decimal_type=float, validation='lax')
            # I HATE THIS
            if isinstance(xmlp, tuple):
                xmlp = xmlp[0]

            # Back to normal.
            keys = xmlp.keys()

            # Store each key:value pairing
            for each in keys:
                val = xmlp[each]

                # TESTING
                if isinstance(val, dict):
                    flatVals = flatten(val, parent_key=each)
                    fields.update(flatVals)
                else:
                    fields.update({each: val})

            if fields is not None:
                # do something ... ?
                pass
        except xmls.XMLSchemaDecodeError as err:
            print(err.message.strip())
            print(err.reason.strip())

        # Added for itteratively testing parsed packets outside of the
        #   usual operational mode (like in toymodels/PacketSchemer)
        if debug is True:
            print("Parsed packet: ", fields)

    return fields


def flatten(d, parent_key='', sep='_'):
    """
    Thankfully StackOverflow exists because I'm too tired to write out this
    logic myself and now I can just use this:
    https://stackoverflow.com/a/6027615
    With thanks to:
    https://stackoverflow.com/users/1897/imran
    https://stackoverflow.com/users/1645874/mythsmith
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
