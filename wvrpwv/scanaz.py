#! /usr/bin/env python

from optparse import OptionParser
import argparse

import numpy as np
import matplotlib.pyplot as pl

import wvrAnalysis
import am

if __name__ == '__main__':
        usage = '''
        Fit the median PWV from a radiometer 1 hour azimuth scan file 
        
        '''
        #options ....
        parser = OptionParser(usage=usage)
        
        parser.add_option("-a", '--amc-path',
                          dest="amc-path",
                          default='SPole_winter.amc',
                          help=" -a option: AM input template")

        parser.add_option("-f", '--filename',
                          dest="filename",
                          help=" -f option: slow scan filename")

(options, args) = parser.parse_args()
wvrA = wvrAnalysis.wvrAnalysis()			
fitatm = am.FitAtmosphere(options.amc-path)
uttime,tslow,wvrdata,az,el,tsrc = wvrA.readSlowFile(options.filename)

tsrc_med = np.median(tsrc,axis=0)
el_med = np.median(el)

pwv,rms = fitatm.fit_meas(tsrc_med,el_med)
print pwv,rms

pred,fs,tb = fitatm.model(pwv,el[0])
pl.plot(fs,tb,label='PWV=%.1f um'%pwv)

fitatm.radiometer.plot_meas(tsrc[0],linestyle='--')
fitatm.radiometer.plot_meas(pred,linestyle='-')

pl.title('Fit to radiometer data\nsolid is fit, dashed is measured')
pl.legend()
	pl.grid()
	pl.show()

