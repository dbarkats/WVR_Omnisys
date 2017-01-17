#!/usr/bin/env python

from pylab import genfromtxt
from pylab import *
from datetime import datetime, timedelta

def parseEhtSchedule(file = 'eht_schedule.txt'):
    """
    load the eht observing schedule text file provided by EHT group
    Format is  date/time, src, AZ, EL
    Comma delimited
    Returns a structured array
    """
    conv = {0: lambda s: datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')}
    eht = genfromtxt(file,delimiter=',',names=True,skip_header=4,dtype=None, converters=conv)

    return eht

def find_source(tnow, tsource):
    """
     find the index of the  object to observe at a given time
    inputs are a time ( typically time now ) in datetime format
    and tsource is an array of datetime (parsed from eht schedule observing file)
    """
    # if t is out of tsource range
    if tnow < tsource[0] or tnow > tsource[-1]:
        print('Current time %s outside source time range.'%tnow)
        return None
        
    # find index of source we should be observing now
    inds = find(tsource < tnow)
    ind_now = inds[-1]
    return ind_now
