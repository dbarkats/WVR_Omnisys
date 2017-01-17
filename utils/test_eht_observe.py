#! /usr/bin/env python

import time
import os,sys
from wvrRegList import *
import wvrDaq
import wvrComm
import wvrPeriComm
import StepperCmd
import datetime
import SerialPIDTempsReader_v2 as sr
import threading
import logWriter
import checkProcess
from ehtUtils import *
from optparse import OptionParser
from datetime import datetime,timedelta

# load the eht observing text file
# names are time, src, AZ, EL
eht =  parseEhtSchedule()

# determine what source to look at and for how long 
starttime = datetime.now();
#endtime = starttime + timedelta(seconds=3400);
endtime = starttime + timedelta(seconds=1200);
objindold = -1;
while datetime.now() < endtime:
        now = datetime.now()
	tleft = endtime - now;
	objind = find_source(now, eht['time']);
	obstime = eht['time'][objind+1] - now;
	obstime = min(obstime, tleft);
        if (objind != objindold):
                el = eht['EL'][objind];
                az = eht['AZ'][objind];
                print "slew in az and el"
                print('observing source %i %s (az, el) = (%.3f, %.3f) for %.1f seconds'%(objind, eht['src'][objind],az,el,obstime.total_seconds()))
        else:
                print "contiuing on this source without doing anything"
	time.sleep(10)
        objindold = objind




	

