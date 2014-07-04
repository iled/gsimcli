# -*- coding: utf-8 -*-
"""
This module provides tools to control the execution of the *Direct Sequencial
Simulation* (DSS) program.

DSS is not open source software and is not part of GSIMCLI. Although, it is
freely available at CMRP Software website, within the GeoMS_ package. For
GSIMCLI, the only requirement from GeoMS is the DSS binary file.

.. _GeoMS: https://sites.google.com/site/cmrpsoftware/geoms

Created on 04/10/2013

@author: julio
"""

import copy
import datetime
import ntpath
import os
import shutil
import sys

import multiprocessing as mp
import parsers.dss as pdss
import subprocess as sp
import tools.utils as ut


class DssEnvironment(object):
    """Handle the environment to run the *old version* of DSS, in which the
    parameters file path is hard coded as *DSSim.PAR*.

    In this version of DSS, both binary and parameters files must be within the
    same directory. When running multiple threads of DSS, in order to avoid
    overlapping accesses to the same parameters file (which would probably lead
    to execution failure), each thread should be run from a different
    directory.

    This class does that: it creates new directories and copy both binary and
    parameters files to that new directory. It also updates the parameters
    which are path related.

    Attributes
    ----------
    envs : list
        Keep track of created directories and files.
    par : DssParam object
        Instance of DssParam containing the actual DSS parameters.
    par_path : string
        Parameters file path.
    pardir : string
        Parameters directory path.
    parfile : string
        Parameters file name.
    dss_path : string
        Binary file path.
    exedir : string
        Binary directory path.
    exefile : string
        Binary file name.
    output : string
        Simulation output file path.
    simnum : int
        Number of the next realization.
    tempdir : string
        Temporary directory path.

    """
    def __init__(self, dss_path, par_path, output='dssim.out', simnum=0):
        """Constructor to initialise a DSS environment.

        A new directory named *temp* will be created in the same directory as
        the parameters file.

        Parameters
        ----------
        dss_path : string
            Binary file full path.
        par_path : string or DssParam object
            Parameters file full path or DssParam instance.
        output : string, default 'dssim.out'
            Simulation output file full (NT) path.
        simnum : int, default 0
            Number of the next realization.

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
        self.outputdir, self.outputfile = ntpath.split(output)
        self.simnum = simnum

        self.tempdir = os.path.join(self.pardir, 'temp')
        if not os.path.isdir(self.tempdir):
            os.mkdir(self.tempdir)
        self.update_paths()

    def new(self):
        """Create a new directory, within the environment's temporary
        directory, and copy both binary and parameters files into it. Update
        the output and seed parameters.

        Returns
        -------
        new_exe : string
            Binary file path.
        new_par : string
            Parameters file path.

        """
        os.chdir(self.tempdir)
        new_dir = os.path.join(self.tempdir, str(len(self.envs) + 1))
        if not os.path.isdir(new_dir):
            os.mkdir(new_dir)

        new_exe = os.path.join(new_dir, self.exefile)
        new_par = os.path.join(new_dir, 'DSSim.PAR')  # TODO: old
        if not os.path.isfile(new_exe):
            shutil.copyfile(self.dss_path, new_exe)
        self.envs.append([new_dir, new_exe, new_par])

        # update path parameters and seed:
        if self.simnum > 1:
            outfile = ut.filename_indexing(self.outputfile, self.simnum)
        else:
            outfile = self.outputfile
        # update output file full path
#         if self.outputdir:
#             outdir = ntpath.abspath(self.outputdir)
#         else:
#             # try to guess the output directory
#             outdir = '..\\..\\..\\'

        outdir = '..\\..\\'

        keywords = ['output', 'seed']
        values = [ntpath.join(outdir, outfile),
                  self.par.seed + 2 * self.simnum]
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

    def update_paths(self):
        """Update the parameters related to file paths. Prepends '..\..\'.
        Necessary to call multiprocessing DSS launcher.

        """
        params = ['datapath', 'corrpath', 'secpath']

        for param in params:
            val = getattr(self.par, param)
            if not ntpath.isfile(val) and val != 'no file':
                # FIXME: not a pretty solution... code smell
                setattr(self.par, param, ntpath.join('..\\..\\',
                                                     ntpath.basename(val)))


def _normal(exe_path, par):
    """Launch normal version of DSS.

    Testing launching method with sarge.

    """
    import sarge

    os.chdir(os.path.dirname(exe_path))
    if os.name == 'posix':
        cmd = ['wine', os.path.basename(exe_path), par]
    else:
        cmd = [os.path.basename(exe_path), par]
    prog = sarge.Command(cmd, shell=False,
                        stdout=sarge.Capture(buffer_size=1))
    progrun = prog.run(input=sp.PIPE, async=True)

    return progrun


def _execute(command):
    """Testing a different method.

    """
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
    """Launch DSS binary.

    Parameters
    ----------
    dss_path : string
        Binary file full path.
    par_path : string
        Parameters file full path.
    dbg : string, optional
        Debug output file path. Write DSS console output to a file.
    print_status : boolean, default False
        Print execution status.

    """
    if print_status:
        print "Computing: {}".format(mp.current_process().name)

    if os.name == 'posix':
        env = 'wine '
    else:
        env = str()
    command = (env + os.path.basename(dss_path) + ' ' +
               os.path.basename(par_path))
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


def mp_exec(dss_path, par_path, output, simnum, totalsim=None, dbg=None,
            print_dss_status=False, cores=None, print_mp_status=False,
            purge=False):
    """Launch multiple threads of DSS at the same time, running at different
    cores.

    Parameters
    ----------
    dss_path : string
        Binary file full path.
    par_path : string or DssParam object
        Parameters file full path or DssParam instance.
    output : string
        Simulation output file full path.
    simnum : int
        Number of the next realization.
    totalsim : int, optional
        Total number of realizations.
    dbg : string, optional
        Debug output file path. Write DSS console output to a file.
    print_dss_status : boolean, default False
        Print DSS execution status.
    cores : int, optional
        Maximum number of cores to be used. If None, it will use all available
        cores.
    print_mp_status : boolean, default False
        Print threads execution status.
    purge : boolean, default False
        Remove all temporary files and directories created.

    """
    if not cores:
        cores = mp.cpu_count()
    if print_mp_status:
        print 'Running {} in {} cores'.format(os.path.basename(dss_path),
                                                cores)

    runs = list()
    dssenv = DssEnvironment(dss_path, par_path, output, simnum)

    for run in xrange(cores):
        if totalsim and simnum + run > totalsim:
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
    # _execute(dssexe)
    # exec_ssdir(dssexe, dsspar)
    # raw_input()
    # dssn.terminate()
    mp_exec(dssexe, dsspar, 'testinho.out', 1, print_dss_status=False,
            print_mp_status=True, totalsim=1)
    print 'done'
