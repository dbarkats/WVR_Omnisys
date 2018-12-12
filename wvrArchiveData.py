#!/usr/bin/env python

# wvrArchiveData.py
# search for files in TEMPDIR and tar gz them into a single file
# and move them over to /wvr/data

import datetime
import glob
import os
import sys

HOME = os.getenv('HOME')
TEMPDIR = HOME+'/wvr_data/';
ARCHDIR = '/data/wvr';
script = 'wvrArchiveData.py'
oldpwd = os.getcwd();

# Also print to standard output
ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S');
print "Starting %s at %s"%(script,ts)
sys.stdout.flush()

# List all data files in the temporary directory.
os.chdir(TEMPDIR);
#filelist = glob.glob('*_fast.txt');
filelist = glob.glob('2018*_log.txt')

# Also build a list of the data which has already been archived.
os.chdir(ARCHDIR);
archlist = glob.glob('2018*.tar.gz');

os.chdir(oldpwd);

# Remove text data files which already have a compressed archive on disk, and
# also skip over a data file for the current hour which is still being
# written to.
filtlist = [];
nowstamp = datetime.datetime.now().strftime('%Y%m%d_%H');
for datafile in filelist:
    fname = datafile.replace('_log.txt','.tar.gz');
    if fname not in archlist and not datafile.startswith(nowstamp):
        filtlist.append(datafile);

# For each data file in the filtered list, we need to archive several files
# together.
os.chdir(TEMPDIR);

filegroup = []
for datafile in filtlist:
    archfile = datafile.replace('_log.txt', '.tar.gz');
    baseName = datafile.strip('_log.txt')
    ymd = baseName.split('_')[0]
    hms = baseName.split('_')[1]
    filegroup = glob.glob(baseName+'*.txt')
    # add Wx file if it exists
    wxFile = glob.glob('%s_%s0000_Wx_*_NOAA.txt'%(ymd,hms[0:2]))
    print wxFile
    if wxFile != []:
        if os.path.isfile(wxFile[0]):
            filegroup = filegroup+wxFile
    print filegroup
    fileTypes = [n.split('_')[-1] for n in filegroup]
    print "In %s filegroup, there are %d files: %s \n"\
        %(baseName, len(filegroup),', '.join(fileTypes))

    # Archive the pieces together with tar, then move to the archive
    # directory.
    print "Writing archive {}...".format(archfile)
    os.system("tar czf {} {}".format(archfile,' '.join(filegroup)));
    os.rename(archfile, os.path.join(ARCHDIR, archfile));

os.system("tar czf 2018wvrLog.tar.gz wvrLog.txt")
os.rename('2018wvrLog.tar.gz', os.path.join(ARCHDIR, '2018wvrLog.tar.gz'));
os.chdir(oldpwd)

ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S');
print "Stopping %s at %s"%(script,ts)
