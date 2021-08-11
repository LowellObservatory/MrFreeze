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
from uuid import uuid4

from ligmos.workers import workerSetup, connSetup
from ligmos.utils import amq, common, classes, confparsers

from mrfreeze import publishers


def main():
    """
    """
    # Define the default files we'll use/look for. These are passed to
    #   the worker constructor (toServeMan).
    devices = './config/mrfreeze.conf'
    deviceconf = classes.instrumentDeviceTarget
    passes = './config/passwords.conf'
    logfile = './mrfreeze_victor.log'
    desc = "Victor: The Cruel Master of the Cold Stuff"
    eargs = None
    logenable = False

    # Interval between successive runs of the polling loop (seconds)
    bigsleep = 1

    # config: dictionary of parsed config file
    # comm: common block from config file
    # args: parsed options
    # runner: class that contains logic to quit nicely
    config, comm, _, runner = workerSetup.toServeMan(devices,
                                                     passes,
                                                     logfile,
                                                     desc=desc,
                                                     extraargs=eargs,
                                                     conftype=deviceconf,
                                                     enableCheck=False,
                                                     logfile=logenable)

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

    print("Config:")
    print(allInsts)

    # Check to see if there are any connections/objects to establish
    idbs = connSetup.connIDB(comm)

    # Specify our custom listener that will really do all the work
    #   Since we're hardcoding for the DCTConsumer anyways, I'll take
    #   a bit shortcut and hardcode for the DCT influx database.
    # Someone more clever than I can clean up.
    db = idbs['database-dct']
    amqlistener = amq.ParrotSubscriber(dictify=False)
    amqtopics = amq.getAllTopics(config, comm, queuerole='client')
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

        # Leaving this in a loop for testing for now; Victor will
        #   turn into a single-shooter when he's ready
        # inst = 'NIHTS'
        # device = 'sunpowergen2'
        # tag = 'BenchCooler'
        # cmd = 'querydisable'
        # value = None

        # cmdpak = mrfreeze.publishers.constructCommand(inst, device,
        #                                               tag, cmd,
        #                                               value=value,
        #                                               debug=True)
        cmd_id = str(uuid4())
        cmd = 'advertise'
        inst = 'all'
        device = 'all'
        tag = None
        value = None

        cmdpak = publishers.constructCommand(inst, device,
                                             tag, cmd,
                                             value=value,
                                             cmd_id=cmd_id,
                                             debug=True)

        conn.publish(queue.cmdtopic, cmdpak)

        # Consider taking a big nap
        if runner.halt is False:
            print("Starting a big sleep")
            # Sleep for bigsleep, but in small chunks to check abort
            for _ in range(bigsleep):
                time.sleep(1)
                if runner.halt is True:
                    break
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
