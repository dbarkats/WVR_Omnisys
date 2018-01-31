#! /usr/bin/env python

import time
import os,sys
import StepperCmdAzEl
import datetime
import threading
import logWriter
import checkProcess
import SerialPIDTempsReader_v3 as sr
from pylab import floor
from optparse import OptionParser

if __name__ == '__main__':
    usage = '''
    Like wvrObserve1hr, but ignore the radiometer unit.
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
                      dest="elevation",
                      default = 55.0,
                      type= float,
                      help="-e, elevation at which to do the az scanning at. Deafault: 55")
    
    parser.add_option("-o",
                      dest="onlySkydip",
                      action= "store_true",
                      default = False,
                      help="-o, to do only the initial skyDip.")

    parser.add_option("-c",
                      dest='complete',
                      action="store_true",
                      default=False,
                      help="-c, will store a complete set of registers for the slopw file instead of a limited set of registers. Useful for troubleshooting. Default=False")

(options, args) = parser.parse_args()

#Checks that no other intances of wvrObserve1hr.py are already running
checkProcess.checkProcess('wvrObserve1hr.py',force=True)
checkProcess.checkProcess('wvrSpin1hr.py',force=True)
checkProcess.checkProcess('wvrNoise.py',force=True)

#### DEFINE VARIABLES #########
script = "wvrSpin1hr.py"
skyDipDuration =  60  # in seconds
scanEl = options.elevation # elevation where we do the 1hr az scanning
azScanningDuration = options.duration # in seconds
NazTurns = floor(azScanningDuration * 12/360.)

#### START RUNNING skyDip part ###############
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_skyDip'
lw = logWriter.logWriter(prefix, options.verbose)
lw.write("Running %s"%script)

# Also print to standard output file in case we get messages going to it
mypid = os.getpid()
print "Starting %s at %s, PID: %s"%(script,ts, mypid)
lw.write("Starting %s at %s, PID: %s"%(script,ts, mypid))
sys.stdout.flush()

lw.write("create wvrAz object")
wvrAE = StepperCmdAzEl.stepperCmd(logger=lw, debug=False)
lw.write("Homing Az stage")
wvrAE.homeAz()

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid1 = threading.Thread(target=rsp.loopNtimes,args=(skyDipDuration,))
tPid1.daemon = True
tPid1.start()
time.sleep(1)

lw.write("Doing Skydip ...")

wvrAE.homeEl()       #   1/ HOME
wvrAE.slewMinEl()    #   2/ GO TO MinEl
wvrAE.homeEl()       #   3/ BACK TO home
wvrAE.slewEl(scanEl) #   4/ BACK TO ELEVATION OF OBSERVATION

ts = time.strftime('%Y%m%d_%H%M%S')
if options.onlySkydip:
    lw.write("Finished skidip, ending script now at %s"%ts)
    lw.close()
    wvrAE.closePort()
    exit()
else:
  lw.write("Finished skidip, moving on to scanAz part now at %s"%ts)  
  lw.close()

##### START Running azscan part ########
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_scanAz'
lw = logWriter.logWriter(prefix, options.verbose)

print "Done with skyDip part, moving on to scanAz at %s"%(ts)
lw.write("Finished skidip, moving on to scanAz part now at %s"%ts)  
sys.stdout.flush()

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger = lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid2 = threading.Thread(target=rsp.loopNtimes,args=(azScanningDuration,))
tPid2.daemon = True
tPid2.start()
time.sleep(1)

lw.write("start az rotation")
wvrAE.setLogger(lw)
wvrAE.slewAz(NazTurns*360.)

lw.write("Az scanning Duration: %d"%azScanningDuration)
for i in range(int(azScanningDuration)):
    lw.write("Az Pos: %.3f, El Pos: %.3f"%(wvrAE.getAzPos(), wvrAE.getElPos()))
    time.sleep(1)

# Clean up.
wvrAE.closePort()
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with scanAz part, finished with script at %s \n"%(ts)
sys.stdout.flush()

