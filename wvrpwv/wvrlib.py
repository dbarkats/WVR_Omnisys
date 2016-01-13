
import datetime

import numpy as np

def read_wvrfile(fn):
	d = np.genfromtxt(fn,names=True,skip_header=3)
	times = []
	with open(fn,'r') as f:
		for line in f:
			if line.startswith('#') or line.startswith('TIME'):
				continue
			words = line.split()
			tstr = words[0]

			t = datetime.datetime.strptime(tstr,'%Y-%m-%dT%H:%M:%S.%f')
			times.append(t)
	return times,d

def integrate_band(fs,tb,band_center,band_width):
	lower = band_center*(1-band_width/2.)
	upper = band_center*(1+band_width/2.)

	flag = 1.0*((lower <= fs)&(fs <= upper))
	bw = np.trapz(flag,fs)
	power = np.trapz(flag*tb,fs)
	temp = power/bw
	return temp

