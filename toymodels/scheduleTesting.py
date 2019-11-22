# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 13 Sep 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import time
import functools

import schedule


class passedToSchedule():
    def __init__(self):
        self.var1 = 1
        self.var2 = 0


def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


def with_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print('LOG: Running job "%s"' % func.__name__)
        result = func(*args, **kwargs)
        print('LOG: Job "%s" completed' % func.__name__)
        return result
    return wrapper


@with_logging
def job1(dvice, arg3=False):
    """
    """
    print("Job1 %d %d" % (dvice.var1, dvice.var2))
    dvice.var1 = 42
    dvice.var2 += 1
    print("Job1 update %d %d" % (dvice.var1, dvice.var2))


@with_logging
@catch_exceptions(cancel_on_failure=False)
def job2(dvice, arg3=False):
    """
    """
    print("Job2 %d %d" % (dvice.var1, dvice.var2))
    dvice.var1 = 43
    dvice.var2 += 1
    print("Job2 update %d %d" % (dvice.var1, dvice.var2))


def makeSchedule(s, defInt):
    """
    """
    p2s = passedToSchedule()
    s.every(defInt).seconds.do(job1, p2s).tag("LMI")
    s.every(defInt).seconds.do(job2, p2s).tag("NIHTS")

    return s


if __name__ == "__main__":
    naptime = 15.

    defInt = 10

    sObj = schedule.Scheduler()
    sObj = makeSchedule(sObj, defInt)

    adjusted = False

    while True:
        for job in sObj.jobs:
            print(job)

        i = 0
        while i <= naptime-1:
            sObj.run_pending()
            print("Checked schedule for pending tasks, napped for %d" % (i+1))

            time.sleep(1)
            i += 1

        # if adjusted is False:
        #     sObj.clear('LMI')
        #     sObj.every(30).seconds.do(job1, p2s).tag("LMI")

        #     adjusted = True
