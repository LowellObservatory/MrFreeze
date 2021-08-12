# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 27 Jun 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import time
import functools

import serial
import schedule

from ligmos.utils import ssh

from . import devices
from . import publishers as pubs
from . import serialcomm as scomm


def catch_exceptions(cancel_on_failure=False):
    """
    Decorator ... does what's on the tin
    """
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


@catch_exceptions(cancel_on_failure=False)
def cmd_serial(dvice, dbObj, bkObj, compat=None, debug=False):
    """
    Define and route messages to/from serial attached devices
    """
    # Some quick defines:
    # Supported Sunpower Cryocooler devices
    sunpowerset = ['sunpowergen1', 'sunpowergen2']

    # Supported Lake Shore devices
    lsset = ['lakeshore218', 'lakeshore325']

    # Supported Newport devices
    newportset = ['newport_ithx', 'newport_isd-tc']

    # Go and get commands that are valid for the device
    msgs = devices.defaultQueryCommands(device=dvice.devtype)

    # Now send the commands
    try:
        reply = scomm.serComm(dvice.devhost, dvice.devport,
                              msgs, timeout=0.25, debug=debug)
    except serial.SerialException as err:
        print("Badness 10000")
        print(str(err))
        reply = None

    try:
        if reply is not None:
            if dvice.devtype.lower() == 'vactransducer_mks972b':
                compat = pubs.publish_MKS972b(dvice, reply,
                                              db=dbObj, broker=bkObj,
                                              compat=compat, debug=debug)
            elif dvice.devtype.lower() in sunpowerset:
                compat = pubs.publish_Sunpower(dvice, reply,
                                               db=dbObj, broker=bkObj,
                                               compat=compat, debug=debug)
            elif dvice.devtype.lower() in lsset:
                compat = pubs.publish_LSThing(dvice, reply,
                                              db=dbObj, broker=bkObj,
                                              compat=compat, debug=debug)
            elif dvice.devtype.lower() in newportset:
                compat = pubs.publish_Newport(dvice, reply,
                                              db=dbObj, broker=bkObj,
                                              compat=compat, debug=debug)
            if compat is not None:
                upf = compat.makeNIHTSUpfile()
                print(upf)
                # Now push the upfile out to the place it needs to be
                with open(compat.params['upfnme'], "w") as f:
                    f.write(upf)

                sshNIHTS = ssh.SSHWrapper(host=compat.params['host'],
                                          username=compat.params['user'],
                                          password=compat.params['pw'])
                sshNIHTS.openSFTP()
                lloc = "./%s" % (compat.params['upfnme'])
                rloc = "%s/%s" % (compat.params['upfloc'],
                                  compat.params['upfnme'])
                sshNIHTS.putFile(lloc, rloc)
                sshNIHTS.closeSFTP()
                sshNIHTS.closeConnection()

    except Exception as err:
        print("Unable to parse instrument response!")
        print(str(err))


@catch_exceptions(cancel_on_failure=False)
def cmd_loisgettemp(dvice, bkObj):
    """
    Periodically send messages to the broker at bkObj to LOIS to 'gettemp'

    This is really all there is; the reply is monitored in the STOMP listener
    defined in the main calling code, and since STOMP runs that in its own
    thread it'll happen in the background compared to this loop here.
    """
    cmd = 'gettemp'
    print("Sending %s to broker topic %s" % (cmd, dvice.devbrokercmd))
    bkObj.publish(dvice.devbrokercmd, cmd)


def scheduleInstruments(sched, allInsts, amqs, idbs, debug=False):
    """
    """
    # Scheduling of individual devices happens fast, so all the actions
    #   will be piled up in scheduled time.  Offset them by a small amount to
    #   account for the actual time needed to send/process the reply and
    #   then move on to the next scheduled action!
    temporalOffset = 2

    # Loop thru the different instrument sets
    for inst in allInsts:
        try:
            # This makes sure we have a reference to the base-level instrument
            #   compatibility file in each specific device file.
            # This could (and should) be cleaned up to be less convoluted!
            compat = allInsts[inst]['compatibility']
        except KeyError:
            # I *think* keyerror is the right one to catch?
            compat = None

        for dtag in allInsts[inst]:
            dvice = allInsts[inst][dtag]

            # Check to make sure this device's query is actually set as enabled
            if dvice.enabled is True and dvice.devtype != "upfile":
                if debug is True:
                    print("Scheduling %s+%s+%s" % (dvice.instrument,
                                                   dvice.devtype,
                                                   dvice.extratag))

                # Set up some easy-access things for the scheduler
                #   schedTags *must* be hashable, so it can't be a list.
                #   Make it specific so it can be sensibly cancelled
                schedTag = "%s+%s" % (dvice.instrument, dvice.devtype)
                if dvice.extratag is not None:
                    schedTag += "+%s" % (dvice.extratag)

                interval = int(dvice.queryinterval)

                # Get our specific database connection object
                try:
                    dbObj = idbs[dvice.database]
                except KeyError:
                    dbObj = None

                # Now try to get our broker connection object
                try:
                    # [1] is the listener, and we don't need that here
                    bkObj = amqs[dvice.broker][0]
                except KeyError:
                    bkObj = None

                # SPECIAL handling for this one, since it's not a serial
                #   device but a broker command topic
                if dvice.devtype.lower() == 'arc-loisgettemp':
                    print("Scheduling 'gettemp' for %s every %d seconds" %
                          (dvice.instrument, interval))
                    sched.every(interval).seconds.do(cmd_loisgettemp,
                                                     dvice,
                                                     bkObj).tag(schedTag)
                else:
                    print("Scheduling '%s' for %s every %d seconds" %
                          (dvice.devtype, dvice.instrument, interval))
                    sched.every(interval).seconds.do(cmd_serial,
                                                     dvice, dbObj, bkObj,
                                                     compat=compat,
                                                     debug=debug).tag(schedTag)

                # If we're in here, we scheduled an action. Pause so they
                #   don't stack up too close. Do it in *here* rather than
                #   the main dvice loop to ignore disabled devices!
                time.sleep(temporalOffset)
            else:
                print("Device %s is disabled! Skipping it." % (dvice.devtype))

    return sched


def queueProcessor(sched, queueActions, allInsts, conn, queue):
    """
    """
    # Do some stuff!
    for action in queueActions:
        # Parse the incoming action by hand since it's a simple deal
        ainst = action['request_instrument']
        adevc = action['request_devicetype']
        atag = action['request_tag']
        acmd = action['request_command']
        aarg = action['request_argument']

        # Do a simple check to see if it's a command for Nora
        if acmd.lower() == 'advertise':
            print("Advertising the current actions...")
            adpacket = pubs.advertiseConfiged(allInsts)
            conn.publish(queue.replytopic, adpacket)
        else:
            # All other command types are specific to an instrument
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
                schedTag = "%s+%s" % (ainst, adevc)
                if atag is not None:
                    schedTag += "+%s" % (atag)
                if acmd.lower() == "queryenable":
                    print("Enabling %s %s" % (ainst, cdest.lower()))
                    selInst.enabled = True
                    # Schedule this instrument

                elif acmd.lower() == "querydisable":
                    print("Disabling %s %s" % (ainst, cdest.lower()))
                    selInst.enabled = False
                    # Remove this instrument from the schedule if it's there

                elif acmd.lower() == "devicehost":
                    print("Setting device host to %s" % (aarg))
                    selInst.devhost = aarg
                    # Cancel this instrument from the schedule if it's there,
                    #   then reschedule it

                elif acmd.lower() == "deviceport":
                    print("Setting device port to %s" % (aarg))
                    selInst.devport = aarg
                    # Cancel this instrument from the schedule if it's there,
                    #   then reschedule it

                else:
                    # Check to see if the command is in the remoteAPI
                    #   that we defined for the devices
                    # https://github.com/LowellObservatory/MrFreeze/issues/8
                    pass

                # Now store this instrument back in the main set,
                #   so we can use any updates that just happened
                allInsts[ainst][cdest] = selInst

    return allInsts


def scheduleManipulation(sched, tag, action=None):
    """
    """
    if action is None:
        print("No change to the schedule was requested!")
    else:
        if action.lower() == 'enable':
            pass
        elif action.lower() == 'disable':
            pass
        elif action.lower() == 'reschedule':
            pass