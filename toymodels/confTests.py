# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 23 Jul 2018
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import ligmos


confps = ligmos.utils.confparsers
cfile = "./mrfreeze.conf"
ctype = ligmos.utils.common.deviceTarget

idict, commconfig = confps.getActiveConfiguration(cfile,
                                                  conftype=ctype,
                                                  debug=True)

for each in idict:
    inst = idict[each]
    print(inst.name)
    print(inst.__dict__)
