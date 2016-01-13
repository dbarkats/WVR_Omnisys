#! /usr/bin/env python

import time
import sys
from wvrRegList import *
import wvrDaq
import wvrComm
import wvrPeriComm
import StepperCmd
import datetime
import SerialPIDTempsReader
import threading
import logWriter
from optparse import OptionParser

if __name__ == '__main__':
    usage = '''
    Wrapper script to acquire 1hr of WVR data. The following is done:
    - define all variables at the top.
    - create daq, az stage, el stage , PIDTemps objects
    - reset and home az stage
    - start data acquisition
    - do Skydip (home, el=90, home, el=oberving el)
    - stop data acquisition
    - create new daq object
    - reset and home az stage
    - start az scanning motion
    - start data acquisition
    
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
                      default = 3300,
                      type= int,
                      help="-d, duration of scanAz observation phase in seconds. Default = 3400s")
    
    parser.add_option("-e",
                      dest="elevation",
                      default = 55.0,
                      type= float,
                      help="-e, elevation at which to do the az scanning at. Deafault: 55")
    
    parser.add_option("-s",
                      dest="speed",
                      default = 12.5,
                      type= float,
                      help="-s, rotation velocity in deg/s to perform the az scanning at. Default: 12.5 deg/s")
    
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

#### DEFINE VARIABLES #########
script = "wvrObserve1hr.py"
skyDipDuration =  60  # in seconds
skyDipAz = options.azimuth # in deg
scanEl = options.elevation # elevation where we do the 1hr az scanning
azScanningDuration = options.duration # in seconds
azScanningSpeed = options.speed # in deg/s

# Common variables are defined in wvrRegList

#### START RUNNING skyDip part ###############

ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_skyDip'
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

lw.write("create wvrAz object")
wvrAz = wvrPeriComm.wvrPeriComm(logger=lw, debug=False)

lw.write("Resetting and Homing Az stage")
wvrAz.stopRotation()
wvrAz.resetAndHomeRotStage()
lw.write("Slewing to az=%3.1f"%skyDipAz)
wvrAz.slewAz(skyDipAz)

lw.write("create wvrEl object")
wvrEl = StepperCmd.stepperCmd(logger=lw, debug=False)

lw.write("Homing El stepper motor")
wvrEl.initPort()

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw,  wvr=wvrC, peri=wvrAz, elstep=wvrEl, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="skyDip observation", 
                    prefix = prefix, debug=False)

lw.write("create PIDTemps object")
rsp = SerialPIDTempsReader.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid1 = threading.Thread(target=rsp.loopNtimes,args=(skyDipDuration + 2,))
tPid1.start()
time.sleep(1)

lw.write("start wvr data acquisition in the background")
tdaq1 = threading.Thread(target=daq.recordData,args=(skyDipDuration,))
tdaq1.start()
time.sleep(1)

lw.write("Doing Skydip ...")
# Skydip:
#    1/ HOME
wvrEl.home()
#    2/ GO TO END OF MOTION at el=13.8 (steps=3200)
wvrEl.slewMinEl()
#    4/ BACK TO home
wvrEl.home()
#    5/ BACK TO ELEVATION OF OBSERVATION
wvrEl.slewEl(scanEl)

#Check previous acquisition is done
#while(daq.isProcessActive()):
#    lw.write("Waiting for previous recordData to finish")
#    time.sleep(10)
while(tdaq1.isAlive()):
     lw.write("Waiting for previous recordData thread to finish")
     time.sleep(10)

if options.onlySkydip:
    ts = time.strftime('%Y%m%d_%H%M%S')
    lw.write("Finished skidip, ending script now at %s"%ts)
    wvrEl.closePort()
    wvrAz.closeSerialPort()
    exit()
lw.close()

##### START Running azscan part ########
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_scanAz'
lw = logWriter.logWriter(prefix, options.verbose)

print "Done with skyDip part, moving on to scanAz at %s"%(ts)

lw.write("Updating wvrDaq object with az scan parameters")
daq.setPrefix(prefix)
daq.setComments('Az Scanning Observation')
daq.setLogger(lw)

lw.write("create PIDTemps object")
rsp = SerialPIDTempsReader.SerialPIDTempsReader(logger = lw, plotFig=False, prefix=prefix, debug=False)

lw.write("start PIDtemps acquisition in the background")
tPid2 = threading.Thread(target=rsp.loopNtimes,args=(azScanningDuration+5,))
tPid2.start()
time.sleep(1)

lw.write("start az rotation")
wvrAz.setLogger(lw)
wvrAz.startRotation(azScanningDuration, azScanningSpeed)
azScanningDuration= wvrAz.getRotationTime(azScanningDuration, azScanningSpeed)

lw.write("start wvr data acquisition in the foreground")
(nfast, nslow) = daq.recordData(azScanningDuration)

# Clean up.
wvrAz.closeSerialPort()
wvrEl.closePort()
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with scanAz part, finished with script at %s"%(ts)

