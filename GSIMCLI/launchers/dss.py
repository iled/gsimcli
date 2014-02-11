# -*- coding: utf-8 -*-
'''
Created on 04/10/2013

@author: jcaineta
'''

# import sarge

import copy
import datetime
import ntpath
import os
import shutil
import sys

import multiprocessing as mp
import parsers.dss as pdss
import subprocess as sp
from tools.utils import path_up


class DssEnvironment(object):
    """Handle the environment to run DSS old version, where the parameters file
    path is hard coded as DSSim.PAR.

    """
    def __init__(self, dss_path, par_path, output='dssim.out', simnum=0):
        """Constructor.

        """
        if isinstance(par_path, pdss.DssParam):
            self.par = copy.copy(par_path)
            self.par_path = self.par.path
        else:
            self.par_path = par_path
            self.par = pdss.DssParam()
            self.par.load_old(par_path)  # TODO: old

        self.envs = list()
        self.dss_path = dss_path
        self.exedir, self.exefile = os.path.split(dss_path)
        self.pardir, self.parfile = os.path.split(self.par_path)
        self.output = output
        self.simnum = simnum

        self.tempdir = os.path.join(self.pardir, 'temp')
        if not os.path.isdir(self.tempdir):
            os.mkdir(self.tempdir)
        self._update_paths()

    def new(self):
        """Create a new directory and copy EXE and PAR files into it.

        """
        os.chdir(self.tempdir)
        new_dir = os.path.join(self.tempdir, str(len(self.envs) + 1))
        if not os.path.isdir(new_dir):
            os.mkdir(new_dir)

        new_exe = os.path.join(new_dir, self.exefile)
        new_par = os.path.join(new_dir, 'DSSim.PAR')
        if not os.path.isfile(new_exe):
            shutil.copyfile(self.dss_path, new_exe)
        self.envs.append([new_dir, new_exe, new_par])

        # update path parameters and seed:
        if self.simnum > 1:
            outpath = (ntpath.splitext(self.output)[0] + str(self.simnum) +
                       ntpath.splitext(self.output)[1])
        else:
            outpath = self.output
        # remove the first directory in the the output tree
        # splitpath = ntpath.split(outpath)
        # outpath = ntpath.join(ntpath.basename(splitpath[0]), splitpath[1])
        keywords = ['output', 'seed']
        values = ['..\\..\\..\\' + outpath, self.par.seed + 2 * self.simnum]
        self.par.update(keywords, values)
        self.par.save_old(new_par)
        self.simnum += 1

        return new_exe, new_par

    def purge(self):
        """Remove all files and directories created for the environment.

        """
        shutil.rmtree(self.tempdir)
        
    def reset_par_path(self):
        """Restore the original parameter file path.
        
        """
        self.par.path = os.path.join(self.pardir, self.parfile)
        
    def _update_paths(self):
        """Update the parameters related to file paths. Prepends '..\..\'.
        Necessary to call multiprocessing DSS launcher.

        """
        params = ['datapath', 'corrpath', 'secpath']

        for param in params:
            val = getattr(self.par, param)
            if val and val != 'no file':
                # FIXME: not a pretty solution... code smell
                setattr(self.par, param, '..\\..\\..\\' + val)


# def normal(exe_path, par):
"""Launch normal version of DSS"""
"""    os.chdir(os.path.dirname(exe_path))
    if os.name == 'posix':
        cmd = ['wine', os.path.basename(exe_path), par]
    else:
        cmd = [os.path.basename(exe_path), par]
    prog = sarge.Command(cmd, shell=False,
                        stdout=sarge.Capture(buffer_size=1))
    progrun = prog.run(input=sp.PIPE, async=True)

    return progrun
"""


def execute(command):
    process = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() != None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise ProcessException(command, exitCode, output)  # @UndefinedVariable


def exec_ssdir(dss_path, par_path, dbg=None, print_status=False):
    # print 'Running {}...'.format(os.path.basename(dss_path))
    print mp.current_process().name

    if os.name == 'posix':
        env = 'wine '
    else:
        env = str()
    command = env + dss_path + ' ' + par_path
    wd = os.path.dirname(dss_path)
    process = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT,
                       cwd=wd)

    # sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    if dbg:
        dbgtest = open(dbg, 'ab')

    while True:
        nextline = process.stdout.readline()
        if print_status:
            if 'realization number' in nextline:
                print nextline.strip()
                # sys.stdout.write(nextline)
                # sys.stdout.flush()
            # if 'progress' in nextline:
                # print 'Progress: {}'.format(nextline.split()[-1])
                # sys.stdout.write(nextline)
                # sys.stdout.flush()
            if 'error' in nextline.lower():
                print nextline
                # sys.stdout.write(nextline)
                # sys.stdout.flush()
            if 'elapsed time' in nextline.lower():
                print ' '.join(nextline.split()[:4])

        if not nextline and process.poll() is not None:
            break
        # sys.stdout.write(nextline)
        # sys.stdout.flush()
        if dbg:
            dbgtest.write(str(datetime.datetime.now()) + '  ')
            dbgtest.write(nextline)
            dbgtest.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise SystemError(command, exitCode, output)


def mp_exec(dss_path, par_path, output, simnum, stop=None, dbg=None,
            print_dss_status=False, cores=None, print_mp_status=False,
            purge=False):
    """Launch multiple instances of DSS at the same time, at different cores.

    """
    if not cores:
        cores = mp.cpu_count()
    if print_mp_status:
        print 'Running {} in {} cores'.format(os.path.basename(dss_path),
                                                cores)

    runs = list()
    dssenv = DssEnvironment(dss_path, par_path, output, simnum)

    for run in xrange(cores):
        if stop and simnum + run > stop:
            break
        dss_run, par_run = dssenv.new()
        run_exe = mp.Process(target=exec_ssdir, args=(dss_run, par_run,
                                                      dbg, print_dss_status))
        runs.append(run_exe)
        run_exe.start()

    for run in runs:
        run.join()

    dssenv.reset_par_path()
    if purge:
        dssenv.purge()


if __name__ == '__main__':
    dssexe = '/Users/julio/Desktop/testes/newDSSIntelRelease.exe'
    dsspar = '/Users/julio/Desktop/testes/DSSim.PAR'
    # print 'Running DSS...'
    # dssn = normal(dssexe, dsspar)
    # execute(dssexe)
    # exec_ssdir(dssexe, dsspar)
    # raw_input()
    # dssn.terminate()
    mp_exec(dssexe, dsspar, 'testinho.out', 1, print_dss_status=False,
            print_mp_status=True, stop=1)
    print 'done'
