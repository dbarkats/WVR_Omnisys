import socket

class Socket(socket.socket):

    def readline(self):
        n = ''
        while True:
            c = self.recv(1)exit

            n = n + c
            if c == '\n':
                break
        return n
            
####
# import Socket as S
#  s = S.Socket(S.socket.AF_INET, S.socket.SOCK_STREAM)
# s.connect(('131.142.156.77',4321))
# s.recv(20000000
# s.readline()
