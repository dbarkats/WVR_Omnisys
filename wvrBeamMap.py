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
minScanEl = 20 # in deg
maxScanEl = 28 # in deg. Must be greater than minScanEl
deltaEl = 0.5 # in deg
Nsteps = int((maxScanEl - minScanEl)/deltaEl +1)
elSteps = minScanEl + arange(Nsteps)*deltaEl
NscansPerElStep = 1
oneStepAzScanningDuration =  4*(NscansPerElStep * 360/azScanningSpeed) + 12
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

wvrAE.stopAzRot()
time.sleep(1)
wvrAE.homeAz()

wvrAE.homeEl()
lw.write("Done with homing El stepper motor")
lw.write("Moving to MinScanEl")
wvrAE.slewEl(minScanEl)
lw.write("Done with Moving to MinScanEl")

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw, wvr=wvrC, azelstep=wvrAE, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="Beam Map observation", 
                    prefix=prefix, debug=False)

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid1 = threading.Thread(target=rsp.loopNtimes, args=(totalAzScanningDuration +10,))
tPid1.daemon = True
tPid1.start()
time.sleep(1)

lw.write("start wvr data acquisition in the background")
tDaq1 = threading.Thread(target=daq.recordData, args=(totalAzScanningDuration+10,))
tDaq1.daemon = True
tDaq1.start()
time.sleep(2)

azMax = 0
for El in elSteps:
    lw.write("Slewing to El:%.1f"%El)
    wvrAE.slewEl(El)
    time.sleep(1.0)
    azMax = azMax + NscansPerElStep*360
    wvrAE.slewAz(azMax)
    lw.write("start Az rotation at El=%.1f for %.1f sec, until az=%.1f"%(El,oneStepAzScanningDuration, azMax))
    #time.sleep(0.5)
    azPos = wvrAE.monitorAzPos()
    lw.write(azPos)
    while azPos < azMax-0.1:
        time.sleep(2)
        azPos = wvrAE.monitorAzPos()
        elPos = wvrAE.monitorElPos()
        print "Commanded Az:%d, current Az:%.2f, El:%.1f"%(azMax, azPos, elPos)  
        lw.write("Commanded Az:%d, current Az:%.2f, El:%.1f "%(azMax, azPos, elPos))  
        
#wait for tdaq1 thread to finish
while(tDaq1.isAlive()):
     lw.write("Waiting for previous recordData thread to finish")
     time.sleep(10)
     
# Clean up.
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with %s script, finished with script at %s"%(script,ts)

