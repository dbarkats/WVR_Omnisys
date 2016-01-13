import sys
import os
import time
import datetime
import numpy as np
import threading
import wvrComm
import wvrPeriComm
import StepperCmd
import MCpoints
import traceback
import logWriter

# Update this if you make major changes to code.
VERSION = 'version 2016-01-11'

class wvrDaq():
    """
    Class for WVR data acquisition
    """

    def __init__(self, logger=None, wvr=None, peri=None, elstep=None,
                 chan=[0,1,2,3], reg_fast=[], reg_slow=['HOT_TEMP','COLD_TEMP'], 
                 reg_stat=['STATE','ALARMS'], cadence=0.01, slowfactor=10,
                 comments='', prefix = '', debug=True):
         
        self.setPrefix(prefix=prefix)
        self.setLogger(logger=logger)
        self.wvr = wvr
        self.peri = peri
        self.wvrEl = elstep
        self.chan = chan
        self.reg_fast = self.setReg(reg_fast)
        self.reg_slow = self.setReg(reg_slow)
        self.reg_stat = self.setReg(reg_stat)
        self.cadence = cadence
        self.slowfactor = slowfactor
        self.comments = comments
        self.dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
        
    def setPrefix(self, prefix=''):
        if prefix == '':
            self.prefix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        else:
            self.prefix = prefix
    
    def setComments(self,comments=''):
        self.comments = comments

    def setLogger(self,logger=None):
        if logger == None:
            self.lw = logWriter.logWriter(prefix=self.prefix, verbose=False)
        else:
            self.lw = logger

    def defaultFile(self, ftype=None):
        """Default name for output file"""
        
        if ftype is None:
            return (self.prefix + '_fast.txt',
                    self.prefix +'_slow.txt', 
                    self.prefix +'_stat.txt')
        else:
            return time.strftime('%Y%m%d_%H%M%S_{}.txt'.format(ftype))

    def createFile(self, filename, reglist, isFast=False):
        """Creates new file and prints header"""

        # Open file to write.
        newfile = file(self.dataDir+filename, 'w')
        self.lw.write("Recording WVR data in file: %s "%(self.dataDir+filename))
        # wvrDaq software version
        newfile.write('# WVR data file, ' + VERSION + '\n')
        newfile.write('#%s \n'%self.comments)
        newfile.write('#\n')

        # Generate list of data fields.
        fields = ['TIME', 'TIMEWVR']
        if isFast:
            # Add WVR channels to fields list
            for ch in self.chan:
                fields.append('CH{}C'.format(ch))
                fields.append('CH{}A'.format(ch))
                fields.append('CH{}H'.format(ch))
                fields.append('CH{}B'.format(ch))
            # Add periscope az encoder to fields list.
            fields.append('EL')
            fields.append('AZ')
        # Add hk registers to fields list.
        for entry in reglist:
            for fld in entry[3]:
                fields.append(fld)
        # Print fields list.
        fldstr = (' {}' * len(fields))[1:].format(*fields)
        newfile.write(fldstr + '\n')
        # Return file handle.
        return (newfile, len(fields))

    def setReg(self, reglist):
        """
        Generate list of function handles for acquiring housekeeping data.
        """

        # This dictionary maps requested data to function handles that 
        # acquire it. Each entry consists of a tuple with four items:
        #   1. Function to call to get the data,
        #   2. Arguments used by that function (or None),
        #   3. Index(es) of the returned tuple that contains the desired data,
        #   4. Column label(s)
        reg_dict = {}
        # WVR alarms, state
        reg_dict['ALARMS'] = (self.wvr.getWvrAlarms, None, range(7),
                              ('AL_BYTS', 'AL_CTRL', 'AL_V12', 'AL_CURR', 
                               'AL_VOLT', 'AL_TEMP', 'AL_TEST'))
        
        reg_dict['STATE'] = (self.wvr.getWvrState, None, range(6), 
                             ('STATE_MODE', 'STATE_OP', 'STATE_ALARM', 
                              'STATE_BOOT', 'STATE_CLK', 'STATE_TE'))

        # Monitor hot load.
        reg_dict['HOT_TEMP'] = (self.wvr.getHotTemp, None, [0, 1], 
                               ('HOT_TEMP', 'HOT_SETP'))
        reg_dict['HOT_PWM'] = (self.wvr.getHotPwm, None, None, ('HOT_PWM',))
        reg_dict['HOT_NTC'] = (self.wvr.getHotNtc, None, None, ('HOT_NTC',))

        # Monitor cold load.
        reg_dict['COLD_TEMP'] = (self.wvr.getColdTemp, None, [0, 1],
                                ('COLD_TEMP', 'COLD_SETP'))
        reg_dict['COLD_PWM'] = (self.wvr.getColdPwm, None, None, ('COLD_PWM',))
        reg_dict['COLD_NTC'] = (self.wvr.getColdNtc, None, None, ('COLD_NTC',))

        # Monitor chopper.
        reg_dict['CHOP_STATE'] = (self.wvr.getChopState, None, [0, 1], 
                                  ('CHOP_PH', 'CHOP_VEL'))
        reg_dict['CHOP_PWM'] = (self.wvr.getChopPwm, None, None, ('CHOP_PWM',))
        reg_dict['CHOP_CURR'] = (self.wvr.getChopCurr, None, None, ('CHOP_CURR',))

        # WVR integrated / calibrated response.
        reg_dict['TSRC0'] = (self.wvr.getInt, MCpoints.GET_INT_TSRC0, [0], ('TSRC0',))
        reg_dict['TSRC1'] = (self.wvr.getInt, MCpoints.GET_INT_TSRC1, [0], ('TSRC1',))
        reg_dict['TSRC2'] = (self.wvr.getInt, MCpoints.GET_INT_TSRC2, [0], ('TSRC2',))
        reg_dict['TSRC3'] = (self.wvr.getInt, MCpoints.GET_INT_TSRC3, [0], ('TSRC3',))
        reg_dict['EST0'] = (self.wvr.getInt, MCpoints.GET_INT_EST0, [0], ('EST0',))
        reg_dict['EST1'] = (self.wvr.getInt, MCpoints.GET_INT_EST1, [0], ('EST1',))
        reg_dict['EST2'] = (self.wvr.getInt, MCpoints.GET_INT_EST2, [0], ('EST2',))
        reg_dict['EST3'] = (self.wvr.getInt, MCpoints.GET_INT_EST3, [0], ('EST3',))
        reg_dict['HOT0'] = (self.wvr.getInt, MCpoints.GET_INT_HOT0, [0], ('HOT0',))
        reg_dict['HOT1'] = (self.wvr.getInt, MCpoints.GET_INT_HOT1, [0], ('HOT1',))
        reg_dict['HOT2'] = (self.wvr.getInt, MCpoints.GET_INT_HOT2, [0], ('HOT2',))
        reg_dict['HOT3'] = (self.wvr.getInt, MCpoints.GET_INT_HOT3, [0], ('HOT3',))
        reg_dict['COLD0'] = (self.wvr.getInt, MCpoints.GET_INT_COLD0, [0], ('COLD0',))
        reg_dict['COLD1'] = (self.wvr.getInt, MCpoints.GET_INT_COLD1, [0], ('COLD1',))
        reg_dict['COLD2'] = (self.wvr.getInt, MCpoints.GET_INT_COLD2, [0], ('COLD2',))
        reg_dict['COLD3'] = (self.wvr.getInt, MCpoints.GET_INT_COLD3, [0], ('COLD3',))
        reg_dict['SKYA0'] = (self.wvr.getInt, MCpoints.GET_INT_SKYA0, [0], ('SKYA0',))
        reg_dict['SKYA1'] = (self.wvr.getInt, MCpoints.GET_INT_SKYA1, [0], ('SKYA1',))
        reg_dict['SKYA2'] = (self.wvr.getInt, MCpoints.GET_INT_SKYA2, [0], ('SKYA2',))
        reg_dict['SKYA3'] = (self.wvr.getInt, MCpoints.GET_INT_SKYA3, [0], ('SKYA3',))
        reg_dict['SKYB0'] = (self.wvr.getInt, MCpoints.GET_INT_SKYB0, [0], ('SKYB0',))
        reg_dict['SKYB1'] = (self.wvr.getInt, MCpoints.GET_INT_SKYB1, [0], ('SKYB1',))
        reg_dict['SKYB2'] = (self.wvr.getInt, MCpoints.GET_INT_SKYB2, [0], ('SKYB2',))
        reg_dict['SKYB3'] = (self.wvr.getInt, MCpoints.GET_INT_SKYB3, [0], ('SKYB3',))

        # Power supplies.
        reg_dict['12CURR'] = (self.wvr.getCtrl12Curr, None, None, ('12CURR',))
        reg_dict['6CURR'] = (self.wvr.getCtrl6Curr, None, None, ('6CURR',))
        reg_dict['M6CURR'] = (self.wvr.getCtrlM6Curr, None, None, ('M6CURR',))
        reg_dict['12VOLT'] = (self.wvr.getCtrl12Volt, None, None, ('12VOLT',))
        reg_dict['6VOLT'] = (self.wvr.getCtrl6Volt, None, None, ('6VOLT',))
        reg_dict['M6VOLT'] = (self.wvr.getCtrlM6Volt, None, None, ('M6VOLT',))

        # Monitor TP
        reg_dict['TP_TEMP'] = (self.wvr.getTpTemp, None, [0, 1], ('TP_TEMP', 'TP_SETP'))
        reg_dict['TP_PWM'] = (self.wvr.getTpPwm, None, None, ('TP_PWM',))

        # Monitor BE
        reg_dict['BE_TEMP'] = (self.wvr.getBeTemp, None, [0, 1], ('BE_TEMP', 'BE_SETP'))
        reg_dict['BE_PWM'] = (self.wvr.getBePwm, None, None, ('BE_PWM',))
        reg_dict['BE_NTC'] = (self.wvr.getBeNtc, None, None, ('BE_NTC',))
        reg_dict['BE_BIAS0'] = (self.wvr.getBeBias0, None, None, ('BE_BIAS0',))
        reg_dict['BE_BIAS1'] = (self.wvr.getBeBias1, None, None, ('BE_BIAS1',))
        reg_dict['BE_BIAS2'] = (self.wvr.getBeBias2, None, None, ('BE_BIAS2',))
        reg_dict['BE_BIAS3'] = (self.wvr.getBeBias3, None, None, ('BE_BIAS3',))

        # Monitor CS
        reg_dict['CS_TEMP'] = (self.wvr.getCsTemp, None, [0, 1], ('CS_TEMP', 'CS_SETP'))
        reg_dict['CS_PWM'] = (self.wvr.getCsPwm, None, None, ('CS_PWM',))
        reg_dict['CS_NTC'] = (self.wvr.getCsNtc, None, None, ('CS_NTC',))

        # Monitor LO
        reg_dict['LO_FREQ'] = (self.wvr.getLoFreq, None, None, ('LO_FREQ',))
        reg_dict['LO_BIAS0'] = (self.wvr.getLoBias0, None, None, ('LO_BIAS0',))
        reg_dict['LO_BIAS1'] = (self.wvr.getLoBias1, None, None, ('LO_BIAS1',))

        # Monitor LNA
        reg_dict['LNA_TEMP'] = (self.wvr.getLnaTemp, None, None, ('LNA_TEMP',))

        # AZ and EL -- only use for slow/stat file (az/el already included in fast file)
        #reg_dict['ENC'] = (self.monitor.read_position, None, [0,1], ('AZ', 'EL'))
        reg_dict['AZ'] = (self.peri.monitorAzPos, None, None, ('AZ',))
        reg_dict['EL'] = (self.wvrEl.monitorElPos, None, None, ('EL',))

        # Generate list of function handles.
        reg = []
        for tag in reglist:
            if reg_dict.has_key(tag.upper()):
                reg.append(reg_dict[tag.upper()])
            else:
                print "WARNING: unknown register: {}".format(tag.upper())
        return reg

    def listReg(self, reglist):
        """Print the list of housekeeping channels to record."""
        for entry in reglist:
            print entry[3]

    def acquireHk(self, reglist):
        """
        Acquire housekeeping data from WVR.
        """
        vec = []
        # Loop over entries in the housekeeping list.
        for entry in reglist:
            # For each entry:
            #   Call function listed in entry[0],
            #   using entry[1] as function arguments,
            #   then select the entry[2] element(s) of the returned tuple.
            if entry[1] is not None:
                res = entry[0](entry[1])
            else:
                res = entry[0]()
            # Add values to hk vector.
            if entry[2] is not None:
                for ind in entry[2]:
                    vec.append(res[ind])
            else:
                vec.append(res)
        # Done.
        return vec

    def acquireFastSample(self, warn=True):
        """
        Acquire one 48 ms sample of raw radiometer data for all channels.
        """
        
        # Allocate data array.
        nch = len(self.chan)
        data = [None] * nch
        # Acquire data for all channels.
        for i in range(nch):
            s = ([], [])
            while len(s[1]) == 0:
                s = self.wvr.getMbuf(self.chan[i])
            data[i] = s
        if warn:
            # Check that all frames have same timestamp.
            tsamp = np.array([x[0] for x in data])
            if np.any(tsamp != tsamp[-1]):
                self.lw.write("[WARNING] Misaligned data sample")
            # Check whether any of these frames have multiple samples.
            nsamp = np.array([len(x[1]) for x in data])
            if np.any(nsamp > 1):
                self.lw.write("[WARNING] Dropped data")
        return (data[-1][0], np.concatenate([x[1][-1,:] for x in data]))
        
    def recordData(self, duration):
        """
        Record data to ascii files.

        Parameters
        ----------
        duration : float
            Duration of data acquisition, in seconds.
        fastfile : str
            Path to file for recording radiometer data, as well as
            housekeeping registers that are designated fast.
        slowfile : str
            Path to file for recording housekeeping data at a slow
            rate.
        statfile : str
            Path to file for recording status once at the start.

        Output
        ------
        nfast : int
            Number of fast samples recorded to file.
        nslow : int
            Number of slow samples recorded to file.

        """
        
        try:
            self.lw.write("Recording data for {} seconds \n".format(duration))
            # Get file names.
            (fastfileN, slowfileN, statfileN) = self.defaultFile()
            self.fastFilename = fastfileN
            # Write stat file -- registers that get recorded just
            # once per call to acquireData.
            self.writeStatFile(statfileN)
            # Create output file for fast registers.
            (fastfile, nfield_fast) = self.createFile(fastfileN, self.reg_fast,
                                                      isFast=True)
            # Create output file for slow registers.
            (slowfile, nfield_slow) = self.createFile(slowfileN, self.reg_slow)
            # Flush WVR buffer.
            (tstart, dummy) = self.acquireFastSample(warn=False)
            tcurr = tstart
            nfast = 0
            nslow = 0
            #self.peri.openSerialPort()
            # Data acquisition loop.
            while not tcurr > (tstart + duration):
                # System timestamp for this sample.
                tstr = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
                # Acquire WVR data for all channels.
                (tcurr, dvec) = self.acquireFastSample()
                # Read encoder position.
                az = self.peri.getAzPos()
                el = self.wvrEl.getElPos()
                # Read fast registers.
                fastvec = self.acquireHk(self.reg_fast)
                # Combine into string.
                faststr = '{} {}'.format(tstr, tcurr)
                faststr = faststr + (' {}' * len(dvec)).format(*dvec)
                faststr = faststr + ' {}'.format(el)
                faststr = faststr + ' {}'.format(az)
                faststr = faststr + (' {}' * len(fastvec)).format(*fastvec)
                fastfile.write(faststr + '\n')
                # Acquire housekeeping data.
                if np.mod(nfast, self.slowfactor) == 0:
                    self.writeSlowFile(slowfile, tstr, tcurr)
                    nslow += 1
                # Increment counter.
                nfast += 1
                # Sleep for specified duration.
                time.sleep(self.cadence)
            # Done with data acquisition.
            self.lw.write("{} fast samples, {} slow samples \n".format(nfast, nslow))
            ret = (nfast, nslow)

        except Exception, ex:
            self.lw.write("Error with recordData. Only acquired {} fast samples, {} slow samples \n".format(nfast, nslow))
            self.lw.write("EXCEPTION: %s " % ex)
            self.lw.write(str(traceback.format_exc()))
            ret = None
            
        finally:
            fastfile.close()
            slowfile.close()
            #self.peri.closeSerialPort()
            return ret


    def writeStatFile(self, filename):
        """
        Create stat file, record registers, then close file.
        """
        
        # Open file and print header.
        (statfile, nfield) = self.createFile(filename, self.reg_stat)
        # Computer timestamp.
        tstr = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        # WVR timestamp.
        (twvr, dummy) = self.wvr.getMbuf(0)
        # Registers requested for statfile.
        statvec = self.acquireHk(self.reg_stat)
        # Write line to file.
        statstr = '{} {}'.format(tstr, twvr)
        statstr = statstr + (' {}' * len(statvec)).format(*statvec)
        statfile.write(statstr + '\n')
        # Done.
        statfile.close()

    def writeSlowFile(self, slowfile, tstr=None, tcurr=None):
        """
        Write a line to the slow data file.
        """

        # Get housekeeping data.
        slowvec = self.acquireHk(self.reg_slow)
        # Combine into string.
        slowstr = '{} {}'.format(tstr, tcurr)
        slowstr = slowstr + (' {}' * len(slowvec)).format(*slowvec)
        slowfile.write(slowstr + '\n')

    def isProcessActive(self):
        """
        checks if wvrDaq is running
        returns True is fastFileName is changing size evry 2s
        returns False if not
        """
        fastFile = self.dataDir+self.fastFilename
        if self.fastFilename == None:
            return False
        else:
            s0 = os.stat(fastFile).st_size
            time.sleep(2)
            s1 =  os.stat(fastFile).st_size
            if s1 != s0:
                return True
            else:
                return False
