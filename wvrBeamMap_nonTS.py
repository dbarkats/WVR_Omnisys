#! /usr/bin/env python

"""

Wrapper script to acquire perform a wvrBeam map
 - define all variables at the top.
 - create daq, az stage, el stage , PIDTemps objects
 - reset and home az stage
 
"""
import time
import os, sys
from wvrRegList import *
import wvrDaq
import datetime
import SerialPIDTempsReader
import thread
import logWriter
from pylab import *
from optparse import OptionParser

if __name__ == '__main__':
    usage = '''
 
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
    
    parser.add_option("-s",
                      dest="speed",
                      default = 3.0,
                      type= float,
                      help="-s, rotation velocity in deg/s to perform the az scanning at. Default: 12.5 deg/s")
    

(options, args) = parser.parse_args()

#### DEFINE VARIABLES #########
script = "wvrBeamMap.py"
azScanningSpeed = options.speed # in deg/s
minScanEl = 19 # in deg
maxScanEl = 29 # in deg. Must be greater than  minScanEl
deltaEl = .25 # in deg
Nsteps = int((maxScanEl - minScanEl)/deltaEl) +1
elSteps = minScanEl + arange(Nsteps)*deltaEl
NscansPerElStep = 1
oneStepAzScanningDuration =  NscansPerElStep * 360/azScanningSpeed
totalAzScanningDuration = oneStepAzScanningDuration * Nsteps
buffer = 100 # seconds

print "Doing a BeamMap from EL=%2.1f to EL=%2.1f (%d el steps %2.2f each) with %d az scans per step"%(minScanEl, maxScanEl, Nsteps, deltaEl, NscansPerElStep)
print "Total scanning time: %2.12f secs"% totalAzScanningDuration
# Common variables are defined in wvrRegList
#############################################

ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_scanAz_beamMap'
lw = logWriter.logWriter(prefix, options.verbose)

# Also print to standard output file in case we get messages going to it
print "Starting %s at %s"%(script,ts)

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw, reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="Beam Map observation", 
                    prefix = prefix, debug=False)

lw.write("Running %s"%script)

lw.write("create wvrComm object")
wvrC = daq.wvr

lw.write('Set WVR to operational')
if(wvrC.setWvrToOperation()):
    lw.write("WVR Operational!")
else:
    lw.write("ERROR: WVR failed to go to Operational. Check low level errors")
    sys.exit()

lw.write("create PIDTemps object")
rsp = SerialPIDTempsReader.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)

lw.write("create wvrAz object")
wvrAz = daq.peri

lw.write("Resetting and Homing Az stage")
wvrAz.stopRotation()
wvrAz.resetAndHomeRotStage()

lw.write("create wvrEl object")
wvrEl = daq.wvrEl

lw.write("Homing El stepper motor")
wvrEl.home()
wvrEl.slewEl(minScanEl)

lw.write("start PIDtemps acquisition in the background")
tid = thread.start_new_thread(rsp.loopNtimes,(totalAzScanningDuration,))
time.sleep(1)

lw.write("start wvr data acquisition in the background")
thread.start_new_thread(daq.recordData,(totalAzScanningDuration+buffer,))
time.sleep(1)

lw.write("start Az rotation for %.1f sec"%(totalAzScanningDuration))
wvrAz.startRotation(totalAzScanningDuration, azScanningSpeed)
wvrAz.openSerialPort()

azMax = 0
for El in elSteps:
    azMax = azMax + NscansPerElStep*360
    lw.write("start Az rotation at El=%.2f  for %.1f sec"%(El,oneStepAzScanningDuration))
    wvrEl.slewEl(El)
    time.sleep(1)
    lw.write("Waiting until this Az scanning ends")
    # use this to maybe avoid threadng issue
    cmd = 'tail -3 data_tmp/%s_fast.txt'%prefix
    print cmd
    time.sleep(10)
    azPos = float(os.popen(cmd).read().split('\n')[0].split()[-1])
    print azPos, azMax
    while azPos < azMax-0.1:
        #lw.write("Going to %d, current AZ: %f, EL:%f "%(azMax, wvrAz.azPos, El))
        print "Going to %d, current AZ: %f, EL:%f "%(azMax, azPos, El)  
        time.sleep(2)
        azPos = float(os.popen(cmd).read().split('\n')[0].split()[-1])

wvrEl.closePort()
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with scanAz part, finished with script at %s"%(ts)
thread.exit()
