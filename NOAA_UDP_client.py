#!/usr/bin/env python
from __future__ import print_function
import pdb
import os, sys, threading, asyncore, socket, time, subprocess, signal
from datetime import datetime

class ClientException(Exception):
    pass

class Client(asyncore.dispatcher, object):
    """
    The Client class runs an asyncore listener to process 
    incoming UDP packets
    asynchronously. When a UDP packet arrives, handle_read is triggered, 
    and the data is added to a buffer. 
    If the hour at which the packet arrives is
    not equal to the hour to which the buffer corresponds, 
    the buffer is flushed
    and the hour is updated to the current hour.
    Client tries to exit gracefully under normal conditions. 
    If Client fails to
    disconnect, it can be forcefully killed with SIGKILL (kill -9).
    """
    buffer_lock = threading.Lock()
    pid_file = "/var/run/NOAA_UDP_client.pid"
    def __init__(self, port=2101, ip='192.168.1.39', warn_interval=300):
        super(Client, self).__init__()
        self.warn_interval = warn_interval
        self.data_buffer = []
        self.port = int(port)
        self.ip = str(ip)
        self.home = os.getenv('HOME')
        self.dataDir = os.path.join(self.home, 'wvr_data') #symlink to where the data is

    @staticmethod
    def get_cur_hour():
        now = datetime.now()
        return (now.year, now.strftime('%m'), now.strftime('%d'), now.strftime('%H'))

    @staticmethod
    def signal_handler(signum, frame):
        raise ClientException("Received kill signal - exiting")

    def get_process_lock(self, check_proc=True):
        self.has_lock = False
        try:
            with open(Client.pid_file, 'r') as lock_file:
                pid = lock_file.read()
        except IOError:
            pass
        else:
            # If PID file did exist, we check if it corresponds to a running process.
            if pid.isdigit():
                if check_proc:
                    python_procs = []
                    try:
                        python_procs = subprocess.check_output(
                                "pgrep -f {0}".format(os.path.basename(__file__)),
                                shell=True).split('\n')
                    except subprocess.CalledProcessError:
                        pass
                    else:
                        if pid in python_procs:
                            raise ClientException("Client already running: PID {0}".format(pid))
                else:
                    raise ClientException("PID file {0} has PID {1}".format(Client.pid_file, pid))
        my_pid = str(os.getpid())
        with open(Client.pid_file, 'w') as lock_file:
            lock_file.write(my_pid)
        self.has_lock = True

    def start(self, daemonize=True):
        self.last_read_time = time.time()
        self.buffer_cur_hour = Client.get_cur_hour()
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        self.bind((self.ip, self.port))
        asyncore.looper = threading.Thread(target=asyncore.loop,
                                           kwargs={'timeout': 30})
        asyncore.looper.setDaemon(daemonize)
        asyncore.looper.start()
        print("Listening on UDP {0}:{1}".format(self.ip, self.port))

    def check_flush_buffer(self):
        if(time.time()-self.last_read_time>self.warn_interval):
            print("Warning: No data received for {1} minutes.".format(
                  (time.time()-self.last_read_time)/60), file=sys.stderr)
        cur_hour = Client.get_cur_hour()
        with Client.buffer_lock:
            if cur_hour != self.buffer_cur_hour:
                self.flush_buffer()

    def flush_buffer(self):
        try:
            filename = "{0}{1}{2}_{3}0000_Wx_Summit_NOAA.txt".format(*self.buffer_cur_hour)
            with open(os.path.join(self.dataDir, filename), 'a+') as data_file:
                data_file.write(''.join(self.data_buffer))
            self.data_buffer = []
            self.buffer_cur_hour = Client.get_cur_hour()
        except Exception as e:
            print("Could not write to file: {0}".format(e), file=sys.stderr)
        
    def writable(self):
        return False

    def handle_read(self):
        self.last_read_time = time.time()
        try:
            self.check_flush_buffer()
            buf = self.recv(4096)
            with Client.buffer_lock:
                self.data_buffer.append(buf)
        except Exception as e:
            print("Read failed: {0}".format(e), file=sys.stderr)

    def __enter__(self):
        self.get_process_lock()
        # Attach signal handlers
        signal.signal(signal.SIGTERM, Client.signal_handler)
        signal.signal(signal.SIGHUP, Client.signal_handler)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.has_lock:
            print("\nClosing listeners", file=sys.stderr)
            asyncore.close_all()
            self.flush_buffer()
            # Clear PID file
            with open(Client.pid_file, 'w+') as lock_file:
                pass

if __name__ == '__main__':
    try:
        with Client() as c:
            c.start()
            # Wait until all threads die before __exit__ing
            while True:
                time.sleep(60)
                try:
                    c.check_flush_buffer()
                except:
                    pass
    except KeyboardInterrupt:
        pass
    except ClientException as e:
        print(e, file=sys.stderr)
