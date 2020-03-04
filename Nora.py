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
from datetime import datetime

import schedule

from ligmos.workers import workerSetup, connSetup
from ligmos.utils import amq, common, classes, confparsers

from mrfreeze import actions, listener, compatibility


def main():
    """
    """
    # Define the default files we'll use/look for. These are passed to
    #   the worker constructor (toServeMan).
    devices = './config/mrfreeze.conf'
    deviceconf = classes.instrumentDeviceTarget
    passes = None
    logfile = './mrfreeze_nora.log'
    desc = "Nora: Heart of the DCT Instrument Cooler Manager"
    eargs = None

    # Interval between successive runs of the polling loop (seconds)
    bigsleep = 1

    # config: dictionary of parsed config file
    # comm: common block from config file
    # args: parsed options
    # runner: class that contains logic to quit nicely
    config, comm, args, runner = workerSetup.toServeMan(devices,
                                                        passes,
                                                        logfile,
                                                        desc=desc,
                                                        extraargs=eargs,
                                                        conftype=deviceconf,
                                                        enableCheck=False,
                                                        logfile=True)

    # Get this PID for diagnostics
    pid = os.getpid()

    # Print the preamble of this particular instance
    #   (helpful to find starts/restarts when scanning thru logs)
    common.printPreamble(pid, config)

    # Reorganize the configuration to be per-instrument so it's a little
    #   easier to loop over and do other stuff with
    allInsts = confparsers.regroupConfig(config, groupKey='instrument',
                                         ekeys=['devtype', 'extratag'],
                                         delim="+")

    # We need to store our NIHTS compatibility stuff in the above NIHTS
    #   section, to guarantee that it's shared between all devices for that
    #   instrument.  So it needs to be in this level!
    # Also hack in the required password
    compatConfig = confparsers.rawParser("/home/lig/conf/compat.conf")
    try:
        np = compatConfig['nihts']
    except Exception as err:
        print(str(err))
        np = None

    compatClass = compatibility.upfileNIHTS(np)
    allInsts["nihts"].update({"compatibility": compatClass})

    # Check to see if there are any connections/objects to establish
    idbs = connSetup.connIDB(comm)

    # Specify our custom listener that will really do all the work
    #   Since we're hardcoding for the DCTConsumer anyways, I'll take
    #   a bit shortcut and hardcode for the DCT influx database.
    # Someone more clever than I can clean up.
    db = idbs['database-dct']
    amqlistener = listener.MrFreezeConsumer(db=db)

    # TODO: Figure out a way to create a dict of listeners specified
    #   in some creative way. Could add a configuration item to the
    #   file and then loop over it, and change connAMQ accordingly.
    amqtopics = amq.getAllTopics(config, comm, queuerole='master')
    amqs = connSetup.connAMQ(comm, amqtopics, amqlistener=amqlistener)

    # Just hardcode this for now. It's a prototype!
    conn = amqs['broker-dct'][0]
    queue = comm['queue-mrfreeze']

    # Assemble our *initial* schedule of actions. This will be adjusted
    #   by any inputs from the broker once we're in the main loop
    sched = schedule.Scheduler()
    sched = actions.scheduleInstruments(sched, allInsts,
                                        amqs, idbs,
                                        debug=True)

    # Before we start the main loop, query all the defined actions
    #   in turn. This will help avoid triggering alerts/warnings/etc.
    # We need to make sure the connection to the broker is up first,
    #   though, because we need to get the LOIS reply topics connected.
    amqs = amq.checkConnections(amqs, subscribe=True)
    sched.run_all(delay_seconds=0.5)

    # Semi-infinite loop
    while runner.halt is False:
        # Check on our connections
        amqs = amq.checkConnections(amqs, subscribe=True)
        # Make sure we update our hardcoded reference
        conn = amqs['broker-dct'][0]

        # Check for any actions, and do them if it's their time
        print("Checking schedule for pending tasks...")
        sched.run_pending()
        for job in sched.jobs:
            remaining = (job.next_run - datetime.now()).total_seconds()
            print("    %s in %f seconds" % (job.tags, remaining))

        # Check for any updates to those actions, or any commanded
        #   actions in general
        print("Cleaning out the queue...")
        queueActions = amqlistener.emptyQueue()
        print("%d items obtained from the queue" % (len(queueActions)))

        # Process and deal with the things in the queue
        allInsts = actions.queueProcessor(sched, queueActions, allInsts,
                                          conn, queue)

        # Diagnostic output
        nleft = len(amqlistener.brokerQueue.items())
        print("%d items still in the queue" % (nleft))
        print("Done for now!")

        # Consider taking a big nap
        if runner.halt is False:
            print("Starting a big sleep")
            # Sleep for bigsleep, but in small chunks to check abort
            for _ in range(bigsleep):
                time.sleep(1)
                if runner.halt is True:
                    break

    # The above loop is exited when someone sends SIGTERM
    print("PID %d is now out of here!" % (pid))

    # Disconnect from all ActiveMQ brokers
    amq.disconnectAll(amqs)

    # The PID file will have already been either deleted/overwritten by
    #   another function/process by this point, so just give back the
    #   console and return STDOUT and STDERR to their system defaults
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    print("STDOUT and STDERR reset.")


if __name__ == "__main__":
    main()
