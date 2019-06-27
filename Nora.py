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
from ligmos.utils import amq, common, classes
from ligmos.workers import workerSetup, connSetup


if __name__ == "__main__":
    # For PIDfile stuff; kindly ignore
    mynameis = os.path.basename(__file__)
    if mynameis.endswith('.py'):
        mynameis = mynameis[:-3]
    pidpath = '/tmp/'

    # Define the default files we'll use/look for. These are passed to
    #   the worker constructor (toServeMan).
    devices = './mrfreeze.conf'
    deviceconf = classes.instrumentDeviceTarget
    queue = './queue.conf'
    queueconf = classes.brokerCommandingTarget
    passes = './passwords.conf'
    logfile = './mrfreeze_nora.log'
    desc = "Nora: Heart of the DCT Instrument Cooler Manager"
    eargs = None
    amqlistener = mrfreeze.listener.MrFreezeCommandConsumer()

    # Interval between successive runs of the polling loop (seconds)
    bigsleep = 600

    # Total time for entire set of actions per instrument
    alarmtime = 600

    # MUY IMPORTANTE
    #   If you want to generate the file needed for LOIS compatability
    #   for NIHTS (/home/obsnihts/cooler/coolerupf.current) IN ADDITION TO
    #   the broker publishing path, set this to True.
    loiscompat = True

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
                                                        logfile=False)

    try:
        with PidFile(pidname=mynameis.lower(), piddir=pidpath) as p:
            # Print the preamble of this particular instance
            #   (helpful to find starts/restarts when scanning thru logs)
            common.printPreamble(p, config)

            # Check to see if there are any connections/objects to establish
            idbs = connSetup.connIDB(comm)

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

            # Semi-infinite loop
            while runner.halt is False:
                # Check on our connections
                amqs = amq.checkConnections(amqs, subscribe=True)

                print("Doing some sort of loop ...")
                mrfreeze.actions.queryAllDevices(config, amqs, idbs)

                print("Done stuff!")

                print("Cleaning out the queue...")
                queueActions = amqlistener.emptyQueue()
                print("%d items obtained from the queue" % (len(queueActions)))

                # Do some more stuff!

                print("Done queue processing!")

                # Diagnostic output
                nleft = len(amqlistener.brokerQueue.items())
                print("%d items still in the queue" % (nleft))

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
