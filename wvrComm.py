import socket
import time
import os,sys
import struct
import array
#import binascii
import time
import datetime
import numpy as np
from MCpoints import *

#import code
#code.interact(local=locals())

def help(match='', debug=False):
    """
    Print an alphabetized list of all the defined functions at the top 
    level in wvrComm.py
    match: limit the list to those functions containing this string (case insensitive)
    """
    myfile ='wvrComm.py'
    wvrfile = open(myfile,'r')
    lines = wvrfile.readlines()
    if (debug): print "Read %d lines from %s" % (len(lines),myfile)
    wvrfile.close()
    functions = []
    for line in lines:
        if 'def ' in line:
            functionline = line.split('def ')[1]
            tokens = functionline.split('(')
            if (len(tokens) > 1):
                function = tokens[0]
            else:
                function = functionline.strip('\n\r').strip('\r\n')
            if (match == '' or function.lower().find(match.lower()) >= 0):
                functions.append(function)
    functions.sort()
    for function in functions:
        print function


def get_bits(decimal,N):
    return decimal >> N  &1

class wvrComm():
    
    def __init__(self, debug=False):
        """
        """
        self.host = '192.168.168.230'
        self.port = 9734
        self.sock = None
        self.debug = debug
        self.wvrTftpServer = '192.168.168.232'
        #Write FORMAT: empty char(1byte), address (unsigned short, 2bytes), data(array of 8 unsigned char bytes), serverIP (20byte char), filename(40byte char), msg (40byte char)
        fmt_w = 'B H 8s 20s 40s 40s' 
        self.packer = struct.Struct(fmt_w) 
        # READ FORMAT
        fmt_r = 'B H 8s 20s 40s 40s'# empty char, address, data, serverIP, filename, msg
        self.unpacker = struct.Struct(fmt_r) 
        self.recv_size = self.unpacker.size

    def getTCPInfo(self):
        fmt = "7B21I"
        x = struct.unpack(fmt,self.sock.getsockopt(socket.IPPROTO_TCP,socket.TCP_INFO,92))
        if self.debug: print "TCP connecting status: %d" % x[0]
        return x
        
    def connect(self, force=True):
        # if(self.debug): print 'Connecting to wvr %s port %s'% (self.host,self.port)
        try:
            if (force) or (not self.sock):
                self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.sock.connect((self.host,self.port))
            else:
                state = self.getTCPInfo()
                while(state[0] != 1):
                    self.sock.close()
                    self.sock = None
                    time.sleep(1)
                    self.connect()
                    state = self.getTCPInfo()
        except Exception, e:
            print('Connection refused. Something is wrong with %s:%d. Exception type is %s' %(self.host, self.port, `e`))

    def sendMessageReadResponse(self, rid, sendData='', serverIP = '', filename='', msg='', autoClose=True):
        self.connect()
        values = (0, rid, sendData, serverIP, filename, msg)
        packed_data = self.packer.pack(*values)
        self.sock.sendall(packed_data)
        data = self.sock.recv(self.recv_size)
        unpacked_data = self.unpacker.unpack(data)
        if (autoClose):
            self.sock.close()
        return unpacked_data
   

    ################
    # Command points
    ################

    def setWvrState(self, mode, reset=(0,0,0,0)):
        """
        mode: 0=operational, 
              1=idle, 
              2=configuration, 
              3=N/A
        reset bitmask: (exit,boot,trip,time)
        ie setWvrState(2,(0,0,0,1)) will set the WVR to conf mode and clear the timestamp counter.
        """
        rid = SET_WVR_STATE[0]
        reset = int('0b%s%s%s%s'%(reset),2)
        b = [mode,reset]
        sendData = str(bytearray(b))
        unpacked_data= self.sendMessageReadResponse(rid,sendData)
        return 
    
    def setChopVel(self, vel):
        """
        vel: 0=n/a, 1=10.42Hz, 2= fixed position, 3= 5.21Hz
        """
        rid = SET_CHOP_VEL[0]
        sendData = str(bytearray([vel]))
        unpacked_data= self.sendMessageReadResponse(rid,sendData)
        return 

    def setChopPhase(self, phase):
        """
        phase: 0: cold load, 1=skyA, 2=hot load, 3= skyB
        """
        rid = SET_CHOP_PHASE[0]
        sendData = str(bytearray([phase]))
        unpacked_data= self.sendMessageReadResponse(rid,sendData)
        return 
       
    def checkTftpServer(self):
        """
        function which checks if the tftp server is running.
        Only used in setCalUpload and setCalReprg
        """
        if 'tftpy' not in (os.popen('ps -elf | grep [t]ftpy_server.py')).read():
            print "WARNING: Run the tftp server before calling this command."
            print "        In a separate window, run:"
            print "        - sudo tftpy_server.py -r ~/WVR_Omnisys/tftp/"
            print "        - enter passwd"
            print "        - tftpy should be running"
            return 1
        else:
            print "TFTP Server is running, proceeding... "
            return 0

    def setCalReprg(self, calFilename = ''):
        """
        download a new caliberation file from an tftp server 
        to wvr and copied it to non-volatile memory on the WVR. 
        This calibration file is then used by the WVR after reboot
        """
        rid = SET_CAL_REPRG[0]
        # check tftp server is running
        if self.checkTftpServer(): 
            return
        if calFilename == '':
            print "ERROR: You must specify a filename you want to download to the WVR"
            return

        serverIP = self.wvrTftpServer
        unpacked_data= self.sendMessageReadResponse(rid,'',serverIP,calFilename)
        if self.debug: print unpacked_data
        print self.getSwRev()


    def setCalUpload(self):
        """
        upload the wvr calibration file to an tftp server.
        For this to work, a tftp server must be running.
        In a separate window, run:
            - sudo tftpy_server.py -r ~/WVR_Omnisys/tftp/
            - enter passwd
            - tftp server should be running
        """
        # check tftp server is running
        if self.checkTftpServer(): 
            sys.exit()

        rid = SET_CAL_UPLOAD[0]
        serverIP = self.wvrTftpServer
        now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        calFile = 'NewCalFile_%s.txt'%now
        unpacked_data= self.sendMessageReadResponse(rid,'',serverIP,calFile)
        if self.debug: print unpacked_data

    #################
    #Monitoring points
    #################
 
    def getSwRev(self):
        rid = GET_SW_REV[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res =  struct.unpack('8B',unpacked_data[2])
        if self.debug:
            print "CPU_rev:%d.%d FPGA_rev:%d.%d CALfile_rev: %d.%d serial_rev:%d.%d" %(res)
        return res
        
    def getWvrAlarms(self):
        rid = GET_WVR_ALARMS[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res =  struct.unpack('8B',unpacked_data[2])
        byts =  get_bits(res[1],3)
        ctrl =  get_bits(res[1],2)
        V12 =  get_bits(res[1],0)
        curr = res[0]
        volt = res[2]
        temp = res[3]
        test = res[4]
        if self.debug:
            print "BYTES: %d, CTRL: %d, 12V: %d" %(byts, ctrl, V12)
            print "CURR: %d, VOLT: %d, TEMP: %d, TEST: %d" %(curr, volt, temp, test)
        return (byts, ctrl, V12, curr, volt, temp, test)

    def getWvrState(self):
        rid = GET_WVR_STATE[0]
        unpacked_data = self.sendMessageReadResponse(rid, '')
        res =  array.array('B', unpacked_data[2])[0]
        te = get_bits(res,7)
        clk = get_bits(res,6)
        boot = get_bits(res,5)
        alarm = get_bits(res,4)
        op = get_bits(res,2)
        mode = 2 * get_bits(res, 1) + get_bits(res, 0)
        if self.debug:
            print "TE:%d CLK:%d BOOT:%d ALARM:%d OP:%d MODE:%d"%(te,clk,boot,alarm,op,mode)
            if mode == 0:
                print "Mode: Operational"
            elif mode == 1:
                print "Mode: Idle"
            elif mode == 2:
                print "Mode: Configuration"
        return (mode, op, alarm, boot, clk, te)

    def getColdTemp(self):
        rid = GET_COLD_TEMP[0]
        unpacked_data= self.sendMessageReadResponse(rid,'')
        res =  struct.unpack('ff',unpacked_data[2])
        if self.debug: print "COLD LOAD SETPOINT: %3.3fK\n          MEASURED: %3.4fK"%(res[1],res[0])
        return res
        
    def getHotTemp(self):
        rid = GET_HOT_TEMP[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res =  struct.unpack('ff',unpacked_data[2])
        if self.debug: print "HOT LOAD SETPOINT: %3.3fK\n         MEASURED: %3.4fK"%(res[1],res[0])
        return res

    def getChopState(self):
        """
        Get chopper state.

        Returns
        -------
        ph : int
            Chopper wheel present phase.
            0 = cold load / no phase shift
            1 = sky A     / 90 degrees
            2 = hot load  / 180 degrees
            3 = sky B     / 270 degrees
        vel : int
            Chopper wheel present velocity.
            0 = Not applicable
            1 = 10.42 Hz (96 ms per revolution)
            2 = Fixed 
            3 = 5.21 Hz (192 ms per revolution)

        """
        rid = GET_CHOP_STATE[0]
        unpacked_data= self.sendMessageReadResponse(rid,'')
        res =  array.array('B',unpacked_data[2])[0]
        ph = get_bits(res,5)*2+get_bits(res,4)
        vel = get_bits(res,1)*2+get_bits(res,0)
        if self.debug:
            if ph == 0:
                phase = 'ColdLoad'
            elif ph == 1:
                phase = 'skyA'
            elif ph == 2:
                phase = 'HotLoad'
            elif ph == 3:
                phase = 'SkyB'
            if vel == 1:
                chopV = '10.42Hz'
            elif vel== 2:
                chopV = 'Fixed'
            elif vel == 3:
                chopV = '5.21 Hz'
            print "CHOP PHASE: %s,  VELOCITY: %s" %(phase,chopV)
        return (ph, vel)


    def getChopPwm(self):
        rid = GET_CHOP_PWM[0]
        unpacked_data = self.sendMessageReadResponse(rid, '')
        res = array.array('B',unpacked_data[2])[0]
        pwmfrac = 100*res/256.
        if self.debug: print "CHOPPER PWM: %d (256 max) = %2.1f%%"%(res,pwmfrac)
        return pwmfrac

    def getChopPos(self):
        """Doesn't currently uppack data correctly."""
        rid = GET_CHOP_POS[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = struct.unpack('8B',unpacked_data[2])
        if self.debug: print "CHOPPER POS:%d  ZERO-POSITION:%d"%(res[0],res[1])
        return res

    def getChopCurr(self):
        rid = GET_CHOP_CURR[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "CHOPPER SUPPLY CURRENT:%3.3f Amps"%(res)
        return res

    def getHotPwm(self):
        rid = GET_HOT_PWM[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('B',unpacked_data[2])[0]
        pwmfrac = 100*res/256.
        if self.debug: print "HOT LOAD PWM:%d (256 max) = %2.1f%%"%(res,pwmfrac)
        return pwmfrac

    def getHotNtc(self):
        rid = GET_HOT_NTC[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('H',unpacked_data[2])[0]
        if self.debug: print "HOT LOAD NTC TEMP:%d (65536 max)"%(res)
        return res

    def getColdPwm(self):
        rid = GET_COLD_PWM[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('B',unpacked_data[2])[0]
        pwmfrac = 100*res/256.
        if self.debug: print "COLD LOAD PWM:%d (256 max) = %2.1f%%"%(res,pwmfrac)
        return pwmfrac

    def getColdNtc(self):
        rid = GET_COLD_NTC[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('H',unpacked_data[2])[0]
        if self.debug: print "COLD LOAD NTC TEMP:%d (65536 max)"%(res)
        return res

    def getCtrl12Curr(self):
        rid = GET_CTRL_12CURR[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "+12V CURRENT:%3.3f A"%(res)
        return res

    def getCtrl6Curr(self):
        rid = GET_CTRL_6CURR[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "+6V CURRENT:%3.3f A"%(res)
        return res

    def getCtrlM6Curr(self):
        rid = GET_CTRL_M6CURR[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "-6V CURRENT:%3.3f A"%(res)
        return res

    def getCtrl12Volt(self):
        rid = GET_CTRL_12VOLT[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "+12V VOLTAGE:%3.3f V"%(res)
        return res

    def getCtrl6Volt(self):
        rid = GET_CTRL_6VOLT[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "+6V VOLTAGE:%3.3f V"%(res)
        return res

    def getCtrlM6Volt(self):
        rid = GET_CTRL_M6VOLT[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "-6V VOLTAGE:%3.3f V"%(res)
        return res

    def getCtrlNtc(self):
        rid = GET_CTRL_NTC[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('H',unpacked_data[2])[0]
        if self.debug: print "CTRL BOARD NTC TEMP:%d (65536 max)"%(res)
        return res

    def getTpTemp(self):
        rid = GET_TP_TEMP[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res =  struct.unpack('ff',unpacked_data[2])
        if self.debug: print "TOP PLATE SETPOINT: %3.3fK\n          MEASURED: %3.4fK"%(res[1],res[0])
        return res

    def getTpPwm(self):
        rid = GET_TP_PWM[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('B',unpacked_data[2])[0]
        pwmfrac = 100*res/256.
        if self.debug: print "TOP PLATE PWM: %d (max 256) = %2.1f"%(res,pwmfrac)
        return pwmfrac

    def getBeTemp(self):
        rid = GET_BE_TEMP[0]
        unpacked_data = self.sendMessageReadResponse(rid, '')
        res =  struct.unpack('ff',unpacked_data[2])
        if self.debug: print "BACKEND SETPOINT: %3.3fK\n        MEASURED: %3.4fK"%(res[1],res[0])
        return res
        
    def getBePwm(self):
        rid = GET_BE_PWM[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('B',unpacked_data[2])[0]
        pwmfrac = 100*res/256.
        if self.debug: print "BE PWM: %d (256max) = %2.1f%%"%(res,pwmfrac)
        return pwmfrac

    def getBeNtc(self):
        rid = GET_BE_NTC[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('H',unpacked_data[2])[0]
        if self.debug: print "BE NTC TEMP:%d (65536 max)"%(res)
        return res

    def getBeBias0(self):
        rid = GET_BE_BIAS0[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BIAS VOLTAGE FOR FILTERBANK0 = %3.3f V"%(res)
        return res

    def getBeBias1(self):
        rid = GET_BE_BIAS1[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BIAS VOLTAGE FOR FILTERBANK1 = %3.3f V"%(res)
        return res

    def getBeBias2(self):
        rid = GET_BE_BIAS2[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BIAS VOLTAGE FOR FILTERBANK2 = %3.3f V"%(res)
        return res

    def getBeBias3(self):
        rid = GET_BE_BIAS3[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BIAS VOLTAGE FOR FILTERBANK3 = %3.3f V"%(res)
        return res

    def getBeBw0(self):
        rid = GET_BE_BW0[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BANDWIDTH FOR FILTERBANK0 =%3.3f MHz"%(res)
        return res

    def getBeBw1(self):
        rid = GET_BE_BW1[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BANDWIDTH FOR FILTERBANK1 =%3.3f MHz"%(res)
        return res

    def getBeBw2(self):
        rid = GET_BE_BW2[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BANDWIDTH FOR FILTERBANK2 =%3.3f MHz"%(res)
        return res

    def getBeBw3(self):
        rid = GET_BE_BW3[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "BE BANDWIDTH FOR FILTERBANK3 =%3.3f MHz"%(res)
        return res

    def getCsTemp(self):
        rid = GET_CS_TEMP[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res =  struct.unpack('ff',unpacked_data[2])
        if self.debug: print "CS SETPOINT: %3.3fK\n   MEASURED: %3.4fK"%(res[1],res[0])
        return res
        
    def getCsPwm(self):
        rid = GET_CS_PWM[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('B',unpacked_data[2])[0]
        pwmfrac = 100*res/256.
        if self.debug: print "CS PWM: %d (256 max) = %2.1f%%"%(res,pwmfrac)
        return pwmfrac

    def getCsNtc(self):
        rid = GET_CS_NTC[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('H',unpacked_data[2])[0]
        if self.debug: print "CS NTC TEMP: %d"%(res)
        return res

    def getLoFreq(self):
        rid = GET_LO_FREQ[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('I',unpacked_data[2])[0]
        if self.debug: print "LO FREQ: %i kHz"%(res)
        return res

    def getLoBias0(self):
        rid = GET_LO_BIAS0[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "LO BIAS VOLTAGE 0: %3.3f V"%(res)
        return res

    def getLoBias1(self):
        rid = GET_LO_BIAS1[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "LO BIAS VOLTAGE 1: %3.3f V"%(res)
        return res

    def getLnaTemp(self):
        rid = GET_LNA_TEMP[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        res = array.array('f',unpacked_data[2])[0]
        if self.debug: print "LNA TEMP: %3.3f K"%(res)
        return res
        
    def getWvrPart(self):
        # doesn't currently work#
        rid = GET_WVR_PART[0]
        unpacked_data = self.sendMessageReadResponse(rid,'')
        print unpacked_data
        res =  struct.unpack('LL',unpacked_data[2])
        print res
        if self.debug: print "PART ID: %d  REV: %l"%(res[0],res[1])
        return res

    def getInt(self,mp=None):
        """
        function to retrieve any of the Wvr data integrations
        works for GET_INT_TRSC, EST, HOT, COLD, SKYA, SKYB
        """
        if mp == None:
            print "Specify a Monitor point"
            return
        rid = mp[0]
        unpacked_data = self.sendMessageReadResponse(rid, '')
        res =  struct.unpack('ff', unpacked_data[2])
        if self.debug: print "time: %3.3f  Tsrc0: %3.3fK"%(res[1],res[0])
        return res
                
    def getTsrc(self,chan=0):
        rid = GET_INT_TSRC0[0]+8*chan
        unpacked_data= self.sendMessageReadResponse(rid,'')
        res =  struct.unpack('ff',unpacked_data[2])
        if self.debug: print "time: %3.7f  Tsrc0: %3.3fK"%(res[1],res[0])
        return res
            
    def getMbuf(self,chan=0):
        """
        Get memory buffer holding raw data.

        Parameters
        ----------
        chan : int
            WVR channel in range [0:3]

        Returns
        -------
        time : flt
            Timestamp, in seconds, corresponding to the last phase of the 
            data array.
        data : ndarray
            Data array with shape [4,N] where N is the number of phases read.
            Data-type is int.

        """
        # Message id.
        rid = GET_INT_MBUF0[0] + 8 * chan
        # Get first message containing size of data packet and timestamp.
        unpacked_data = self.sendMessageReadResponse(rid, '', autoClose=False)
        (Nphase, time) = struct.unpack('ff', unpacked_data[2])
        Nphase = int(Nphase) # Number of phases in buffer.
        ss = 16 * Nphase     # Size of data buffer in bytes.
        # Data could arrive in multiple socket messages. 
        # Concatenate into one str.
        datastr = ''
        while len(datastr) < ss:
            datastr = datastr + self.sock.recv(ss - len(datastr))
        self.sock.close()
        # Unpack data into array with size [4,Nphase].
        data = np.array([struct.unpack('iiii', datastr[i*16:(i+1)*16]) 
                         for i in range(Nphase)])
        # Return timestamp and data array.
        return (time, data)


    ##############
    # Additionnal function
    ##############
    def rebootWvr(self):
        """
        Simple wrapper to reboot WVR
        """
        self.setWvrState(1,(0,1,0,0))
        print "Rebooted WVR... This will take 30s... Please wait..."
        time.sleep(30)
        if self.debug: print self.getWvrState()

    def clearWvrAlarms(self):
        """
        when an alarm is present, use this function to 
        clear the alarm. 
        """
        self.getWvrAlarms()
        print ""
        print "Clearing Alarms by resetting trip bit and mode to IDLE"
        print ""
        self.setWvrState(1,(0,0,1,0))
        self.getWvrAlarms()
        
    def setWvrToOperation(self):
        """
        Function to set WVR from Idle mode (mode = 1)  
        to Operational mode (mode=0), 
        and start the  chopper wheel turning
        Returns 1 if all happens well.
        Returns 0 if there is a problem
        
        """
        st = self.getWvrState()
        ch = self.getChopState()
        als = self.getWvrAlarms()
        al = sum(als[:])
        op = st[1]
        mode = st[0]
        vel = ch[1]

        if mode == 0 and vel == 3:
            # only reset timestamp counter
            self.setWvrState(0,(0,0,0,1))
            return 1

        if al != 0 :
            print "ERROR: Cannot go to Operational Mode, Alarms detected. check Alarms"
            print als
            return 0
        else:
            if self.debug: print "ALARMS: OK"
        
        if op == 0:
            print "ERROR: Cannot go to Operational Mode, WVR still warming up"
            return 0
        else:
            if self.debug: print "Ready for Operational Mode: OK"
            # sets the mode to Operational, 
            # clears the timestamp counter, 
            # clear CPU boot bit.
            self.setWvrState(0,(0,0,1,1))
            self.setChopVel(3)
            time.sleep(12)
            if self.debug: print self.getChopState()
            return 1

    def getStatus(self):
        
        """
        function to print all the health status of WVR
        
        """
        t = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')  
        al = self.getWvrAlarms()
        st = self.getWvrState()
        coldT = self.getColdTemp()
        coldPwm = self.getColdPwm()
        hotT = self.getHotTemp()
        hotPwm = self.getHotPwm()
        tpT = self.getTpTemp()
        tpPwm = self.getTpPwm()
        csT = self.getCsTemp()
        csPwm = self.getCsPwm()
        beT = self.getBeTemp()
        bePwm = self.getBePwm()
        lnaT = self.getLnaTemp()
        chopState = self.getChopState()
        chopPwm = self.getChopPwm()
        Cchop = self.getChopCurr()
        V12=self.getCtrl12Volt()
        C12=self.getCtrl12Curr()
        V6  = self.getCtrl6Volt()
        C6  = self.getCtrl6Curr()
        VM6 =self.getCtrlM6Volt()
        CM6 =self.getCtrlM6Curr()
        lof = self.getLoFreq()
        lobias0 = self.getLoBias0()
        lobias1 = self.getLoBias1()
        if self.debug:
            print('# timestamp                 , byts, ctrl,  V12, curr, volt, temp, test, mode,   op, alrm, boot,  clk,   te,  Cold Temp Setpoint,  Cold Temp Measured,  Cold PWM, Hot Temp Setpoint,  Hot Temp Measured,  Hot PWM, TP Temp Setpoint,  TP Temp Measured,  TP Temp PWM,  CS Temp Setpoint,  CS Temp Measured, CS PWM, BE Temp Setpoint,  BE Temp Measured, BE PWM, Lna Temp, V12, V6, VM6, C12, C6, CM6, LO_freq, LO_bias0, LO_bias1')
            print '%s,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d,%5d, %3.3f, %3.3f, %2.2f, %3.3f, %3.3f, %2.2f, %3.3f, %3.3f, %2.2f,%3.3f, %3.3f, %2.2f, %3.3f, %3.3f, %2.2f, %3.3f, %2.2f, %2.2f, %2.2f, %2.2f, %2.2f, %2.2f, %d,%2.2f, %2.2f'%(t, al[0],al[1],al[2],al[3],al[4],al[5],al[6],st[0],st[1],st[2],st[3],st[4],st[5],coldT[1],coldT[0],coldPwm,hotT[1],hotT[0],hotPwm, tpT[1],tpT[0],tpPwm,csT[1],csT[0],csPwm,beT[1],beT[0],bePwm,lnaT,V12,V6,VM6,C12,C6,CM6,lof,lobias0,lobias1)
        else:
            return (t, al,st,coldT,coldPwm,hotT,hotPwm, tpT,tpPwm,csT,csPwm,beT,bePwm,lnaT,V12,V6,VM6,C12,C6,CM6,lof,lobias0,lobias1)
    
    
