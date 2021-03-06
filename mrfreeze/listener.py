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

import copy
from uuid import uuid4
from collections import OrderedDict

import xmltodict as xmld

from stomp.listener import ConnectionListener

from ligmos import utils

from . import parsers
from . import publishers


class MrFreezeConsumer(ConnectionListener):
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
                    cmddict = parsers.parserCmdPacket(headers, body,
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
                    elif 'nasa42' in tname.lower():
                        meas = ["NASA42_arc-loisgettemp"]

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
                cmduuid = str(uuid4())
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
