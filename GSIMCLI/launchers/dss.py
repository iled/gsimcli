# -*- coding: utf-8 -*-
'''
Created on 04/10/2013

@author: jcaineta
'''

# import sarge

import datetime
import os
import sys

import subprocess as sp

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


def exec_ssdir(dss_path, par_path, dbg=None):
    # print 'Running {}...'.format(os.path.basename(dss_path))
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
        # """
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
        # """
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

if __name__ == '__main__':
    dssexe = '/home/julio/Testes/ssdir.exe'
    # dsspar = '/home/julio/Transferências/test/snirh.par'
    dsspar = '/home/julio/Testes/snirh50/dss_par_st3.par'
    # print 'Running DSS...'
    # dssn = normal(dssexe, dsspar)
    # execute(dssexe)
    exec_ssdir(dssexe, dsspar)
    # raw_input()
    # dssn.terminate()
    print 'done'
