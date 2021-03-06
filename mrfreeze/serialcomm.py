# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 24 May 2018
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import datetime as dt

import serial


def encoder(msg):
    """
    """
    if isinstance(msg, str):
        # msg = msg + "\r\n"
        msg = msg.encode("utf-8")

    return msg


def read_all(port, chunk_size=1024):
    """Read all characters on the serial port and return them."""
    # https://stackoverflow.com/a/47614497
    if not port.timeout:
        raise TypeError('Port needs to have a timeout set!')

    read_buffer = b''

    while True:
        # Read in chunks. Each chunk will wait as long as specified by
        # timeout. Increase chunk_size to fail quicker
        byte_chunk = port.read(size=chunk_size)
        read_buffer += byte_chunk
        if not len(byte_chunk) == chunk_size:
            break

    return read_buffer


def serWriter(ser, msg):
    """
    """
    try:
        nwritten = ser.write(msg)
        if nwritten != len(msg):
            print("Wrote less bytes than in the message?")
        else:
            print("Good write: %s" % (str(msg)))
    except Exception as err:
        print(str(err))


def serComm(host, port, cmds, debug=False):
    """
    WARNING: By using just a plain old "socket://" URL below, the connection
    connection is NOT encrypted and NO authentication is supported!
    Only use it in trusted environments.

    If we want to use authentication and all that jazz, the box that
    the device is plugged into at the DCT must be reconfigured!  Right now
    they're all set up as TCP servers on each port rather than RFC2217 ports.
    """
    allreplies = {}
    hosturl = "socket://%s:%s" % (host, port)
    with serial.serial_for_url(hosturl, write_timeout=1., timeout=1.) as ser:
        if isinstance(cmds, dict):
            # NOTE: cmds should be a dict mapping a description to the
            #   actual command string that is sent. The description is
            #   used to tag the reply for later processing so make it good.
            for each in cmds:
                msg = encoder(cmds[each])
                serWriter(ser, msg)
                # Get the time right after we sent the message
                t = dt.datetime.utcnow()
                # print(t.strptime("%Y-%m-%dT%H:%M:%S.%f UTC"))

                # Get the answer; it'll take timeout seconds to return
                byteReply = read_all(ser)
                if debug is True:
                    print("%d bytes recieved in response" % (len(byteReply)))
                    print(byteReply)

                # Store the stuff for returning
                allreplies.update({each: [byteReply, t]})
        else:
            print("Commands need to be given as a dict! Ignoring %s" % (cmds))

        return allreplies
