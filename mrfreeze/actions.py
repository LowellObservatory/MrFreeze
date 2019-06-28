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
            bkObj = amqs[dvice.broker][0]
        except KeyError:
            bkObj = None

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
                elif dvice.devtype.lower() in ['sunpowergen1', 'sunpowergen2']:
                    pubs.publish_Sunpower(dvice, reply,
                                          db=dbObj, broker=bkObj,
                                          debug=debug)
                elif dvice.devtype.lower() in ['lakeshore218', 'lakeshore325']:
                    pubs.publish_LSThing(dvice, reply,
                                         db=dbObj, broker=bkObj,
                                         debug=debug)
                elif dvice.devtype.lower() == 'arc-loisgettemp':
                    pass
        except Exception as err:
            print("Unable to parse instrument response!")
            print(str(err))
