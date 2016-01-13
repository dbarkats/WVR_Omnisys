
import argparse

import numpy as np
import matplotlib.pyplot as pl

import wvrlib
import am

''' Compare a radiometer sky dip to a radiosonde measurement '''

def getargs():
	parser = argparse.ArgumentParser()
	parser.add_argument('--amc_path',default='SPole_winter.amc',help='AM input template')
	parser.add_argument('fn',help='Sky dip slow scan file')
	args = parser.parse_args()
	return args

def main():
	args = getargs()

	times,wvrdata = wvrlib.read_wvrfile(args.fn)
	sonde_amc = am.AMDrive(args.amc_path)

	cut = 13
	times = times[cut:]
	wvrdata = wvrdata[cut:]

	el = wvrdata['EL']
	tsrc0 = wvrdata['TSRC0']
	tsrc1 = wvrdata['TSRC1']
	tsrc2 = wvrdata['TSRC2']
	tsrc3 = wvrdata['TSRC3']

	ii = np.arange(len(el))

	# Upsample and align elevation to radiometer channels
	ii2 = np.linspace(0,max(ii),len(ii)*10)

	def upsample(x):
		return np.interp(ii2,ii,x)
	
	el = upsample(el)
	tsrc0 = upsample(tsrc0)
	tsrc1 = upsample(tsrc1)
	tsrc2 = upsample(tsrc2)
	tsrc3 = upsample(tsrc3)

	tsrc = np.vstack([tsrc0,tsrc1,tsrc2,tsrc3]).T

	shift = 7
	el = el[:-shift]
	tsrc = tsrc[shift:]

	npred = 10
	el_pred = np.linspace(20.,90.,npred)

	radiometer = am.Radiometer()

	pred = np.zeros((npred,4))
	for i in range(npred):
		fs,eta,tb = sonde_amc.run_params([0,300,90.-el_pred[i]])
		pred[i] = radiometer.output(fs,tb)

	colors = ['blue','green','red','purple']
	for i in range(4):
		pl.plot(el,tsrc[:,i],color=colors[i],label='ch %d meas'%i)

	colors = ['blue','green','red','purple']
	for i in range(4):
		pl.plot(el_pred,pred[:,i],color=colors[i],linestyle='--',label='ch %d pred'%i)

	pl.title('Sky dip compared to sonde model')
	pl.xlabel('El (deg)')
	pl.ylabel('Temperature (K)')
	pl.legend()
	pl.grid()
	pl.show()

if __name__=='__main__':
	main()

