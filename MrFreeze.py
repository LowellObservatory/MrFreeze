# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 25 May 2018
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

import os
import sys
import time
import signal
import datetime as dt

import serial

import mrfreeze
from ligmos import utils

from pid import PidFile, PidFileError


if __name__ == "__main__":
    # For PIDfile stuff; kindly ignore
    mynameis = os.path.basename(__file__)
    if mynameis.endswith('.py'):
        mynameis = mynameis[:-3]
    pidpath = '/tmp/'

    conf = './mrfreeze.conf'
    passes = None
    logfile = '/tmp/mrfreeze.log'

    # InfluxDB database name to store stuff in
    dbname = 'MrFreeze'

    # Interval between successive runs of the polling loop (seconds)
    bigsleep = 600

    # Total time for entire set of actions per instrument
    alarmtime = 600

    # Quick renaming to keep line length under control
    malarms = utils.multialarm
    ip = utils.packetizer
    devices = mrfreeze.devices
    scomm = mrfreeze.serialcomm
    ic = utils.common.deviceTarget

    # idict: dictionary of parsed config file
    # args: parsed options of wadsworth.py
    # runner: class that contains logic to quit nicely
    idict, cblk, args, runner = mrfreeze.workerSetup.toServeMan(mynameis, conf,
                                                                passes,
                                                                logfile,
                                                                conftype=ic,
                                                                logfile=True)

    # Gather up all the broker topics that are defined in the diff sections.
    #   Assumes that they're all 'brokertopic' which is what they should be.
    topics = []
    for each in idict:
        try:
            topics.append(idict[each].brokertopic)
        except AttributeError:
            pass

    # ActiveMQ connection checker
    conn = None

    try:
        with PidFile(pidname=mynameis.lower(), piddir=pidpath) as p:
            # Print the preamble of this particular instance
            #   (helpful to find starts/restarts when scanning thru logs)
            utils.common.printPreamble(p, idict)

            # One by one, set up the broker connections.
            if cblk is not None:
                first = False
                if cblk.brokertype.lower() == "activemq":
                    # Register the custom listener class.
                    #   This will be the thing that parses packets depending
                    #   on their topic name and does the hard stuff!!
                    #   It should be a subclass of (stomp.py) subscriber.
                    # (removed for now)

                    # Establish connections and subscriptions w/our helper
                    conn = utils.amq.amqHelper(cblk.brokerhost,
                                               topics=topics,
                                               dbname=cblk.influxdbname,
                                               user=None,
                                               passw=None,
                                               port=cblk.brokerport,
                                               connect=True)
#                                               listener=crackers)
                    first = True

            # Semi-infinite loop
            while runner.halt is False:

                # Double check that the connection is still up
                #   NOTE: conn.connect() handles ConnectionError exceptions
                if conn.conn is None:
                    print("No connection at all! Retrying...")
                    conn.connect()
                elif conn.conn.transport.connected is False and first is False:
                    # Added the "first" flag to take care of a weird bug
                    print("Connection died! Reestablishing...")
                    conn.connect()
                else:
                    print("Connection still valid")

                # If we're here, we made it once thru. The above comparison
                #   will fail without this and we'll never reconnect!
                first = False

                # Loop thru the different instrument sets
                for inst in idict:
                    print(inst)
                    for dvice in idict[inst].devices:
                        # Go and get commands that are valid for the device
                        msgs = devices.commandSet(device=dvice.type)

                        # Now send the commands
                        try:
                            replies = scomm.serComm(dvice.serialURL, msgs)
                        except serial.SerialException as err:
                            print("Badness 10000")
                            print(str(err))

                        for i, reply in enumerate(replies):
                            # Parse our MKS specific stuff
                            #   Because we got a dict of replies, we can
                            #   bag and tag easier.  As defined in serComm:
                            #     reply[0] is the message (still in bytes)
                            #     reply[1] is the timestamp
                            if dvice.type == "vactransducer_mks972b":
                                d, s, v = devices.MKSchopper(replies[reply][0])
                                # Make an InfluxDB packet
                                meas = [idict[inst].name]
                                tags = {"Device": dvice.type}
                                # Check the command status (ACK == good)
                                if s == 'ACK':
                                    fieldname = reply
                                    fs = {fieldname: float(v[0])}
                                    packet = ip.makeInfluxPacket(meas,
                                                                 ts=None,
                                                                 tags=tags,
                                                                 fields=fs,
                                                                 debug=True)
                                else:
                                    packet = None
                            elif dvice.type == 'sunpowergt':
                                print(reply)
                            elif dvice.type == 'lakeshore218':
                                print(reply)
                            elif dvice.type == 'lakeshore325':
                                print(reply)

                            if dbname is not None and packet is not None:
                                # Actually write to the database to store
                                #   for plotting
                                dbase = utils.database.influxobj(dbname,
                                                                 connect=True)
                                dbase.writeToDB(packet)
                                dbase.closeDB()

                # Consider taking a big nap
                if runner.halt is False:
                    print("Starting a big sleep")
                    # Sleep for bigsleep, but in small chunks to check abort
                    for i in range(bigsleep):
                        time.sleep(1)
                        if runner.halt is True:
                            break

            # The above loop is exited when someone sends SIGTERM
            print("PID %d is now out of here!" % (p.pid))

            # Disconnect from the ActiveMQ broker
            conn.disconnect()

            # The PID file will have already been either deleted/overwritten by
            #   another function/process by this point, so just give back the
            #   console and return STDOUT and STDERR to their system defaults
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            print("Archive loop completed; STDOUT and STDERR reset.")
    except PidFileError as err:
        # We've probably already started logging, so reset things
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        print("Already running! Quitting...")
        utils.common.nicerExit()
