
import argparse

import numpy as np
import matplotlib.pyplot as pl

import wvrlib
import am

''' Fit the median PWV from a radiometer 1 hour azimuth scan file '''

def getargs():
	parser = argparse.ArgumentParser()
	parser.add_argument('--amc_path',default='SPole_winter.amc',help='AM input template')
	parser.add_argument('fn',help='Slow az scan file')
	args = parser.parse_args()
	return args

			
def main():
	args = getargs()
	fitatm = am.FitAtmosphere(args.amc_path)
	times,wvrdata = wvrlib.read_wvrfile(args.fn)

	el = wvrdata['EL']
	az = wvrdata['AZ']

	tscr0 = wvrdata['TSRC0']
	tscr1 = wvrdata['TSRC1']
	tscr2 = wvrdata['TSRC2']
	tscr3 = wvrdata['TSRC3']

	tscr = np.vstack([tscr0,tscr1,tscr2,tscr3]).T

	tscr_med = np.median(tscr,axis=0)
	el_med = np.median(el)

	pwv,rms = fitatm.fit_meas(tscr_med,el_med)
	print pwv,rms

	pred,fs,tb = fitatm.model(pwv,el[0])
	pl.plot(fs,tb,label='PWV=%.1f um'%pwv)

	fitatm.radiometer.plot_meas(tscr[0],linestyle='--')
	fitatm.radiometer.plot_meas(pred,linestyle='-')

	pl.title('Fit to radiometer data\nsolid is fit, dashed is measured')
	pl.legend()
	pl.grid()
	pl.show()

if __name__=='__main__':
	main()

