#! /usr/bin/env python
"""

"""

import os
import time
import wvrComm

from optparse import OptionParser

if __name__ == '__main__':
    usage = '''
 
    '''
    #creating class ...
    wvr = wvrComm.wvrComm()

    #options ....
    parser = OptionParser(usage=usage)

    parser.add_option("-i", 
                      dest="interval",
                      type= 'int',
                      default = 60,
                      help="interval to sample")

(options, args) = parser.parse_args()
  
interval = options.interval
prefix = time.strftime('%Y%m%d_%H%M%S')
filename = prefix+'_wvrHealthMonitor.txt'
newfile = file(filename, 'w')

newfile.write('# timestamp                 , byts, ctrl,  V12, curr, volt, temp, test, mode,   op, alrm, boot,  clk,   te,  Cold Temp Setpoint,  Cold Temp Measured,  Cold PWM, Hot Temp Setpoint,  Hot Temp Measured,  Hot PWM, TP Temp Setpoint,  TP Temp Measured,  TP Temp PWM,  CS Temp Setpoint,  CS Temp Measured, CS PWM, BE Temp Setpoint,  BE Temp Measured, BE PWM, Lna Temp, V12, V6, VM6, C12, C6, CM6, LO_freq, LO_bias0, LO_bias1 \n' )

while(True):
    try:
        (t, al,st,coldT,coldPwm,hotT,hotPwm, tpT,tpPwm,csT,csPwm,beT,bePwm,lnaT,V12,V6,VM6,C12,C6,CM6,lof,lobias0,lobias1) = wvr.getStatus()
        newfile.write('%s,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d, %3.3f, %3.3f, %2.3f, %3.3f, %3.3f, %2.3f, %3.3f, %3.3f, %2.3f,%3.3f, %3.3f, %2.3f, %3.3f, %3.3f, %2.3f, %3.3f, %2.3f, %2.3f, %2.3f, %2.3f, %2.3f, %2.3f, %d,%2.3f, %2.3f \n'%(t, al[0],al[1],al[2],al[3],al[4],al[5],al[6],st[0],st[1],st[2],st[3],st[4],st[5],coldT[1],coldT[0],coldPwm,hotT[1],hotT[0],hotPwm, tpT[1],tpT[0],tpPwm,csT[1],csT[0],csPwm,beT[1],beT[0],bePwm,lnaT,V12,V6,VM6,C12,C6,CM6,lof,lobias0,lobias1))
        time.sleep(interval)
        newfile.flush()
    except:
        exit()
        newfile.close()
              
