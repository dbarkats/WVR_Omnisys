#! /usr/bin/env python

"""

 
"""

## arduino definition

from subprocess import Popen, PIPE
import socket
from optparse import OptionParser
import os

# Needed to add this line in /etc/sudoers to allow usbreset to be run as root 
# w/o passwd
#sudo visudo -f /etc/sudoers
#dbarkats ALL=(root) NOPASSWD: /home/dbarkats/usbreset

if __name__ == '__main__':
    usage = '''
         
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-d", "--device",
                      dest="device",
                      type= 'string',
                      default = 'arduinoPidTemp',
                      help="device name to be reset(arduinoPidTemp or arduinoElAxis) or IdVendor:IdProduct pair. Default = 'arduinoPidTemp' ")

(options, args) = parser.parse_args()

def getDeviceName(device):

    process = Popen(['lsusb'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print stdout, stderr

    nusb = len(stdout.split('\n')[:-1])
    for i,line in enumerate(stdout.split('\n')[:-1]):
        sline = line.split()
        if sline[5] == device:
            bus = sline[1]
            dev = sline[3][:-1]
            deviceName = '/dev/bus/usb/%s/%s'%(bus,dev)
            return deviceName
        if i == nusb-1:
            print "ERROR: Device %s was not found in lsusb"%device
            print "ERROR: your device is missing from the device list or your device name is incorrect."
            print "Doing nothing"
            return 0

host = socket.gethostname()
if ':' not in options.device:
    if 'wvr2' in host:
        arduinoPidTemp = '2341:003e'
        arduinoElAxis = '2a03:0042'    
    elif 'wvr1' in host:
        arduinoPidTemp = '2341:003e'
        arduinoElAxis = '2341:0042'
    device = eval(device)
else:
    device = options.device
    
deviceName = getDeviceName(device)
if deviceName != 0:
    cmd = 'sudo $HOME/usb_utils/usbreset %s'%deviceName
    print cmd
    os.system(cmd)
