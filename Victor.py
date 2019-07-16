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
    logfile = './mrfreeze_victor.log'
    desc = "Victor: The Cruel Master of the Cold Stuff"
    eargs = None

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

            amqlistener = amq.silentSubscriber()
            amqtopics = amq.getAllTopics(config, comm)
            amqs = connSetup.connAMQ(comm, amqtopics, amqlistener=amqlistener)

            # Just hardcode this for now. It's a prototype!
            conn = amqs['broker-dct'][0]
            queue = comm['queue-mrfreeze']

            # Semi-infinite loop
            while runner.halt is False:
                # Check on our connections
                amqs = amq.checkConnections(amqs, subscribe=True)

                # Leaving this in a loop for testing for now; Victor will
                #   turn into a single-shooter when he's ready
                inst = 'NIHTS'
                device = 'sunpowergen2'
                tag = 'BenchCooler'
                cmd = 'querydisable'
                value = None

                cmdpak = mrfreeze.publishers.constructCommand(inst, device,
                                                              tag, cmd,
                                                              value=value,
                                                              debug=True)

                conn.publish(queue.cmdtopic, cmdpak)

                # Consider taking a big nap
                if runner.halt is False:
                    print("Starting a big sleep")
                    # Sleep for bigsleep, but in small chunks to check abort
                    for i in range(6):
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
