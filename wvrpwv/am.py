#! /usr/bin/env python

from optparse import OptionParser
import os,sys
import tempfile
import popen2

import numpy as np
import matplotlib.pyplot as pl
from scipy import optimize

''' am.py
library for fitting pwv from an atmosphere model 
and measurements from an Omnisys 4 channel radiometer
'''

class AMDrive():
	''' Read and run am files '''
	def __init__(self, debug=True):
                self.debug=debug

	def run_params(self, infn, pars):

		outfn = infn.replace('.amc','.out')
		errfn = infn.replace('.amc','.err')

		cmd = 'am %s '%infn
                if self.debug:
                        print ("am parameters: f0: %.2f %s, "
			       "f1: %.2f %s,  df: %.2f %s, "
			       "za: %2.2f %s, h2o_scale=%2.2f"
			       %(pars[0],pars[1],pars[2],pars[3],pars[4],
				 pars[5],pars[6],pars[7],pars[8]))
		cmd += ("%.2f %s %.2f %s %.2f %s %.2f %s %.2f" 
			%(pars[0],pars[1],pars[2],pars[3],pars[4],
			  pars[5],pars[6],pars[7],pars[8]))
                
		cmd +=  ' >%s '%outfn
		cmd += ' 2>%s '%errfn
                if self.debug: print cmd

		os.system(cmd)
		fs,tau,tb,trj = np.loadtxt(outfn,unpack=True)

		return fs,tau,tb,trj



class Layer():
	''' Parse and render a single layer in an am8.0 amc file '''
	def __init__(self,layer_def):
		self.Pbase = None
		self.Tbase = None
		self.o3 = None
		self.h2o = None
		self.dry_air = None

		for line in layer_def:
			words = line.split()
			if words[0] == 'Pbase':
				self.Pbase = float(words[1])
			elif words[0] == 'Tbase':
				self.Tbase = float(words[1])
			elif words[1] == 'o3':
				self.o3 = float(words[3])
			elif words[1] == 'h2o':
				self.h2o = float(words[3])
			elif words[1] == 'dry_air':
				self.dry_air = True

	def render(self,pscale=1.,tscale=1.,h2oscale=1.,o3scale=1.):
		out = ''
		out += 'layer\n'
		if self.Pbase is not None:
			out += 'Pbase %.4f mbar\n'%(pscale*self.Pbase)
		if self.Tbase is not None:
			out += 'Tbase %.4f K\n'%(tscale*self.Tbase)
		if self.dry_air is not None:
			out += 'column dry_air hydrostatic\n'
		if self.o3 is not None:
			out += 'column o3 hydrostatic %.4e\n'%(o3scale*self.o3/pscale)
		if self.h2o is not None:
			out += 'column h2o hydrostatic %.4e\n'%(h2oscale*self.h2o/pscale)

		return out

class LayerFile():
	''' Read/write am-8.0 amc files with changing pressure/temperature/pwv '''

	def __init__(self,fn,debug=True):
		''' fn is template input file e.g. SPole_winter.amc '''
                self.debug=debug
                infn =  amDir+fn
                self.templateFile = infn
		lines = open(infn).readlines()

		layers = []
		current_layer = []
		for line in lines:
			if line.startswith('layer'):
				layers.append(current_layer)
				current_layer = []
			else:
				line = line.strip()
				if len(line) > 0:
					current_layer.append(line)
		layers.append(current_layer)

		self.header = '\n'.join(layers.pop(0))+'\n\n'

		self.layers = [Layer(x) for x in layers]
		self.pground = self.layers[-1].Pbase
		self.tground = self.layers[-1].Tbase

	def rescale_amTemplate(self,outfn,pground=None,tground=None):
		''' create amfile outfn with pressure and temperature rescaled to given
			 pressure at ground and temperature at ground'''

		f = open(outfn,'w')
		tscale = 1.
		pscale = 1.

		if tground is not None:
			tscale = tground / self.tground
		if pground is not None:
			pscale = pground / self.pground
                
                if self.debug:
                        print "Scaling factor from Template: Temp: %2.3f, Press: %2.3f"\
                                %(tscale, pscale)

		print>>f, self.header
		for layer in self.layers:
			out = layer.render(pscale=pscale,tscale=tscale)
			print>>f, out

		f.close()
	
	def run_am(self,pground=680.,tground=245.,h2o=1000.,za=0.,f0=170.,f1=200., df=100):
		'''
		pground: pressure at ground
		tground: temperature at ground
		h2o: pwv in um
		f0 and f1 in GHz
		za = zenigh angle : 90 -el [deg]

		'''
		fUnits = 'GHz'
		dfUnits = 'MHz'
		zaUnits = 'deg'

		fn = tempfile.mktemp('.amc',dir=amDir)  

                # rescale am Template file 
		# comment this out, not sure about this step
		# self.rescale_amTemplate(fn,pground=pground,tground=tground) 
                
		# run am
		amdrive = AMDrive(fn, debug=self.debug)
		fs,tau,tb = amdrive.run_params([f0,fUnits,
						f1,fUnits,
						df,dfUnits, 
						za,zaUnits])

                #interpolate to 10MHz frequency line.
		df = f1 - f0
		fstep = 0.01
		nf = int(df / fstep)
		fs2 = np.linspace(f0,f1,nf)
		tb2 = np.interp(fs2,fs,tb)
                # delete temporary scaled amc file.
		os.unlink(fn)
		return fs2,tb2

class Radiometer():
	''' Specification of the 4 channel radiometer in the Keck Omnisys WVR '''
	def __init__(self):
		# From Denis
		self.bands = [(1.191,1.428),(3.145,2.466),(5.548,1.890),(7.293,1.374)]
		self.lo = 183.31
        
        def integ_channel(self,center,bw,fs,tb):
		''' integrate the atmosphere over a single channel '''
		lower = center-bw/2.
		upper = center+bw/2.
		flag_lower = (self.lo - upper < fs) & (fs < self.lo - lower)
		flag_upper = (self.lo + lower < fs) & (fs < self.lo + upper)
		flag = 1.0*(flag_lower | flag_upper)

		band_power = np.trapz(tb*flag,fs)
		band_width = np.trapz(flag,fs)
		avg_temp = band_power / band_width
		return avg_temp

	def observe(self,fs,tb):
		''' Predict output channel temperatures given fs,tb atmosphere model '''
		outs = np.array([self.integ_channel(x[0],x[1],fs,tb) for x in self.bands])
		return outs

	def plot_meas(self,temps,markerStyle):
		''' Plot temperatures of channels '''
		colors = ['blue','green','red','black']
		for i,temp in enumerate(temps):
			center,bw = self.bands[i]
			lower = center-bw/2
			upper = center+bw/2
			#pl.plot([self.lo+lower,self.lo+upper],[temp,temp],color=colors[i],linestyle=linestyle,linewidth=2)
			#pl.plot([self.lo-upper,self.lo-lower],[temp,temp],color=colors[i],linestyle=linestyle,linewidth=2)
                        pl.plot([self.lo+center],[temp],color=colors[i],marker=markerStyle)
			pl.plot([self.lo-center],[temp],color=colors[i],marker=markerStyle)
                        

class FitAtmosphere():
	''' Fit for PWV given at am-8.0 atmosphere model 
        and a single 4 channel measurement from the Omnisys WVR '''
	
        def __init__(self,amc_path,debug=True):
                self.debug=debug
		self.layerfile = LayerFile(amc_path,debug=debug)
		self.radiometer = Radiometer()
		self.pwv0 = 500.
		self.t0 = 245.
		self.p0 = 680.
                
	def model(self,pwv,el):
		''' predict atmosphere temperature and radiometer 
                response from pwv and elevation '''
		
                fs,tb = self.layerfile.run_am(pground=self.p0,tground=self.t0,h2o=pwv,el=el)
		pred = self.radiometer.observe(fs,tb)
		return pred,fs,tb

	def fit_meas(self,meas,el):
		''' Fit pwv from measurements meas from radiometer at elevation el '''
		def resid(params):
			pwv = params[0]
			pred,fs,tb = self.model(pwv,el)
			return pred - meas
		def fmin_func(params):
			r = resid(params)
			return np.dot(r,r)

		params0 = np.array([self.pwv0])

		x,cov_x, infodict, mesg, ier = optimize.leastsq(resid,params0,full_output=True,epsfcn=0.001,xtol=0.001)
		pred,fs,tb = self.model(x[0],el)
		error = meas - pred
		error_var = np.mean(error*error)
		pcov = cov_x * error_var / (len(pred) - len(params0))
		perr = np.sqrt(np.diag(pcov))

		pwv_fit = x[0]
		pwv_err_fit = perr[0]
		rms_error = np.sqrt(error_var)

                if self.debug: print "PWV fit: %3.3f um +- %3.3f um" %(pwv_fit, pwv_err_fit)
		return pwv_fit,pwv_err_fit


if __name__ == '__main__':
        usage =  '''
        Fit a series of measurements in a file 
        '''
        
        #options ....
        parser = OptionParser(usage=usage)
        
        parser.add_option("-a", '--amc-path',
                          dest="amc-path",
                          default='SPole_winter.amc',
                          help=" -a option: AM input template")
        
        parser.add_options('-p',
                           destination='pressure',
                           type=float,
                           default=680.0,
                           help='Ground level pressure (mbar), Default=680mB')
        
        parser.add_options('-t',
                           destination='temperature',
                           type=float,
                           default=243.0,
                           help='Ground level temperature (K), Default=243K = -30C')
        
        parser.add_options('-e',
                           type=float,
                           default=55.0,
                           help='Elevation of observation, Default=55')
        
        parser.add_option("-f", '--filename',
                          dest="filename",
                          help=" -f option: slow scan filename")
        
        (options, args) = parser.parse_args()
        
        # instantiate wvr utility
        wvrA = wvrAnalysis.wvrAnalysis()			

        fitatm = FitAtmosphere(options.amc_path, debug=True)
        fitatm.p0 = options.pressure
        fitatm.t0 = options.temperature
        
        utTime,tslow,d,az,el,tsrc =  wvrA.readSlowFile(options.filename)
        
        pwv,rms = fitatm.fit_meas(meas,options.e)
        
        print "PWV: %.1f um    RMS:  %.1f K"%(pwv,rms)
        print pwv,rms
        
