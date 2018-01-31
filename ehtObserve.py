#! /usr/bin/env python

import time
import os,sys
from wvrRegList import *
import wvrDaq
import wvrComm
import wvrPeriComm
import StepperCmd
import SerialPIDTempsReader_v2 as sr
from ehtUtils import *
import threading
import logWriter
import checkProcess
from optparse import OptionParser
from datetime import datetime, timedelta

if __name__ == '__main__':
    usage = '''
    Wrapper script to acquire 1hr of WVR data while observing eht az/el
    - do skydip
    - look up eht source schedule
    - start on the 1st source and observe it until either:
            - the 1hr observing is up OR
            - the next source is up
    
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-v",
                      dest="verbose",
                      action="store_true",
                      default=False,
                      help="-v option will print to Logging to screen in addition to file. Default = False")
    
    parser.add_option("-d",
                      dest="duration",
                      default = 3400,
                      type= int,
                      help="-d, duration of scanAz observation phase in seconds. Default = 3400s")
        
    parser.add_option("-e",
                      dest="ehtScheduleFile",
                      default = '',
                      help="-e, name of the eht schedule file to observe. Default is eht_schedule.txt")

    parser.add_option("-z",
                      dest="azimuth",
                      default = 150.0,
                      type= float,
                      help="-z, azimuth angle to perform the skydip at, in deg. Default: 150")

    parser.add_option("-o",
                      dest="onlySkydip",
                      action= "store_true",
                      default = False,
                      help="-o, to do only the initial skyDip.")

(options, args) = parser.parse_args()

#Checks that no other instances of wvrObserve1hr.py are already running
checkProcess.checkProcess('wvrObserve1hr.py',force=True)
checkProcess.checkProcess('wvrNoise.py',force=True)
checkProcess.checkProcess('ehtObserve.py',force=True)

#### DEFINE VARIABLES #########
script = "ehtObserve.py"
skyDipDuration =  60  # in seconds
skyDipAz = options.azimuth # in deg
observingDuration = options.duration # in seconds
ehtScheduleFile = options.ehtScheduleFile

#### START RUNNING skyDip part ###############
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_skyDip'
lw = logWriter.logWriter(prefix, options.verbose)
lw.write("Running %s"%script)

# Also print to standard output file in case we get messages going to it
mypid = os.getpid()
print "Starting %s at %s, PID: %s"%(script,ts, mypid)
sys.stdout.flush()

lw.write("create wvrComm object")
wvrC = wvrComm.wvrComm(debug=False)

lw.write('Set WVR to operational')
if(wvrC.setWvrToOperation()):
    lw.write("WVR Operational!")
else:
    lw.write("ERROR: WVR failed to go to Operational. Check low level errors")
    sys.exit()

lw.write("create wvrAz object")
wvrAz = wvrPeriComm.wvrPeriComm(logger=lw, debug=False)

lw.write("Resetting and Homing Az stage")
wvrAz.stopRotation()
wvrAz.resetAndHomeRotStage()
lw.write("Slewing to az=%3.1f"%skyDipAz)
wvrAz.slewAz(skyDipAz)

lw.write("create wvrEl object")
wvrEl = StepperCmd.stepperCmd(logger=lw, debug=False)
lw.write("Initializing El stepper motor")
wvrEl.initPort()

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw,  wvr=wvrC, peri=wvrAz, elstep=wvrEl, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="skyDip observation", 
                    prefix = prefix, debug=False)

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid1 = threading.Thread(target=rsp.loopNtimes,args=(skyDipDuration + 2,))
tPid1.daemon = True
tPid1.start()
time.sleep(1)

lw.write("start wvr data acquisition in the background")
tdaq1 = threading.Thread(target=daq.recordData,args=(skyDipDuration,))
tdaq1.daemon = True
tdaq1.start()
time.sleep(1)

lw.write("Doing Skydip ...")
wvrEl.home()       #    1/ HOME
wvrEl.slewMinEl()  #    2/ GO TO MIN ELEVATION at el=13.8 (steps=3200)
wvrEl.home()       #    3/ BACK TO home
wvrEl.slewEl(45)   #    4/ BACK TO ELEVATION OF OBSERVATION

while(tdaq1.isAlive()):
     lw.write("Waiting for previous recordData thread to finish")
     time.sleep(10)

if options.onlySkydip:
    ts = time.strftime('%Y%m%d_%H%M%S')
    lw.write("Finished skidip, ending script now at %s"%ts)
    lw.close()
    wvrEl.closePort()
    wvrAz.closeSerialPort()
    exit()
lw.close()

##### START Running EHT obsering part ########

# parse eht schedule file
eht = parseEhtSchedule(ehtScheduleFile)

ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_eht'
lw = logWriter.logWriter(prefix, options.verbose)
print "Done with skyDip, moving on to EHT scanning at %s"%(ts)
sys.stdout.flush()

lw.write("Updating wvrDaq object with EHT scanning parameters")
daq.setPrefix(prefix)
daq.setComments('EHT Scanning Observation')
daq.setLogger(lw)

lw.write("starting EHT observations")
wvrAz.setLogger(lw)
wvrEl.setLogger(lw)

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger = lw, plotFig=False, prefix=prefix, debug=False)

lw.write("start PIDtemps acquisition in the background")
tPid2 = threading.Thread(target=rsp.loopNtimes,args=(observingDuration,))
tPid2.daemon = True
tPid2.start()
time.sleep(1)

lw.write("start wvr data acquisition in the background")
tdaq2 = threading.Thread(target=daq.recordData,args=(observingDuration,))
tdaq2.daemon = True
tdaq2.start()
time.sleep(1)

# determine what source to look at and for how long 
startTime = datetime.now()
endTime = startTime + timedelta(seconds = observingDuration) # obs ending time
print 'EHT total observing duration %d'%observingDuration
iold = -1;
while datetime.now() < endTime:
        now = datetime.now()
	tLeft = endTime - now
	i = find_source(now, eht['time'])
        if i == size(eht['time'])-1:
            obsTime = tLeft
        else:
            obstime = eht['time'][i+1] - now
            obsTime = min(obsTime, tLeft)
        if (i != iold):
                el = eht['EL'][i]
                az = eht['AZ'][i]
                print '%s: observing source %d: %s (az, el) = (%.3f, %.3f) for %.1f s, timeLeft in complete observation: %.1f '%(now,i,eht['src'][i],az,el,obsTime.total_seconds(), tLeft.total_seconds())
                wvrAz.slewAz(az)
                wvrEl.slewEl(el)
        else:
                 print "continuingto observe on this source"
        time.sleep(10)
        iold = i

# Clean up.
wvrAz.closeSerialPort()
wvrEl.closePort()
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with scanAz part, finished with script at %s \n"%(ts)
sys.stdout.flush()

