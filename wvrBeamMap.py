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
import StepperCmdAzEl
import wvrDaq
import datetime
import SerialPIDTempsReader_v3 as sr
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
    
(options, args) = parser.parse_args()

#### DEFINE VARIABLES #########
script = "wvrBeamMap.py"
azScanningSpeed = 12 # default Arduino hard-wired deg/s
minScanEl = 19 # in deg
maxScanEl = 29 # in deg. Must be greater than minScanEl
deltaEl = 0.5 # in deg
Nsteps = int((maxScanEl - minScanEl)/deltaEl)
elSteps = minScanEl + arange(Nsteps)*deltaEl
NscansPerElStep = 1
oneStepAzScanningDuration =  NscansPerElStep * 360/azScanningSpeed
totalAzScanningDuration = oneStepAzScanningDuration * Nsteps
NazTurns = floor(totalAzScanningDuration * 12.0/360.)

print "Doing a BeamMap from EL=%2.1f to EL=%2.1f (%d el steps %2.2f each) with %d az scans per step"%(minScanEl, maxScanEl, Nsteps, deltaEl, NscansPerElStep)
print "Total scanning time: %.1f secs"% totalAzScanningDuration

# Common variables are defined in wvrRegList
#############################################
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_scanAz_beamMap'
lw = logWriter.logWriter(prefix, options.verbose)
lw.write("Running %s"%script)

# Print to standard output file in case we get messages going to it
print "Starting %s at %s"%(script,ts)
sys.stdout.flush()

lw.write("create wvrComm object")
wvrC = wvrComm.wvrComm(debug=False)

lw.write('Set WVR to operational')
if(wvrC.setWvrToOperation()):
    lw.write("WVR Operational!")
else:
    lw.write("ERROR: WVR failed to go to Operational. Check low level errors")
    sys.exit()

lw.write("create wvrAzEl object")
wvrAE = StepperCmdAzEl.stepperCmd(logger=lw, debug=False)

lw.write("Homing Az stepper motor")
wvrAE.stopAzRot()
time.sleep(1)
wvrAE.homeAz()

lw.write("Homing El stepper motor")
wvrAE.homeEl()
wvrAE.slewEl(minScanEl)

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw, wvr=wvrC,  azelstep=wvrAE, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="Beam Map observation", 
                    prefix=prefix, debug=False)

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid1 = threading.Thread(target=rsp.loopNtimes, args=(totalAzScanningDuration +2,))
tPid1.daemon = True
tPid1.start()
time.sleep(1)

lw.write("start wvr data acquisition in the background")
tDaq1 = threading.Thread(target=daq.recordData, args=(totalAzScanningDuration+2,))
tDaq1.daemon = True
tDaq1.start()

lw.write("start az rotation.")
lw.write("Doing %d turns, %d deg at 12deg/s: %d seconds"%(NazTurns,NazTurns*360.,totalAzScanningDuration))
wvrAE.slewAz(NazTurns*360.)

azMax = 0
for El in elSteps:
    azMax = azMax + NscansPerElStep*360
    lw.write("start Az rotation at El=%.2f for %.1f sec"%(El,oneStepAzScanningDuration))
    wvrAE.slewEl(El)
    lw.write("Waiting until this Az scanning ends")
    
    while wvrAE.monitorAzPos() < azMax-1.0:
        azPos = wvrAE.monitorAzPos()
        print "Going to %d, current AZ: %f, EL:%f "%(azMax, azPos, El)  
        time.sleep(2)

#wait for tdaq1 thread to finish
while(tDaq1.isAlive()):
     lw.write("Waiting for previous recordData thread to finish")
     time.sleep(10)
     
# Clean up.
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with %s script, finished with script at %s"%(script,ts)

