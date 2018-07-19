# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 25 May 2018
#
#  @author: rhamilton

"""workerSetup: Common core for Data Servants

This is for codes which are designed to live on one machine,
and do some actions possibly passing things to other workers.

There can only be one 'procname' instance running on a machine,
controlled via a PID file in /tmp/ as well as some command line options to
kill/restart the process.
"""

from __future__ import division, print_function, absolute_import

import os
import time
import signal
import argparse as argp

from pid import PidFile, PidFileError

from ligmos import utils


def parseArguments(conf=None, prog=None, passes=None, log=None, descr=None):
    """Setup command line arguments that everyone will use.
    """
    fclass = argp.ArgumentDefaultsHelpFormatter

    if descr is None:
        description = "ADataServant: Doing Things That Are Helpful"
    else:
        description = descr

    parser = argp.ArgumentParser(description=description,
                                 formatter_class=fclass,
                                 prog=prog)

    if conf is None:
        parser.add_argument('-c', '--config', metavar='/path/to/file.conf',
                            type=str,
                            help='File for configuration information',
                            default='./programname.conf', nargs='?')
    else:
        parser.add_argument('-c', '--config', metavar='/path/to/file.conf',
                            type=str,
                            help='File for configuration information',
                            default=conf, nargs='?')

    if passes is not None:
        parser.add_argument('-p', '--passes', metavar='/path/to/file.conf',
                            type=str,
                            help='File for instrument password information',
                            default='./passwords.conf', nargs='?')

    if log is None:
        parser.add_argument('-l', '--log', metavar='/path/to/file.log',
                            type=str,
                            help='File for logging of messages',
                            default='/tmp/programname.log', nargs='?')
    else:
        parser.add_argument('-l', '--log', metavar='/path/to/file.log',
                            type=str,
                            help='File for logging of messages',
                            default=log, nargs='?')

    parser.add_argument('-k', '--kill', action='store_true',
                        help='Kill an already running instance',
                        default=False)

    parser.add_argument('-k9', '--kill9', action='store_true',
                        help='Kill -9 an already running instance',
                        default=False)

    # Note: Need to specify dest= here since there are multiple long options
    #   (and I prefer the fun option name in the code)
    lhtext = 'Kill another instance, then take its place'
    parser.add_argument('-r', '--restart', '--fratricide', action='store_true',
                        help=lhtext, dest='fratricide',
                        default=False)

    parser.add_argument('-n', '--nlogs', type=int,
                        help='Number of previous logs to keep after rotation',
                        default=30, nargs=1)

    parser.add_argument('--debug', action='store_true',
                        help='Print extra debugging messages while running',
                        default=False)

    args = parser.parse_args()

    return args


def toServeMan(procname, conffile, passfile, log, parser=parseArguments,
               confparser=utils.confparsers.getActiveConfiguration,
               logfile=True, desc=None):
    """Main entry point, which also handles arguments.

    ... it's - it's a cookbook!

    This will parse the arguments specified in XXXXXXXX

    Args:
        procname (:obj:`str`)
            Process name to search for another running instance.
        logfile (:obj:`bool`, optional)
            Bool to control whether we write to a logfile (with rotation)
            or just dump everything to STDOUT. Useful for debugging.
            Defaults to True.
        parser (:obj:`function`)
            Parser function that interprets options.
            Should be the reference to the name of the relevant function
            since it's called here.

    Returns:
        idict (:class:`dataservants.utils.common.InstrumentHost`)
            Class containing instrument machine target information
            populated via :func:`dataservants.utils.confparsers.parseInstConf`.
        args (:class:`argparse.Namespace`)
            Class containing parsed arguments, returned from
            :func:`dataservants.iago.parseargs.parseArguments`.
        runner (:class:`dataservants.utils.common.HowtoStopNicely`)
            Class containing logic to catch ``SIGHUP``, ``SIGINT``, and
            ``SIGTERM``.  Note that ``SIGKILL`` is uncatchable.
    """
    # Time to wait after a process is murdered before starting up again.
    #   Might be over-precautionary, but it gives time for the previous process
    #   to write whatever to the log and then close the file nicely.
    killSleep = 30

    # Setup termination signals
    runner = utils.common.HowtoStopNicely()

    # Setup argument parsing *before* logging so help messages go to stdout
    #   NOTE: This function sets up the default values when given no args!
    #   Also check for kill/fratracide options so we can send SIGTERM to the
    #   other processes before trying to start a new one
    #   (which PidFile would block)
    #   ALSO NOTE: If you give a custom one, it needs (at a minimum):
    #       fratricide|kill, log, nlogs, config, passes
    args = parser(conf=conffile, passes=passfile, prog=procname,
                  log=log, descr=desc)

    pid = utils.pids.check_if_running(pname=procname)

    # Slightly ugly logic
    if pid != -1:
        if (args.fratricide is True) or (args.kill is True) or\
           (args.kill9 is True):
            if args.kill9 is False:
                print("Sending SIGTERM to %d" % (pid))
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception as err:
                    print("Process not killed; why?")
                    # Returning STDOUT and STDERR to the console/whatever
                    utils.common.nicerExit(err)
            else:
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception as err:
                    print("Process not killed; why?")
                    # Returning STDOUT and STDERR to the console/whatever
                    utils.common.nicerExit(err)

            # If the SIGTERM took, then continue onwards. If we're killing,
            #   then we quit immediately. If we're replacing, then continue.
            if args.kill is True:
                print("Sent SIGTERM to PID %d" % (pid))
                # Returning STDOUT and STDERR to the console/whatever
                utils.common.nicerExit()
            elif args.kill9 is True:
                print("Sent SIGKILL to PID %d" % (pid))
                # Returning STDOUT and STDERR to the console/whatever
                utils.common.nicerExit()
            else:
                print("LOOK AT ME I'M THE ALIEN COOK NOW")
                print("%d second pause to allow the other process to exit." %
                      (killSleep))
                time.sleep(killSleep)
        else:
            # If we're not killing or replacing, just exit.
            #   But return STDOUT and STDERR to be safe
            utils.common.nicerExit()
    else:
        if args.kill is True:
            print("No %s process to kill!" % (procname))
            print("Seach for it manually:")
            print("ps -ef | grep -i '%s'" % (procname))
            utils.common.nicerExit()

    if logfile is True:
        # Setup logging (optional arguments shown for clarity)
        utils.logs.setup_logging(logName=args.log, nLogs=args.nlogs)

    # Read in the configuration file and act upon it
    idict = confparser(args.config, parseHardFail=False)

    # If there's a password file, associate that with the above
    if passfile is not None:
        idict = utils.confparsers.parsePassConf(args.passes, idict,
                                                debug=args.debug)

    return idict, args, runner
