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
def job1(arg1, arg2, arg3=False):
    """
    """
    print(arg1, arg2, arg3)


@with_logging
@catch_exceptions(cancel_on_failure=False)
def job2(arg1, arg2, arg3=False):
    """
    """
    print(arg1, arg2, arg3)
    print(1/0)


def makeSchedule(s, defInt):
    """
    """
    s.every(defInt).seconds.do(job1, "cheese", "checkers").tag("LMI")
    s.every(defInt).seconds.do(job2, "rats", "potatoes").tag("NIHTS")

    return s


if __name__ == "__main__":
    naptime = 30.

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

        if adjusted is False:
            sObj.clear('LMI')
            sObj.every(30).seconds.do(job1, "cheese", "checkers").tag("LMI")

            adjusted = True
