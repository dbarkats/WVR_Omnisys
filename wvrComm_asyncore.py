#! /usr/bin/env python

import threading, struct, socket
import time
from pylab import *

s = struct.Struct('B H 8s 20s 40s 40s')
# Cold temp
packet = s.pack(0, 0x01A0,'','','','')

class Client(threading.Thread):
    def __init__(self, ip, port):
        super(Client, self).__init__()
        self.ip = ip
        self.port = port

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.1)
        try:
            sock.connect((self.ip, self.port))
        except socket.timeout:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print "Connection %s timed out - reconnecting"%i
            sock.connect(('192.168.168.230', 9734))   
        sock.sendall(packet)
        ret = sock.recv(112)
        res = struct.unpack('ff',(s.unpack(ret))[2])[0]
        sock.close()
        #print "{0} got from server: {1}".format(self.getName(), res)
        return  s.unpack(ret)

if __name__ == '__main__':
    dt=[]
    N=200
    for i in xrange(N):
        # Each Client will spawn a thread and make a single request to the server
        c = Client('192.168.168.230', 9734)
        c.run()
        dt.append(time.time())
        
    print dt[-1]-dt[0],((dt[-1]-dt[0])/N)
    deltas = diff(dt)
    print max(deltas)

