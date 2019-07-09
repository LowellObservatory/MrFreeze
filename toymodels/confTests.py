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

import os

from ligmos.workers import workerSetup
from ligmos.utils import amq, common, classes, confparsers


# Define the default files we'll use/look for. These are passed to
#   the worker constructor (toServeMan).
devices = './mrfreeze.conf'
deviceconf = classes.instrumentDeviceTarget
passes = './passwords.conf'
logfile = './mrfreeze_nora.log'
desc = "Nora: Heart of the DCT Instrument Cooler Manager"
eargs = None

mynameis = os.path.basename(__file__)
if mynameis.endswith('.py'):
    mynameis = mynameis[:-3]

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

# Reorganize the configuration to be per-instrument
groupKey = 'instrument'
perInst = confparsers.regroupConfig(config, groupKey=groupKey)

print(perInst)
