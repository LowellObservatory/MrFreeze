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

import serial

from . import devices
from . import publishers as pubs
from . import serialcomm as scomm


def queryAllDevices(config, amqs, idbs, debug=False):
    """
    """
    # Some quick defines:
    # Supported Sunpower Cryocooler devices
    sunpowerset = ['sunpowergen1', 'sunpowergen2']

    # Supported Lake Shore devices
    lsset = ['lakeshore218', 'lakeshore325']

    # Loop thru the different instrument sets
    for vice in config:
        dvice = config[vice]

        # Get our specific database connection object
        try:
            dbObj = idbs[dvice.database]
        except KeyError:
            dbObj = None

        # Now try to get our broker connection object
        try:
            # [1] is the listener, and we don't need that at this point
            bkObj = amqs[dvice.broker][0]
        except KeyError:
            bkObj = None

        # SPECIAL handling for this one, since it's not a serial device
        #   but a broker command topic
        if dvice.devtype.lower() == 'arc-loisgettemp':
            cmd = 'gettemp'
            # This is really all there is; the reply is monitored in the
            #   STOMP listener defined in the main calling code, and
            #   since STOMP runs that in its own thread it'll happen in
            #   the background compared to this loop here.
            print("Sending %s to broker topic %s" % (cmd, dvice.devbrokercmd))
            bkObj.publish(dvice.devbrokercmd, cmd)
        else:
            # Go and get commands that are valid for the device
            msgs = devices.queryCommands(device=dvice.devtype)

            # Now send the commands
            try:
                reply = scomm.serComm(dvice.devhost, dvice.devport,
                                      msgs, debug=debug)
            except serial.SerialException as err:
                print("Badness 10000")
                print(str(err))
                reply = None

            try:
                if reply is not None:
                    if dvice.devtype.lower() == 'vactransducer_mks972b':
                        pubs.publish_MKS972b(dvice, reply,
                                             db=dbObj, broker=bkObj,
                                             debug=debug)
                    elif dvice.devtype.lower() in sunpowerset:
                        pubs.publish_Sunpower(dvice, reply,
                                              db=dbObj, broker=bkObj,
                                              debug=debug)
                    elif dvice.devtype.lower() in lsset:
                        pubs.publish_LSThing(dvice, reply,
                                             db=dbObj, broker=bkObj,
                                             debug=debug)
            except Exception as err:
                print("Unable to parse instrument response!")
                print(str(err))
