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

from collections import OrderedDict


class upfileNIHTS():
    """
    Contains the mapping between cryo-device channels/sensors and
    physical objects in/on the instrument.

    These are used in the NIHTS "upfile" and that's why there're in here.
    """
    def __init__(self):
        """
        cooler 1 == detector cooler
        cooler 2 == bench cooler
        """
        self.cooler1 = {"NIHTS1_cooler": self.sunpowercooler()}
        self.cooler2 = {"NIHTS2_cooler": self.sunpowercooler()}
        self.temps_bch = {"NIHTS_Lakeshore218": self.ls218()}
        self.temps_det = {"NIHTS_Lakeshore325": self.ls325()}
        self.vacuum = {"NIHTS_vacgauge": self.vacgauge()}

    def vacgauge(self):
        """
        (This one doesn't really need to be checked)
        """
        return {"cmb4digit": "Torr"}

    def sunpowercooler(self):
        """
        """
        defs = OrderedDict({"coldtiptemp": "TempK",
                            "ttarget": "Setpt",
                            "maxpower": "Maxpow",
                            "minpower": "Minpow",
                            "actualpower": "Meanpow"})
        return defs

    def ls218(self):
        """
        Last checked for accuracy: 20191119 RTH
        """
        defs = OrderedDict({"sensor1": "SINK1",
                            "sensor2": "SINK2",
                            "sensor3": "DEWAR",
                            "sensor4": "FLSHLD",
                            "sensor5": "DETBRK",
                            "sensor6": "BENCH",
                            "sensor7": "PRISM",
                            "sensor8": "INSTRAP"})
        return defs

    def ls325(self):
        """
        Last checked for accuracy: 20191119 RTH
        """
        defs = OrderedDict({"sensortempa": "GETTER",
                            "sensortempb": "DETECTOR",
                            "setpoint1": "GSETPT",
                            "setpoint2": "DSETPT",
                            "heater1": "GHEAT",
                            "heater2": "DHEAT"})
        return defs


def makeNIHTSUpfile():
    """
    Given the nihts.lig.telemetry packet(s), create and/or update the
    NIHTS "upfile" that LOIS needs to put the data into the FITS headers.

    Here's the format we're trying to recreate:
    { { { NIHTS1_cooler } {20191115 21:03:34} {
        { TempK 054.99 } { Setpt 055.00 }
        { Maxpow 240.00 } { Minpow 070.00 } { Meanpow 128.37 } } }
      { { NIHTS2_cooler } {20191115 21:03:50} {
        { TempK 064.99 } { Setpt 065.00 }
        { Maxpow 240.00 } { Minpow 070.00 } { Meanpow 138.91 } } }
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
