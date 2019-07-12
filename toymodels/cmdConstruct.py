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


def constructCommand(inst, device, tag, cmd, value=None, debug=False):
    """
    """
    mstr = "Command"
    fields = {}

    # I'm keeping this super simple, just a set of tags under the root tag
    fields.update({"Instrument": inst})
    fields.update({"Device": device})
    fields.update({"Tag": tag})
    fields.update({"Command": cmd})
    fields.update({"Value": value})

    pak = publishers.constructXMLPacket(mstr, fields,
                                        rootTag="MrFreezeCommunique",
                                        debug=debug)

    return pak


if __name__ == "__main__":
    inst = 'NIHTS'
    device = 'sunpowergen2'
    tag = 'BenchCooler'
    cmd = 'coldtip'
    value = None

    # Make a packet of the above. It's ok for value to be None.
    msg = constructCommand(inst, device, tag, cmd, value=value, debug=True)

    # Parse the packet. Have to do some boilerplate crap first to set up
    headers = {'destination': '/topic/lig.MrFreeze.cmd'}
    tname = headers['destination'].split('/')[-1].strip()

    schemaDict = utils.amq.schemaDicter()
    thisScheme = schemaDict[tname]

    fields = parsers.parserCmdPacket(headers, msg, schema=thisScheme)
