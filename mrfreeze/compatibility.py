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

from datetime import datetime as dt
from collections import OrderedDict


class upfileNIHTS():
    """
    The compatibility layer between Mr. Freeze and the legacy LOIS/moxad setup
    that is needed because of the "upfile" arrangement that Peter made
    for NIHTS; see https://jumar.lowell.edu/confluence/x/PQBCAg
    """
    def __init__(self, debug=False):
        self.debug = debug

        # This is for compatibility with actions.scheduleDevices()
        self.instrument = "NIHTS"
        self.devtype = 'upfile'
        self.enabled = True

        # Initial starting values so it's not at least None at the get-go
        defaultValue = -9999.
        defaultDate = dt.strptime("20190107T02:10:00.00",
                                  "%Y%m%dT%H:%M:%S.%f")

        # OrderedDict() to keep the order consistent just in case LOIS
        #   is hardcoded to the order of things; I didn't check if that's
        #   actually the case or if I'm too paranoid
        self.xkeys = OrderedDict({"NIHTS1_cooler": sunpowercooler(),
                                  "NIHTS2_cooler": sunpowercooler(),
                                  "NIHTS_Lakeshore218": ls218(),
                                  "NIHTS_Lakeshore325": ls325(),
                                  "NIHTS_vacgauge": vacgauge()})

        # Loop through the sections defined above
        for key in self.xkeys:
            # Set up the values for this section
            sectVals = OrderedDict()
            sectVals.update({"sectTimestamp": defaultDate})
            if debug is True:
                print(key)

            # Now fill in all the rest
            for subkey in self.xkeys[key]:
                outputKey = self.xkeys[key][subkey]
                if debug is True:
                    print("\t", subkey, outputKey)
                sectVals.update({outputKey: defaultValue})

            # Set the base key
            setattr(self, key, sectVals)

    def updateSection(self, sect, fields):
        """
        'sect' must be a string that matches exactly one of the sections
        set up in __init__ otherwise it'll fail.
        """
        if hasattr(self, sect) is False:
            if self.debug is True:
                print("INVALID SECTION! %s not found" % (sect))
        else:
            if self.debug is True:
                print("VALID SECTION! %s found" % (sect))

            print(fields)

            print("Updating NIHTS upfile section %s" % (sect))
            datakeys = self.xkeys[sect]

            # Need this because we need to programatically access
            #   the section which was given as an argument
            updated = getattr(self, sect)
            # Update the section timestamp
            updated['sectTimestamp'] = dt.strptime(fields['TimestampUTC'],
                                                   "%Y-%m-%dT%H:%M:%S.%f")

            for field in fields:
                try:
                    translation = datakeys[field]
                    updated[translation] = fields[field]
                except KeyError:
                    print("Field %s not in upfile translation!" % (field))
                    translation = None

            upfile = self.makeNIHTSUpfile()
            print(upfile)

    def makeNIHTSUpfile(self):
        """
        Create the NIHTS "upfile" that LOIS needs for the FITS headers.
        It's a very specific format, shown below.

        Here's the format we're trying to recreate:
        {
          {
            { NIHTS1_cooler } {20191115 21:03:34} {
              { TempK 054.99 } { Setpt 055.00 }
              { Maxpow 240.00 } { Minpow 070.00 } { Meanpow 128.37 }
            }
          }
          {
            { NIHTS2_cooler } {20191115 21:03:50} {
              { TempK 064.99 } { Setpt 065.00 }
              { Maxpow 240.00 } { Minpow 070.00 } { Meanpow 138.91 }
            }
          }
          {
            { NIHTS_Lakeshore218 } {20191115 21:04:00} {
              { SINK1 +293.36 } { SINK2 +293.15 } { DEWAR +289.56 }
              { FLSHLD +236.62 } { DETBK +83.399 } { BENCH +91.662 }
              { PRISM +90.939 } { INSTRAP +56.716 }
            }
          }
          {
            { NIHTS_Lakeshore325 } {20191115 21:04:12} {
              { GETTER +59.215 } { GSETPT +333.00 } { GHEAT +00.00 }
              { DETECTOR +75.000 } { DSETPT +75.000 } { DHEAT +00.54 }
            }
          }
          {
            { NIHTS_vacgauge } {20191115 21:00:00} {
              { Torr 1.00E-8 }
            }
          }
        }

        Worth noting that it *MUST* be all on one line; the newlines above
        are for clarity only.
        """
        tsFormat = "{%Y%m%d %H:%M:%S}"
        sectBegin = "{ "
        sectEnd = " }"

        # Ok, here we go
        finalForm = ""
        finalForm += sectBegin

        skipableSections = ['debug', 'devtype',
                            'enabled', 'instrument', 'xkeys']

        # We'll loop over the properties
        for sect in self.__dict__:
            # Skip any/all non-output properties
            if sect not in skipableSections:
                sectOutput = sectBegin + sect + sectEnd
                thisSect = getattr(self, sect)
                if sect == "NIHTS_Lakeshore325":
                    numFormat = "%+0.3f"
                elif sect in ["NIHTS1_cooler", "NIHTS2_cooler"]:
                    numFormat = "%0.2f"
                elif sect == "NIHTS_vacgauge":
                    numFormat = "%.4e"
                else:
                    numFormat = "%+0.2f"

                for i, subkey in enumerate(thisSect):
                    if subkey == "sectTimestamp":
                        tsVal = thisSect["sectTimestamp"]
                        # Remember that the needed {} are in the tsFormat!
                        #   (but not the initial space)
                        sectOutput += " " + tsVal.strftime(tsFormat)

                        # There's another section that begins after timestamp
                        sectOutput += " " + sectBegin
                    else:
                        # Doing this on two lines just for line length control
                        printedVal = numFormat % (thisSect[subkey])

                        sectOutput += sectBegin + subkey + " "
                        sectOutput += printedVal
                        sectOutput += sectEnd

                    if i != len(thisSect) - 1 and i != 0:
                        sectOutput += " "

                # Finishing up
                sectOutput += sectEnd
                finalForm += sectBegin + sectOutput + sectEnd + " "

        # .strip() here because we already put in the space immediately above
        finalForm += sectEnd.strip()
        if self.debug is True:
            print(finalForm)

        return finalForm


def vacgauge():
    """
    Unfortunately, case here matters.

    (This one doesn't really need to be checked)
    """
    return {"CMB4Digit": "Torr"}


def sunpowercooler():
    """
    Unfortunately, case here matters.
    """
    defs = OrderedDict({"ColdTipTemp": "TempK",
                        "TTARGET": "Setpt",
                        "MaxPower": "Maxpow",
                        "MinPower": "Minpow",
                        "ActualPower": "Meanpow"})
    return defs


def ls218():
    """
    Unfortunately, case here matters.

    Last checked for accuracy: 20191119 RTH
    """
    defs = OrderedDict({"Sensor1": "SINK1",
                        "Sensor2": "SINK2",
                        "Sensor3": "DEWAR",
                        "Sensor4": "FLSHLD",
                        "Sensor5": "DETBRK",
                        "Sensor6": "BENCH",
                        "Sensor7": "PRISM",
                        "Sensor8": "INSTRAP"})
    return defs


def ls325():
    """
    Unfortunately, case here matters.

    Last checked for accuracy: 20191119 RTH
    """
    defs = OrderedDict({"SensorTempA": "GETTER",
                        "SensorTempB": "DETECTOR",
                        "Setpoint1": "GSETPT",
                        "Setpoint2": "DSETPT",
                        "Heater1": "GHEAT",
                        "Heater2": "DHEAT"})
    return defs
