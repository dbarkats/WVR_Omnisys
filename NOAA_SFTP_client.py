#!/usr/bin/env python
from __future__ import print_function
import os, sys, time, subprocess, signal, pysftp, StringIO
from datetime import datetime

class ClientException(Exception):
    pass

class Client(object):
    """
    The Client class pulls a data file from an SFTP server at a given interval
    and compares it to the last data received. If it has changed, it adds the
    contained data to the data buffer.
    If the hour at which the data is pulled is not equal to the hour to which
    the buffer corresponds, the buffer is flushed and the hour is updated to
    the current hour.
    Client tries to exit gracefully under normal conditions.
    If Client fails to disconnect, it can be forcefully killed with SIGKILL
    (kill -9).
    """
    pid_file = ".NOAA_SFTP_client.pid"
    def __init__(self, sftp_server='157.132.47.58', user='spo', password='',
            data_file='spo_recent.dat', poll_interval=45,  warn_interval=300):
        super(Client, self).__init__()
        self.sftp_server = sftp_server
        self.user = user
        self.data_file = data_file
        self.poll_interval = poll_interval
        self.warn_interval = warn_interval
        self.password = password
        self.data_buffer = []
        self.last_data = ""
        self.home = os.getenv('HOME')
        self.data_dir = os.path.join(self.home, 'wvr_data')

    def get_data(self):
        """
        Get data file from remote SFTP server and process.
        """
        tmp_data_buffer = StringIO.StringIO()
        try:
            with pysftp.Connection(self.sftp_server, username=self.user,
                                   password=self.password) as sftp:
                sftp.getfo(self.data_file, tmp_data_buffer)
            tmp_data_buffer.seek(0)
            data_line = tmp_data_buffer.readlines()[-1]
            if data_line != self.last_data:
                self.data_buffer.append(data_line)
                self.last_read_time = time.time()
                self.last_data = data_line
        except (pysftp.ConnectionException, pysftp.SSHException) as e:
            print("Error: Couldn't connect to SFTP server: {0}".format(e),
                  file=sys.stderr)
        except IOError as e:
            print("Error: Couldn't read data file: {0}".format(e),
                  file=sys.stderr)
        self.check_flush_buffer()

    @staticmethod
    def get_cur_hour():
        """
        Returns (y, m, d, h) tuple to determine when the data buffer should be
        flushed.
        """
        now = datetime.now()
        return (now.year, now.strftime('%m'), now.strftime('%d'), now.strftime('%H'))

    @staticmethod
    def signal_handler(signum, frame):
        raise ClientException("Received kill signal - exiting")

    def get_process_lock(self, check_proc=True):
        """
        Check if PID file is empty, and if so, add our PID so another client
        can not run. If the PID file is not empty and check_proc=True, check if
        the PID corresponds to a running process of the same name. If so, or if
        check_proc=False, get_process_lock raises an exception.
        """
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
                        if pid in python_procs:
                            raise ClientException("Client already running: PID {0}".format(pid))
                    except subprocess.CalledProcessError:
                        pass
                else:
                    raise ClientException("PID file {0} has PID {1}".format(Client.pid_file, pid))
        my_pid = str(os.getpid())
        with open(Client.pid_file, 'w') as lock_file:
            lock_file.write(my_pid)
        self.has_lock = True

    def free_process_lock(self):
        """
        Clear PID file so another client can start.
        """
        with open(Client.pid_file, 'w+') as lock_file:
            pass

    def start(self):
        """
        Start collecting data.
        """
        self.last_read_time = time.time()
        self.buffer_cur_hour = Client.get_cur_hour()
        print("Beginning data collection from {0}".format(self.sftp_server))
        while True:
            self.get_data()
            time.sleep(self.poll_interval)

    def check_flush_buffer(self):
        """
        Check if it's been 1 hour since we last created a data file. If so,
        flush data buffer to new data file and clear buffer.
        """
        if(time.time()-self.last_read_time>self.warn_interval):
            print("Warning: No data received for {0} minutes.".format(
                  int((time.time()-self.last_read_time)/60)), file=sys.stderr)
        cur_hour = Client.get_cur_hour()
        if cur_hour != self.buffer_cur_hour:
            self.flush_buffer()

    def flush_buffer(self):
        """
        Flush data buffer to hourly data file.
        """
        try:
            filename = "{0}{1}{2}_{3}0000_Wx_Spo_NOAA.txt".format(*self.buffer_cur_hour)
            with open(os.path.join(self.data_dir, filename), 'a+') as data_file:
                data_file.write(''.join(self.data_buffer))
            self.data_buffer = []
            self.buffer_cur_hour = Client.get_cur_hour()
        except Exception as e:
            print("Could not write to file: {0}".format(e), file=sys.stderr)

    def __enter__(self):
        """
        Gets process lock so no other client can start, and attaches signal
        handlers so the data buffer is properly cleared.
        """
        self.get_process_lock()
        # Attach signal handlers
        signal.signal(signal.SIGTERM, Client.signal_handler)
        signal.signal(signal.SIGHUP, Client.signal_handler)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Flush buffer to file before exiting, and release process lock.
        """
        if self.has_lock:
            self.flush_buffer()
            self.free_process_lock()

if __name__ == '__main__':
    try:
        with Client(password='met2016@spo!') as c:
            c.start()
            try:
                c.check_flush_buffer()
            except:
                pass
    except KeyboardInterrupt:
        pass
    except ClientException as e:
        print(e, file=sys.stderr)
