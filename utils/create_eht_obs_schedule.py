from datetime import datetime, timedelta
import numpy as np
import random as rand
from itertools import izip

now = datetime.now()
# starting now, a source every five minutes for 2 days
dtList = range(0,2*86400,300)
tList = [now + timedelta(seconds = dt) for dt in dtList]
tStrList = ['{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'.format(t.year, t.month, t.day, t.hour, t.minute, t.second) for t in tList]
srcname = ['Eht{}'.format(i) for i in range(len(tList))]
elList = [rand.randint(13,90) for i in range(len(tList))]
azList = [rand.randint(0,360) for i in range(len(tList))]

with open('eht_observation_schedule.txt','w') as f:
	for t,src,az,el in izip(tStrList,srcname,elList,azList) :
		f.write('{:s},  {:s},  {:.2f},  {:.2f} \n'.format(t, src, az, el))
	




