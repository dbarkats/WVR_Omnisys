#!/usr/bin/env python

import os,sys
import socket
 
class initialize():
    
    def __init__(self, unit=None):
        '''
        
        Function to initialize directories to perform any kind of wvr reduction
        '''

        self.host = socket.gethostname()
        self.home = os.getenv('HOME')

        if unit == None:
            if self.host.startswith('wvr2'):
                unit = 'wvr2'
            elif self.host.startswith('wvr1'):
                unit = 'wvr1'
            else:
                print "Unit must be defined if running on computer other than wvr1 or wvr2. Exiting"
                return
        else:
            if (unit != 'wvr1') and (unit != 'wvr2'):
                print "unit must be wvr1 or wvr2, exiting"
                return
        self.setWvrUnit(unit)
            
            
    def setWvrUnit(self,unit):
        print "### Analyzing unit %s ..."%unit
        self.unit = unit
        self.setDirs()

    def setDirs(self):

        self.reducDir = self.home+'/%s_reducplots/'%self.unit
        self.dataDir = self.home+'/%s_data/'%self.unit
        self.wxDir = '/n/holylfs/LABS/kovac_lab/keck/wvr_products/wx_reduced/'
