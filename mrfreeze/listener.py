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

import time
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

        # Now send the packet to the right place for processing.
        #   These need special parsing because they're just straight text
        cmddict = {}
        if badMsg is False:
            try:
                if tname == 'lig.MrFreeze.cmd':
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
                # Track the time it was on the queue for later diagnostics.
                #   This will be updated to just the difference/elapsed time
                #   when the action is done and sent back on the reply topic
                cmddict.update({"timeonqueue": time.time()})
                # This lets us make sure that we remove the right one from
                #   the queue when it's processed
                try:
                    cmduuid = cmddict['cmd_id']
                except KeyError:
                    # The cmd producer SHOULD have appended a (UNIQUE!) tag
                    #   to the cmd XML before it sent it, but if it wasn't
                    #   there, generate a random UUID so it could be tracked
                    #   at least part of the way back to the source.
                    cmduuid = str(uuid4())

                # Finally put it all on the queue for later consumption
                self.brokerQueue.update({cmduuid: cmddict})

    def emptyQueue(self):
        # We NEED deepcopy() here to prevent the loop from being
        #   confused by a mutation/addition from the listener
        checkQueue = copy.deepcopy(self.brokerQueue)
        if len(checkQueue.items()) > 0:
            print("%d items in the queue" % len(checkQueue.items()))

        newactions = []

        if checkQueue != {}:
            for uuid in checkQueue:
                # Update the timeonqueue entry to show how long it sat
                action['timeonqueue'] = time.time() - action['timeonqueue']
                action = self.brokerQueue.pop(uuid)

                # Really just a debug print but it helps here
                print("Removing %s from the queue, ready for action" % (uuid))
                print(checkQueue[uuid])

                newactions.append(action)

        return newactions
