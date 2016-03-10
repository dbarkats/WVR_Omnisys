#!/usr/bin/env python

# wvrArchiveData.py
# search for files in TEMPDIR and tar gz them into a single file
# and move them over to /wvr/data

#from __future__ import print_function
import datetime
import glob
import os
import sys

TEMPDIR = '/home/dbarkats/WVR_Omnisys/data_tmp';
ARCHDIR = '/data/wvr';
script = 'wvrArchiveData.py'
oldpwd = os.getcwd();

# Also print to standard output
ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S');
print "Starting %s at %s"%(script,ts)

# List all data files in the temporary directory.
os.chdir(TEMPDIR);
filelist = glob.glob('*_fast.txt');

# Also build a list of the data which has already been archived.
os.chdir(ARCHDIR);
archlist = glob.glob('*.tar.gz');

os.chdir(oldpwd);

# Remove text data files which already have a compressed archive on disk, and
# also skip over a data file for the current hour which is still being
# written to.
filtlist = [];
nowstamp = datetime.datetime.now().strftime('%Y%m%d_%H');
for datafile in filelist:
    fname = datafile.replace('_fast.txt','.tar.gz');
    if fname not in archlist and not datafile.startswith(nowstamp):
        filtlist.append(datafile);


# For each data file in the filtered list, we need to archive several files
# together.
os.chdir(TEMPDIR);
filegroup = []
for datafile in filtlist:
    archfile = datafile.replace('_fast.txt', '.tar.gz');
    baseName = datafile.strip('_fast.txt')
    filegroup = glob.glob(baseName+'*.txt')
    print filegroup
    fileTypes = [n.split('_')[-1] for n in filegroup]
    print "In %s filegroup, there are %d files: %s \n"\
        %(baseName, len(filegroup),', '.join(fileTypes))

    # Verify that each necessary file exists
    #if not os.path.exists(fastfile):
    #    print('Fast file {} does not exist'.format(fastfile), file=sys.stderr);
    #    #continue
    #if not os.path.exists(slowfile):
    #    print('Slow file {} does not exist'.format(slowfile), file=sys.stderr);
    #    #continue
    #if not os.path.exists(statfile):
    #    print('Stat file {} does not exist'.format(statfile), file=sys.stderr);
    #    #continue

        
    # Archive the pieces together with tar, then move to the archive
    # directory.
    print "Writing archive {}...".format(archfile)
    os.system("tar czf {} {}".format(archfile,' '.join(filegroup)));
    os.rename(archfile, os.path.join(ARCHDIR, archfile));

os.system("tar czf wvrLog.tgz wvrLog.txt")
os.rename('wvrLog.tgz', os.path.join(ARCHDIR, 'wvrLog.tgz'));
os.chdir(oldpwd);x

ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S');
print "Stopping %s at %s"%(script,ts)
