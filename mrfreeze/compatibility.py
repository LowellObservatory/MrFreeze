# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 15 Nov 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import


class upfileNIHTS():
    """
    This is the absolute starting point for the NIHTS upfile; further updates
    will change the relevant parts of this, which is then periodically
    written to disk and transferred for the NIHTS LOIS to access.

    This should also have a method to actually make/return the string
    representation of the upfile, so it can be easily written to disk
    and/or transferred to the proper place so LOIS can see it.
    """
    def __init__(self):
        pass


def makeNIHTSUpfile():
    """
    Given the nihts.lig.telemetry packet(s), create and/or update the
    NIHTS "upfile" that LOIS needs to put the data into the FITS headers.

    Here's the format we're trying to recreate:
    { { { NIHTS1_cooler } {20191115 21:03:34} {
        { TempK 054.99 } { Setpt 055.00 } { Maxpow 240.00 } { Minpow 070.00 }
        { Meanpow 128.37 } } }
      { { NIHTS2_cooler } {20191115 21:03:50} {
        { TempK 064.99 } { Setpt 065.00 } { Maxpow 240.00 } { Minpow 070.00 }
        { Meanpow 138.91 } } }
    { { NIHTS_Lakeshore218 } {20191115 21:04:00} {
        { SINK1 +293.36 } { SINK2 +293.15 } { DEWAR +289.56 }
        { FLSHLD +236.62 } { DETBK +83.399 } { BENCH +91.662 }
        { PRISM +90.939 } { INSTRAP +56.716 } } }
    { { NIHTS_Lakeshore325 } {20191115 21:04:12} {
        { GETTER +59.215 } { GSETPT +333.00 } { GHEAT +00.00 }
        { DETECTOR +75.000 } { DSETPT +75.000 } { DHEAT +00.54 } } }
    { { NIHTS_vacgauge } {20191115 21:00:00} { { Torr 1.00E-8 } } } }
    """
    pass
