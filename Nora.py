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

from pid import PidFile, PidFileError

import mrfreeze
from ligmos.workers import workerSetup, connSetup
from ligmos.utils import amq, common, classes, confparsers


if __name__ == "__main__":
    # For PIDfile stuff; kindly ignore
    mynameis = os.path.basename(__file__)
    if mynameis.endswith('.py'):
        mynameis = mynameis[:-3]
    pidpath = '/tmp/'

    # Define the default files we'll use/look for. These are passed to
    #   the worker constructor (toServeMan).
    devices = './config/mrfreeze.conf'
    deviceconf = classes.instrumentDeviceTarget
    passes = './config/passwords.conf'
    logfile = './mrfreeze_nora.log'
    desc = "Nora: Heart of the DCT Instrument Cooler Manager"
    eargs = None

    # Interval between successive runs of the polling loop (seconds)
    bigsleep = 60

    # config: dictionary of parsed config file
    # comm: common block from config file
    # args: parsed options
    # runner: class that contains logic to quit nicely
    config, comm, args, runner = workerSetup.toServeMan(mynameis, devices,
                                                        passes,
                                                        logfile,
                                                        desc=desc,
                                                        extraargs=eargs,
                                                        conftype=deviceconf,
                                                        enableCheck=False,
                                                        logfile=False)

    # Reorganize the configuration to be per-instrument so it's a little
    #   easier to loop over and do other stuff with
    allInsts = confparsers.regroupConfig(config, groupKey='instrument',
                                         ekeys=['devtype', 'extratag'])

    try:
        with PidFile(pidname=mynameis.lower(), piddir=pidpath) as p:
            # Print the preamble of this particular instance
            #   (helpful to find starts/restarts when scanning thru logs)
            common.printPreamble(p, config)

            # Check to see if there are any connections/objects to establish
            idbs = connSetup.connIDB(comm)

            # UGH more hardcoding. Someone more clever than I can clean up.
            db = idbs['database-dct']
            amqlistener = mrfreeze.listener.MrFreezeCommandConsumer(db=db)

            # Specify our custom listener that will really do all the work
            #   Since we're hardcoding for the DCTConsumer anyways, I'll take
            #   a bit shortcut and hardcode for the DCT influx database.
            # TODO: Figure out a way to create a dict of listeners specified
            #   in some creative way. Could add a configuration item to the
            #   file and then loop over it, and change connAMQ accordingly.
            amqtopics = amq.getAllTopics(config, comm)
            amqs = connSetup.connAMQ(comm, amqtopics, amqlistener=amqlistener)

            # Just hardcode this for now. It's a prototype!
            conn = amqs['broker-dct'][0]
            queue = comm['queue-mrfreeze']

            # Semi-infinite loop
            while runner.halt is False:
                # Check on our connections
                amqs = amq.checkConnections(amqs, subscribe=True)
                # Make sure we update our hardcoded reference
                conn = amqs['broker-dct'][0]

                print("Advertising the current actions...")
                adpacket = mrfreeze.publishers.advertiseConfiged(allInsts)
                conn.publish(queue.replytopic, adpacket)

                # Check for any updates to those actions, or any commanded
                #   actions in general
                print("Cleaning out the queue...")
                queueActions = amqlistener.emptyQueue()
                print("%d items obtained from the queue" % (len(queueActions)))

                # Do some stuff!
                for action in queueActions:
                    print("Doing action...")
                    ainst = action['request_instrument']
                    adevc = action['request_device']
                    atag = action['request_tag']
                    acmd = action['request_command']
                    aarg = action['request_argument']

                    # Do a simple check to see if it's a command for Nora
                    if acmd.lower() == 'advertise':
                        print("Advertising the current actions...")
                        adpacket = mrfreeze.publishers.advertiseConfiged(allInsts)
                        conn.publish(queue.replytopic, adpacket)

                    if atag is not None:
                        cdest = "%s_%s" % (adevc, atag)
                    else:
                        cdest = "%s" % (adevc)

                    # Check to see if this destination is one we actually
                    #   know anything about
                    try:
                        selInst = allInsts[ainst][cdest]
                    except AttributeError:
                        print("WARNING: Command %s ignored!" % (acmd))
                        print("Unknown instrument %s" % (cdest))
                        selInst = None

                    print(selInst)

                    # Now check the actual command
                    if selInst is not None:
                        if acmd.lower() == "queryenable":
                            print("Enabling %s %s" % (ainst, cdest.lower()))
                            selInst.enabled = True
                        elif acmd.lower() == "querydisable":
                            print("Disabling %s %s" % (ainst, cdest.lower()))
                            selInst.enabled = False
                        elif acmd.lower() == "devicehost":
                            print("Setting device host to %s" % (aarg))
                            selInst.devhost = aarg
                        elif acmd.lower() == "deviceport":
                            print("Setting device port to %s" % (aarg))
                            selInst.devport = aarg
                        else:
                            # Check to see if the command is in the remoteAPI
                            #   that we defined for the devices
                            pass

                        # Now store this instrument back in the main set,
                        #   so we can use any updates that just happened
                        allInsts[ainst][cdest] = selInst

                # Diagnostic output
                nleft = len(amqlistener.brokerQueue.items())
                print("%d items still in the queue" % (nleft))

                for inst in allInsts:
                    print("Processing instrument %s" % (inst))
                    # It could be that all the devices of this instrument
                    #   are actually disabled; the query function will
                    #   check before actually querying though, since that
                    #   can change from loop-to-loop depending on the above
                    #   queueActions
                    mrfreeze.actions.queryAllDevices(allInsts[inst],
                                                     amqs, idbs,
                                                     debug=True)

                print("Done stuff!")

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

            # Disconnect from all ActiveMQ brokers
            amq.disconnectAll(amqs)

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
        common.nicerExit()
