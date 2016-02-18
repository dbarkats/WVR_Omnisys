
import argparse

import numpy as np
import matplotlib.pyplot as pl

''' Convert a radiosonde trace of the atmosphere from the south pole weather station to an am-8.0 amc file '''

def read_sonde(fn):
	''' read data from radiosonde output file '''
	dtype = ['time','height','pressure','temp','dewp','rh','speed','dir']
	dtype = [(x,np.float64) for x in dtype]
	d = np.loadtxt(fn,skiprows=9,dtype=dtype)

	n = len(d) - 1
	while d['rh'][n] == 1 and n >= 0:
		d['rh'][n] = 0
		n = n - 1
	return d

def saturated_vapor_pressure(T):
	'''	Calculate 100% humidity vapor pressure at temperature T
	T in celcius
	i.e. 100% relative humidity?
	valid to -50C
	'''

	es = 6.1121*np.exp((17.502*T)/(240.97 + T))
	return es

amc_header = '''
? am <sonde.amc> <fmin GHz> <fmax GHz> <za deg>
f %1 GHz %2 GHz 100.0 MHz
output f GHz tau Tb K
za %3 deg
tol 0.0001
PTmode Pbase Tbase


T0 2.7 K
'''

def sonde_to_amc(sonde_data,out_fn,nlayer):
	''' Render data from the radiosonde to an amc file with n layers '''
	f = open(out_fn,'w')

	pressure = sonde_data['pressure']
	temp = sonde_data['temp']
	rh = sonde_data['rh']
	layer_pressure = np.linspace(0,max(pressure),nlayer)

	print>>f,amc_header

	print>>f, 'layer'
	print>>f, 'Pbase 0 mbar'
	print>>f, 'Tbase %f C'%temp[-1]
	print>>f, ''
	for i in range(1,nlayer):
		pressure_max = layer_pressure[i]
		pressure_min = layer_pressure[i-1]
		ok = (pressure_min < pressure) & (pressure <= pressure_max)
		tbase = temp[ok][0]
		h2o_rh = np.mean(rh[ok])
	
		print>>f, 'layer'
		print>>f, 'Pbase %f mbar'%pressure_max
		print>>f, 'Tbase %f C'%tbase
		print>>f, 'column dry_air hydrostatic'
		if h2o_rh > 0:
			print>>f, 'column h2o rh %f%%'%h2o_rh
		print>>f, ''


def getargs():
	parser = argparse.ArgumentParser()
	parser.add_argument('fn',help='Sonde input file')
	parser.add_argument('-n',type=int,default=10,help='Number of output layers')
	parser.add_argument('-o',help='AMC output file')
	args = parser.parse_args()
	return args

def main():
	args = getargs()
	sonde_data = read_sonde(args.fn)
	sonde_to_amc(sonde_data,args.o,args.n)

if __name__=='__main__':
	main()
