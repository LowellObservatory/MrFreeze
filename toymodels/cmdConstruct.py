# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 11 Jul 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

# REMEMBER: Call this FROM the top directory so the import doesn't barf!
import sys
sys.path.append(".")

from ligmos import utils

from mrfreeze import parsers
from mrfreeze import publishers


if __name__ == "__main__":
    # inst = 'NIHTS'
    # device = 'sunpowergen2'
    # tag = 'BenchCooler'
    # cmd = 'coldtip'
    # value = None

    inst = 'NIHTS'
    devicetype = 'sunpowergen2'
    tag = 'BenchCooler'
    cmd = 'querydisable'
    value = None

    # Make a packet of the above. It's ok for value to be None.
    msg = publishers.constructCommand(inst, devicetype, tag, cmd,
                                      value=value, debug=True)

    # Parse the packet. Have to do some boilerplate crap first to set up
    headers = {'destination': '/topic/lig.MrFreeze.cmd'}
    tname = headers['destination'].split('/')[-1].strip()

    schemaDict = utils.amq.schemaDicter()
    thisScheme = schemaDict[tname]

    fields = parsers.parserCmdPacket(headers, msg, schema=thisScheme)
    print(fields)

    inst = fields['request_instrument'].lower()
    device = fields['request_devicetype'].lower()
    tag = fields['request_tag']
    cmd = fields['request_command']
    arg = fields['request_argument']
    print("Message parsed as:")
    print("Instrument: %s" % (inst))
    print("DeviceType: %s" % (device))
    print("AdditionalTag: %s" % (tag))
    print("Command: %s" % (cmd))
    print("CommandArgument: %s" % (arg))
