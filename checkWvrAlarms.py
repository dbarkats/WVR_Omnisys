#! /usr/bin/env python

from wvrComm import wvrComm

# Error codes obtained from Section 3.3 of WVR Operation Manual.
# /calibration/wvr/AFFMAN001A_Operation_Manual.pdf

BYTE_ERRS = ['A control point was requested with the wrong number of bytes']

CTRL_ERRS = ['A control point was requested while not in the proper mode']

V12_ERRS = ['The +12V rail is switched off due to a tripped temperature protection']

CURR_ERRS = ['+12V supply current out of range',
             '+6V supply current out of range',
             '-6V supply current out of range',
             'Chopper wheel current out of range']

VOLT_ERRS = ['+12V supply voltage out of range',
             '+6V supply voltage out of range',
             '-6V supply voltage out of range']

TEMP_ERRS = ['Hot load over-temperature protection tripped',
             'Cold load over-temperature tripped',
             'CTRL over-temperature tripped',
             'BE over-temperature tripped',
             'CS over-temperature tripped']

TEST_ERRS = ['Chopper wheel error',
             'Calibration file error',
             'LO error']

# Error types in the order returned by getWvrAlarms()
ERR_CLASSES = [BYTE_ERRS, CTRL_ERRS, V12_ERRS, CURR_ERRS,
               VOLT_ERRS, TEMP_ERRS, TEST_ERRS]

def get_wvr_errors(lock=None):
    """
    Prints WVR errors in a human-readable way.
    If a lock is provided, will try to obtain lock
    before reading errors.
    """

    if lock:
        with lock:
            wvrc = wvrComm()
            errs = wvrc.getWvrAlarms()
    else:
        wvrc = wvrComm()
        errs = wvrc.getWvrAlarms()
    
    for i in range(len(ERR_CLASSES)):
        ERR_CLASS = ERR_CLASSES[i]
        err = errs[i]
        for j in range(len(ERR_CLASS)):
            if 1<<j & err:
                try:
                    print ERR_CLASS[j]
                except IndexError:
                    print "Unknown Error"

if __name__ == '__main__':
    get_wvr_errors()
