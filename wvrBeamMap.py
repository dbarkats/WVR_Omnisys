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
import wvrComm
import wvrPeriComm
import StepperCmd
import wvrDaq
import datetime
import SerialPIDTempsReader
import threading
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
buffer = 10 # seconds

print "Doing a BeamMap from EL=%2.1f to EL=%2.1f (%d el steps %2.2f each) with %d az scans per step"%(minScanEl, maxScanEl, Nsteps, deltaEl, NscansPerElStep)
print "Total scanning time: %.1f secs"% totalAzScanningDuration
# Common variables are defined in wvrRegList
#############################################

ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_scanAz_beamMap'
lw = logWriter.logWriter(prefix, options.verbose)
lw.write("Running %s"%script)

# Also print to standard output file in case we get messages going to it
print "Starting %s at %s"%(script,ts)

lw.write("create wvrComm object")
wvrC = wvrComm.wvrComm(debug=False)

lw.write('Set WVR to operational')
if(wvrC.setWvrToOperation()):
    lw.write("WVR Operational!")
else:
    lw.write("ERROR: WVR failed to go to Operational. Check low level errors")
    sys.exit()

lw.write("create PIDTemps object")
rsp = SerialPIDTempsReader.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)

lw.write("create wvrAz object")
wvrAz = wvrPeriComm.wvrPeriComm(logger=lw, debug=False)

lw.write("Resetting and Homing Az stage")
wvrAz.stopRotation()
wvrAz.resetAndHomeRotStage()

lw.write("create wvrEl object")
wvrEl = StepperCmd.stepperCmd(logger=lw, debug=False)

lw.write("Homing El stepper motor")
wvrEl.initPort()
wvrEl.home()
wvrEl.slewEl(minScanEl)

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw, wvr=wvrC, peri=wvrAz, elstep=wvrEl, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="Beam Map observation", 
                    prefix=prefix, debug=False)

totalAzScanningDuration= wvrAz.getRotationTime(totalAzScanningDuration, azScanningSpeed)

lw.write("start PIDtemps acquisition in the background")
pid_th = threading.Thread(target=rsp.loopNtimes, args=(totalAzScanningDuration,))
pid_th.daemon = True
pid_th.start()

lw.write("start wvr data acquisition in the background")
daq_th = threading.Thread(target=daq.recordData, args=(totalAzScanningDuration+buffer,))
daq_th.daemon = True
daq_th.start()

lw.write("start Az rotation for %.1f sec"%(totalAzScanningDuration))
wvrAz.startRotation(totalAzScanningDuration, azScanningSpeed)

azMax = 0
for El in elSteps:
    azMax = azMax + NscansPerElStep*360
    lw.write("start Az rotation at El=%.2f  for %.1f sec"%(El,oneStepAzScanningDuration))
    wvrEl.slewEl(El)
    time.sleep(1)
    lw.write("Waiting until this Az scanning ends")
    azPos = wvrAz.getAzPos()
    while azPos < azMax-0.1:
        #lw.write("Going to %d, current AZ: %f, EL:%f "%(azMax, wvrAz.azPos, El))
        print "Going to %d, current AZ: %f, EL:%f "%(azMax, azPos, El)  
        time.sleep(2)
        azPos = wvrAz.getAzPos()

#wait for daq_th thread to finish
while(daq_th.isAlive()):
     lw.write("Waiting for previous recordData thread to finish")
     time.sleep(10)

# Clean up.
wvrAz.closeSerialPort()
wvrEl.closePort()
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with %s script, finished with script at %s"%(script,ts)

