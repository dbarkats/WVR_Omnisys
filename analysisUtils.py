#!/usr/bin/env python
#
"""
This set of libraries, analysisUtils.py, is a collection of often useful
python  functions.  It is an open package for anyone
on the science team to add to and generalize (and commit).  A few
practices will allow us to keep this useful.

1) Write the routines as generally as you can.

2) Before fundamentally changing the default behavior of a function
or class, consider your coworkers.  Do not modify the default behavior
without extreme need and warning.  If you need to modify it quickly,
consider a separate version until the versions can be blended (but please
do try to do the blending!).

3) There is a comment structure within the routines.  Please keep this
for additions because the documentation is automatically generated from
these comments.
 
All examples assume you have imported the library to aU, as import
analysisUtils as aU. You can of course do whatever you like, but the
examples will thus have to be modified.

Thanks and good luck!  If you have any questions, bother Denis 
Denis Barkats, 20160325
"""

if 1 :
    import os
    import shutil
    import distutils.spawn # used in class linfit to determine if dvipng is present
    import sys
    #import re
    #from types import NoneType
    #import math
    #import binascii # used for debugging planet()
    #from mpfit import mpfit
    from pylab import *
    #from numpy.fft import fft
    #import fnmatch, pickle, traceback, copy as python_copy # needed for editIntents
    #import scipy as sp
    import time as timeUtilities
    if (np.__version__ < '1.9'):
        import scipy.signal as spsig
        from scipy.interpolate import splev, splrep
if 0:
    import scipy.special # for Bessel functions
    import scipy.odr # for class linfit
    import string
    import struct # needed for pngWidthHeight
    import glob
    import readscans as rs
    import datetime
    import tmUtils as tmu
    import compUtils  # used in class SQLD
    #import pytz  # used in computeUTForElevation
    from scipy.special import erf, erfc  # used in class Atmcal
    from scipy import ndimage
    from scipy import polyfit
    from scipy import optimize # used by class linfit
    import random  # used by class linfit
    import matplotlib.ticker # used by plotWeather
    from matplotlib import rc # used by class linfit
    from matplotlib.figure import SubplotParams
    from matplotlib.ticker import MultipleLocator # used by plotPointingResults
    import commands  # useful for capturing stdout from a system call
    import warnings
    import csv # used by getALMAFluxcsv
    import StringIO # needed for getALMAFluxcsv
    import fileIOPython as fiop
    from scipy.stats import scoreatpercentile, percentileofscore
    import types
    import operator
    import XmlObjectifier
    from xml.dom import minidom
    import subprocess
    import urllib2
    import itertools
    import calDatabaseQuery  # used by searchFlux
    import socket            # used by searchFlux to set tunnel default
    import rootFinder  # functions for solving quadratic and cubic polynomial roots
    try:
        import pyfits # needed for getFitsBeam
        pyfitsPresent = True
    except:
        pyfitsPresent = False
"""
Constants that are sometimes useful.  Warning these are cgs, we might want to change them
to SI given the propensity in CASA to use SI.
"""
h=6.6260755e-27
k=1.380658e-16
c=2.99792458e10
c_mks=2.99792458e8
jy2SI=1.0e-26
jy2cgs=1.0e-23
pc2cgs=3.0857e18
au2cgs=1.4960e13
solmass2g=1.989e33
earthmass2g=5.974e27
solLum2cgs = 3.826e33
mH = 1.673534e-24
G  = 6.67259e-8
Tcmb = 2.725


def aggregate(object):
    """
    This function checks whether the object is a list, and if it is not,
    it wraps it in a list.
    """
    if type(object) == type([]) or type(object) == type(array(1)):
        return object
    else:
        return [object]


def smooth(x, window_len=10, window='hanning'):
    """
    smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the beginning and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t = linspace(-2,2,0.1)
    x = sin(t)+random.randn(len(t))*0.1
    y = smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string   
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."

    if window_len < 3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman', 'gauss']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman', 'gauss'"

    s = np.r_[2*x[0]-x[window_len:1:-1], x, 2*x[-1]-x[-1:-window_len:-1]]
    #print(len(s))
    
    if window == 'flat': #moving average
        w = np.ones(window_len,'d')
    elif window == 'gauss':
        w = gauss_kern(window_len)
    else:
        w = getattr(np, window)(window_len)
    y = np.convolve(w/w.sum(), s, mode='same')
    return y[window_len-1:-window_len+1]


def mjdToJD(MJD=None):
    """
    Converts an MJD value to JD.  Default = now.
    """
    if (MJD==None): MJD = getMJD()
    JD = MJD + 2400000.5
    return(JD)

def mjdToUT(mjd=None, use_metool=True, prec=6):
    """
    Converts an MJD value to a UT date and time string
    such as '2012-03-14 00:00:00 UT'
    use_metool: whether or not to use the CASA measures tool if running from CASA.
         This parameter is simply for testing the non-casa calculation.
    """
    if mjd==None:
        mjdsec = getCurrentMJDSec()
    else:
        mjdsec = mjd*86400
    utstring = mjdSecondsToMJDandUT(mjdsec, use_metool, prec=prec)[1]
    return(utstring)

def mjdSecondsToMJDandUT(mjdsec, use_metool=True, debug=False, prec=6):
    """
    Converts a value of MJD seconds into MJD, and into a UT date/time string.
    prec: 6 means HH:MM:SS,  7 means HH:MM:SS.S
    example: (56000.0, '2012-03-14 00:00:00 UT')
    Caveat: only works for a scalar input value
    Todd Hunter
    """
    if (os.getenv('CASAPATH') == None or use_metool==False):
        mjd = mjdsec / 86400.
        jd = mjdToJD(mjd)
        trialUnixTime = 1200000000
        diff  = ComputeJulianDayFromUnixTime(trialUnixTime) - jd
        if (debug): print "first difference = %f days" % (diff)
        trialUnixTime -= diff*86400
        diff  = ComputeJulianDayFromUnixTime(trialUnixTime) - jd
        if (debug): print "second difference = %f seconds" % (diff*86400)
        trialUnixTime -= diff*86400
        diff  = ComputeJulianDayFromUnixTime(trialUnixTime) - jd
        if (debug): print "third difference = %f seconds" % (diff*86400)
        # Convert unixtime to date string 
        utstring = timeUtilities.strftime('%Y-%m-%d %H:%M:%S UT', 
                       timeUtilities.gmtime(trialUnixTime))
    else:
        me = createCasaTool(metool)
        today = me.epoch('utc','today')
        mjd = np.array(mjdsec) / 86400.
        today['m0']['value'] =  mjd
        hhmmss = call_qa_time(today['m0'], prec=prec)
        date = qa.splitdate(today['m0'])
        utstring = "%s-%02d-%02d %s UT" % (date['year'],date['month'],date['monthday'],hhmmss)
    return(mjd, utstring)

def ComputeJulianDayFromUnixTime(seconds):
    """
    Converts a time expressed in unix time (seconds since Jan 1, 1970)
    into Julian day number as a floating point value.
    - Todd Hunter
    """
    [tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst] = timeUtilities.gmtime(seconds)
    if (tm_mon < 3):
        tm_mon += 12
        tm_year -= 1
    UT = tm_hour + tm_min/60. + tm_sec/3600.
    a =  floor(tm_year / 100.)
    b = 2 - a + floor(a/4.)
    day = tm_mday + UT/24.
    jd  = floor(365.25*((tm_year)+4716)) + floor(30.6001*((tm_mon)+1))  + day + b - 1524.5
    return(jd) 
