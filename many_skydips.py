#! /usr/bin/env python
import os
from pylab import arange
###
# A super simple wrapper to  be able to run many skydips one after the other
# Can be used to run skydips at many different azimuths ( if azList is a list of different az
# or can be used as was done most recently to  perform skydips in different conditions 
#( like with the different  sonotubes
###


azList = arange(0,360,10)
#
#azList = [   150., 150.,150.]

#for k in [0,1,2]:
for az in azList:
    print  az
    cmd = '/home/dbarkats/wvr_pipeline/wvrObserve1hr.py -e 85 -z %d -o'%az
    os.system(cmd)
