#! /usr/bin/env python
import os
###
# A super simple wrapper to  be able to run many skydips one after the other
# Can be used to run skydips at many different azimuths ( if azList is a list of different az
# or can be used as was done most recently to  perform skydips in different conditions 
#( like with the different  sonotubes
###


#azList = [   0.,   20.,   40.,   60.,   80.,  100.,  120.,  140.,  160.,
#        180.,  200.,  220.,  240.,  260.,  280.,  300.,  320.,  340.]

azList = [   150., 150.,150.]

for k in [0,1,2]:
    for az in azList:
        print k, az
        cmd = '/home/dbarkats/WVR_Omnisys/wvrObserve1hr.py  -e 80 -z %d -o'%az
        os.system(cmd)
