import socket

class Socket(socket.socket):

    def readline(self):
        n = ''
        while True:
            c = self.recv(1)
            n = n + c
            if c == '\n':
                break
        return n
            
####
# import Socket as S
#  s = S.Socket(S.socket.AF_INET, S.socket.SOCK_STREAM)
# s.connect(('131.142.156.77',4321))
#while(1):
#    s.send('p')
#    g = s.readline()
#    #print g
#    t0 = t1
#    t1 = time.time()
#    dt.append(t1-t0)

