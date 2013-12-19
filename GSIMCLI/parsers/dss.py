# -*- coding: utf-8 -*-
'''
Created on 07/10/2013

@author: jcaineta
'''

import ntpath
import os

import numpy as np
import tools.grid as gr


class DssParam:
    """DSS parameters

        datapath: path and data filename
        columns: number of columns
        columns_set: columns for X, Y, Z, Var, Weight, Sec. var
        trimming: trimming limits, min and max
        transflag: transformation file (1/0 - yes/no)
        transfile: transformation path and filename
        tails: data limits (distribution tails)
        lowert: lower tail (interpolation type, min)
        uppert: upper tail (interpolation type, min)
        debuglvl: debugging level (1/2/3)
        debugfile: debugging path and filename
        output: output path and filename
        nsim: number of realizations
        bias: local bias simulation correction, mean (0/1), variance (0/1)
        xx: XX: number of nodes, min., spacing
        yy: YY: number of nodes, min., spacing
        zz: ZZ: number of nodes, min., spacing
        nd: value for unsimulated nodes
        seed: seed
        nsamples: number of search samples (min, max)
        maxsim: max. number of previously simulated nodes
        strategy: search strategy (0 = two-part search, 1 = data nodes)
        simset: grid search method (0 = spiral search, 1 = multiple search),
                number of multiple grids
        octant: samples number per octant (0 = no octant)
        srchradius: search radius (dir. 1, dir. 2., dir. 3), in the data scale
        srchangles: search anisotropy angles
        krig: kriging type, global correlation index if = 4
        corrpath: path and filename of local correlation indexes
        secpath: path and filename of secondary information
        seccol: number of columns and column of secondary variable
        nstruct: number of structures, nugget effect (C0) (normalised variance)
        struct: model type (1 = spherical, 2 = exponential, 3 = gaussian),
                sill (normalised variance), direction angles
        ranges: ranges (dir. 1, dir. 2, dir. 3), in the data scale

    """
    def __init__(self, parpath=None):
        """Initialise with the default parameters for GSIMCLI.

        """
        self.path = str()
        self.datapath = str()
        self.columns = 4
        self.columns_set = [1, 2, 3, 4, 0, 0]
        self.trimming = [0, 0]
        self.transflag = 1
        self.transfile = 'cluster.trn'
        self.tails = [0, 0]
        self.lowert = [1, 0]
        self.uppert = [1, 0]
        self.debuglvl = 1
        self.debugfile = 'dss.dbg'
        self.output = 'dss.out'
        self.nsim = 1
        self.bias = [10, 1, 1]
        self.xx = [1, 1, 1]
        self.yy = [1, 1, 1]
        self.zz = [1, 1, 1]
        self.nd = -999.9
        self.seed = 69069
        self.nsamples = [1, 16]
        self.maxsim = 16
        self.strategy = 1
        self.simset = [0, 1]
        self.octant = 0
        self.srchradius = [1, 1, 1]
        self.srchangles = [0, 0, 0]
        self.krig = [0, 0]
        self.corrpath = 'no file'
        self.secpath = 'no file'
        self.seccol = [0, 0]
        self.nstruct = [1, 0]
        self.struct = [1, 1, 0, 0, 0]
        self.ranges = [1, 1, 1]
        # for old version
        self.smoothflag = 0
        self.smoothfile = 'no file'
        self.smoothcols = [1, 2]
        self.imask = 0
        if parpath:
            self.load_old(parpath)

    def load(self, par_path):
        """Reads the parameters file of DSS parallel version (Nunes, R.)"""
        self.path = par_path
        with open(par_path, 'r') as f:
            par = f.readlines()
        self.datapath = par[4].strip()
        self.columns = int(par[5])
        self.columns_set = map(int, par[6].split())
        self.trimming = map(float, par[7].split())
        self.transflag = int(par[8])
        self.transfile = par[9].strip()
        self.tails = map(float, par[10].split())
        self.lowert = map(float, par[11].split())
        self.uppert = map(float, par[12].split())
        self.debuglvl = int(par[13])
        self.debugfile = par[14].strip()
        self.output = par[15].strip()
        self.nsim = int(par[16])
        self.bias = map(int, par[17].split())  # TODO: check bias[0]
        self.xx = map(int, par[18].split())
        self.yy = map(int, par[19].split())
        self.zz = map(int, par[20].split())
        self.nd = float(par[21])
        self.seed = int(par[22])
        self.nsamples = map(int, par[23].split())
        self.maxsim = int(par[24])
        self.strategy = int(par[25])
        self.simset = map(int, par[26].split())
        self.octant = int(par[27])
        self.srchradius = map(int, par[28].split())
        self.srchangles = map(int, par[29].split())
        self.krig = map(int, par[30].split())  # TODO: check krig
        self.corrpath = par[31].strip()
        self.secpath = par[32].strip()
        self.seccol = map(int, par[33].split())
        self.nstruct = par[34].split()  # (int, float)
        self.struct = [par[35].split()]
        self.ranges = [par[36].split()]
        for i in xrange(1, int(self.nstruct[0])):
            self.struct.append(par[35 + 2 * i].split())
            self.ranges.append(par[36 + 2 * i].split())

    def save(self, par_path=None):
        """Writes the parameters file of DSS parallel version (Nunes, R.)"""
        if not par_path:
            par_path = self.path
        else:
            self.path = par_path
        par = open(par_path, 'w')
        par_header = ['Direct Sequential Simulation',
                      '****************************',
                      'for Parallel version (Nunes, R., 2010)',
                      'START OF PARAMETERS:']
        par.writelines('\n'.join(par_header) + '\n')
        par.write(self.datapath + '\n')
        par.write(str(self.columns) + '\n')
        par.write('    '.join(map(str, self.columns_set)) + '\n')
        par.write('    '.join(map(str, self.trimming)) + '\n')
        par.write(str(self.transflag) + '\n')
        par.write(self.transfile + '\n')
        par.write('    '.join(map(str, self.tails)) + '\n')
        par.write('    '.join(map(str, self.lowert)) + '\n')
        par.write('    '.join(map(str, self.uppert)) + '\n')
        par.write(str(self.debuglvl) + '\n')
        par.write(self.debugfile + '\n')
        par.write(self.output + '\n')
        par.write(str(self.nsim) + '\n')
        par.write('    '.join(map(str, self.bias)) + '\n')
        par.write('    '.join(map(str, self.xx)) + '\n')
        par.write('    '.join(map(str, self.yy)) + '\n')
        par.write('    '.join(map(str, self.zz)) + '\n')
        par.write(str(self.nd) + '\n')
        par.write(str(self.seed) + '\n')
        par.write('    '.join(map(str, self.nsamples)) + '\n')
        par.write(str(self.maxsim) + '\n')
        par.write(str(self.strategy) + '\n')
        par.write('    '.join(map(str, self.simset)) + '\n')
        par.write(str(self.octant) + '\n')
        par.write('    '.join(map(str, self.srchradius)) + '\n')
        par.write('    '.join(map(str, self.srchangles)) + '\n')
        par.write('    '.join(map(str, self.krig)) + '\n')
        par.write(self.corrpath + '\n')
        par.write(self.secpath + '\n')
        par.write('    '.join(map(str, self.seccol)) + '\n')
        par.write('    '.join(self.nstruct) + '\n')
        for i in xrange(int(self.nstruct[0])):
            par.write('    '.join(self.struct[i]) + '\n')
            par.write('    '.join(self.ranges[i]) + '\n')
        par.close()

    def load_old(self, par_path):
        """Reads the parameters file of DSS old version"""
        self.path = par_path
        with open(par_path, 'r') as f:
            par = f.readlines()
        self.datapath = par[4].strip()
        self.columns = int(par[5])
        self.columns_set = map(int, par[6].split())
        self.trimming = map(float, par[7].split())
        self.transflag = int(par[8])
        self.transfile = par[9].strip()
        self.smoothflag = int(par[10])
        self.smoothfile = par[11].strip()
        self.smoothcols = map(int, par[12].split())
        self.tails = map(float, par[13].split())
        self.lowert = [int(par[14].split()[0]), float(par[14].split()[1])]
        self.uppert = [int(par[15].split()[0]), float(par[15].split()[1])]
        self.debuglvl = int(par[16])
        self.debugfile = par[17].strip()
        self.output = par[18].strip()
        self.nsim = int(par[19])
        self.bias = map(int, par[20].split())  # TODO: check bias[0]
        self.xx = map(int, par[21].split())
        self.yy = map(int, par[22].split())
        self.zz = map(int, par[23].split())
        self.nd = float(par[24])
        self.imask = int(par[25])
        self.seed = int(par[26])
        self.nsamples = map(int, par[27].split())
        self.maxsim = int(par[28])
        self.strategy = int(par[29])
        self.simset = map(int, par[30].split())
        self.octant = int(par[31])
        self.srchradius = map(int, par[32].split())
        self.srchangles = map(int, par[33].split())
        # TODO: check krig; + 7.42
        self.krig = [int(par[34].split()[0]), int(par[34].split()[1]),
                     float(par[34].split()[2])]
        self.corrpath = par[35].strip()
        self.secpath = par[36].strip()
        self.seccol = map(int, par[37].split())
        self.nstruct = par[38].split()  # (int, float)
        self.struct = [par[39].split()]
        self.ranges = [par[40].split()]
        for i in xrange(1, int(self.nstruct[0])):
            self.struct.append(par[39 + 2 * i].split())
            self.ranges.append(par[40 + 2 * i].split())

    def save_old(self, par_path=None):
        """Writes the parameters file of DSS old version"""
        if not par_path:
            par_path = self.path
        else:
            self.path = par_path
        par = open(par_path, 'w')
        par_header = ['Direct Sequential Simulation',
                      '****************************',
                      'for old version (~2001)',
                      'START OF PARAMETERS:']
        par.writelines('\n'.join(par_header) + '\n')
        par.write(self.datapath + '\n')
        par.write(str(self.columns) + '\n')
        par.write('    '.join(map(str, self.columns_set)) + '\n')
        par.write('    '.join(map(str, self.trimming)) + '\n')
        par.write(str(self.transflag) + '\n')
        par.write(self.transfile + '\n')
        par.write(str(self.smoothflag) + '\n')
        par.write(self.smoothfile + '\n')
        par.write('    '.join(map(str, self.smoothcols)) + '\n')
        par.write('    '.join(map(str, self.tails)) + '\n')
        par.write('    '.join(map(str, self.lowert)) + '\n')
        par.write('    '.join(map(str, self.uppert)) + '\n')
        par.write(str(self.debuglvl) + '\n')
        par.write(self.debugfile + '\n')
        par.write(self.output + '\n')
        par.write(str(self.nsim) + '\n')
        par.write('    '.join(map(str, self.bias)) + '\n')
        par.write('    '.join(map(str, self.xx)) + '\n')
        par.write('    '.join(map(str, self.yy)) + '\n')
        par.write('    '.join(map(str, self.zz)) + '\n')
        par.write(str(self.nd) + '\n')
        par.write(str(self.imask) + '\n')
        par.write(str(self.seed) + '\n')
        par.write('    '.join(map(str, self.nsamples)) + '\n')
        par.write(str(self.maxsim) + '\n')
        par.write(str(self.strategy) + '\n')
        par.write('    '.join(map(str, self.simset)) + '\n')
        par.write(str(self.octant) + '\n')
        par.write('    '.join(map(str, self.srchradius)) + '\n')
        par.write('    '.join(map(str, self.srchangles)) + '\n')
        if len(self.krig) == 2:
            self.krig.append(7.42)
        par.write('    '.join(map(str, self.krig)) + '\n')
        par.write(self.corrpath + '\n')
        par.write(self.secpath + '\n')
        par.write('    '.join(map(str, self.seccol)) + '\n')
        par.write('    '.join(map(str, self.nstruct)) + '\n')
        for i in xrange(int(self.nstruct[0])):
            par.write('    '.join(map(str, self.struct[i])) + '\n')
            par.write('    '.join(map(str, self.ranges[i])) + '\n')
        par.close()

    def update(self, keywords, values, save=False, par_path=None):
        """Updates a list of keywords with the corresponding values.
        """
        if not par_path:
            par_path = self.path
        for i, keyword in enumerate(keywords):
            if hasattr(self, keyword):
                setattr(self, keyword, values[i])
        if save:
            self.save_old(par_path)  # TODO: old manager

    def data2update(self, dataset, no_data=-999.9, varcol=-1, header=True,
                    save=True, par_path=None):
        """Try to update the parameters according to a data set in the PointSet
        format.

        """
        if isinstance(dataset, gr.PointSet):
            pset = dataset
        else:
            pset = gr.PointSet()
            pset.load(dataset, no_data, header)

        keywords = ['datapath', 'columns', 'trimming', 'tails', 'lowert',
                    'uppert', 'nd']

        hdpath = ntpath.normcase(pset.path)
        ncols = pset.values.shape[1]
        psetvalues = pset.values.iloc[:, varcol].replace(no_data, np.nan)
        datamin = psetvalues.min()
        datamax = psetvalues.max()
        values = [hdpath, ncols, [datamin, datamax], [datamin, datamax],
                  [1, datamin], [1, datamax], pset.nodata]
        self.update(keywords, values, save, par_path)

    def ask_update_default(self):
        """Asks to update or keep existing values.
        """
        arg = raw_input('Hard-data path/file [{}]: '.format(self.datapath.
                                                           strip()))
        if arg:
            self.datapath = arg

        arg = raw_input('Number of columns [{}]: '.format(self.columns))
        if arg:
            self.columns = arg

        arg = raw_input('Columns for X, Y, Z, Var, Weight, Sec. var [{}]: '
                        .format(self.columns_set))
        if arg:
            self.columns_set = arg.split()

        arg = raw_input('Trimming limits, min and max [{}]: '.
                        format(self.trimming))
        if arg:
            self.trimming = arg.split()

        arg = raw_input('Transformation file (1/0 - yes/no) [{}]: '.
                        format(self.transflag))
        if arg:
            self.transflag = arg

        if self.transflag:
            arg = raw_input('Transformation path/filename [{}]: '
                            .format(self.transfile))
            if arg:
                self.transfile = arg
        else:
            self.transfile = 'no file'

        arg = raw_input('Data limits (distribution tails) [{}]: '
                        .format(self.tails))
        if arg:
            self.tails = arg.split()

        arg = raw_input('Lower tail (interpolation type, min.) [{}]: '
                        .format(self.lowert))
        if arg:
            self.lowert = arg.split()

        arg = raw_input('Upper tail (interpolation type, min.) [{}]: '
                        .format(self.uppert))
        if arg:
            self.uppert = arg.split()

        arg = raw_input('Debugging level (1/2/3) [{}]: '.format(self.debuglvl))
        if arg:
            self.dbglvl = arg

        arg = raw_input('Debugging path/filename [{}]: '.format(self.debugfile.
                                                               strip()))
        if arg:
            self.debugfile = arg

        arg = raw_input('Output path/filename [{}]: '.format(self.output.
                                                            strip()))
        if arg:
            self.output = arg

        arg = raw_input('Number of realizations [{}]: '.format(self.nsim))
        if arg:
            self.nsim = arg

        arg = raw_input('Local bias simulation correction, for mean (0/1), for'
                        'variance (0/1) [{}]: '.format(self.bias))
        if arg:
            self.bias = arg

        arg = raw_input('XX: number of nodes, min., spacing [{}]: '
                        .format(self.xx))
        if arg:
            self.xx = arg.split()

        arg = raw_input('YY: number of nodes, min., spacing [{}]: '
                        .format(self.yy))
        if arg:
            self.yy = arg.split()

        arg = raw_input('ZZ: number of nodes, min., spacing [{}]: '
                        .format(self.zz))
        if arg:
            self.zz = arg.split()

        arg = raw_input('Value for unsimulated nodes [{}]: '.format(self.nd))
        if arg:
            self.nd = arg

        arg = raw_input('Seed for pseudo-random numbers [{}]: '
                        .format(self.seed))
        if arg:
            self.seed = arg

        arg = raw_input('Number of search samples (min, max) [{}]: '
                        .format(self.nsamples))
        if arg:
            self.nsamples = arg.split()

        arg = raw_input('Max. number of previously simulated nodes [{}]: '
                        .format(self.maxsim))
        if arg:
            self.maxsim = arg

        arg = raw_input('Search strategy (0 = two-part search, 1 = data nodes)'
                        ' [{}]: '.format(self.strategy))
        if arg:
            self.strategy = arg

        arg = raw_input('Two-step simulation (0/1), number of multiple grids'
                        ' [{}]: '.format(self.simset))
        if arg:
            self.simset = arg.split()

        arg = raw_input('Samples number per octant (0 = no octant) [{}]: '
                        .format(self.octant))
        if arg:
            self.octant = arg.split()

        arg = raw_input('Search radius (dir. 1, dir. 2, dir. 3), in the data '
                        'scale [{}]: '.format(self.srchradius))
        if arg:
            self.srchradius = arg.split()

        arg = raw_input('Search anisotropy angles, in the data scale [{}]: '
                        .format(self.srchangles))
        if arg:
            self.srchangles = arg.split()

        arg = raw_input('Kriging type, global correlation index if = 4 [{}]: '
                        .format(self.krig))
        if arg:
            self.krig = arg.split()

        # TODO: detectar kriging type
        arg = raw_input('Local correlation indexes path/filename [{}]: '
                        .format(self.corrpath))
        if arg:
            self.corrpath = arg

        arg = raw_input('Secondary information path/filename [{}]: '
                        .format(self.secpath))
        if arg:
            self.secpath = arg

        arg = raw_input('Number of columns in secondary file, column of second'
                        'ary variable [{}]: '.format(self.seccol))
        if arg:
            self.seccol = arg.split()

        arg = raw_input('Number of variogram structures, nugget effect (C0) '
                        '(normalised variance) [{}]: '.format(self.nstruct))
        if arg:
            self.nstruct = arg.split()
            self.struct = self.struct[:int(self.nstruct[0])]
            self.ranges = self.ranges[:int(self.nstruct[0])]

        arg = raw_input('Structure 1: Model type, sill (normalised variance), '
                        'direction angles [{}]: '.format(self.struct))
        if arg:
            self.struct = [arg.split()]

        arg = raw_input('Structure 1: Ranges (dir.1, dir. 2, dir. 3), in the '
                        'data scale [{}]: '.format(self.ranges))
        if arg:
            self.ranges = [arg.split()]

        for i in xrange(1, int(self.nstruct[0])):
            arg = raw_input('Structure {}: Model type, sill (normalised '
                            'variance), direction angles [{}]: '
                            .format(i, self.struct))
            if arg:
                self.struct.append(arg.split())

            arg = raw_input('Structure {}: Ranges (dir.1, dir. 2, dir. 3), in '
                            'the data scale [{}]: '.format(i, self.ranges))
            if arg:
                self.ranges.append(arg.split())

    def ask_new(self):
        """Asks to insert new values.
        """
        self.datapath = raw_input('Hard-data path/file: ').strip()
        self.column = int(raw_input('Number of columns: '))
        self.columns_set = map(int, raw_input('Columns for X, Y, Z, Var, '
                                                'Weight, Sec. var: ').split())
        self.trimming = map(float, raw_input('Trimming limits, min and max: ')
                            .split())
        self.transflag = int(raw_input('Transformation file (1/0 - yes/no): '))
        if self.transflag:
            self.transfile = raw_input('Transformation path/filename:'
                                       ' ').strip()
        else:
            self.transfile = 'no file'
        self.tails = map(float, raw_input('Data limits (distribution tails): ')
                         .split())
        self.lowert = map(float, raw_input('Lower tail (interpolation type, '
                                           'min.): ').split())
        self.uppert = map(float, raw_input('Upper tail (interpolation type, '
                                           'min.): ').split())
        self.dbglvl = int(raw_input('Debugging level (1/2/3): '))
        self.debugfile = raw_input('Debugging path/filename: ').strip()
        self.output = raw_input('Output path/filename: ').strip()
        self.nsim = int(raw_input('Number of realizations: '))
        self.bias = map(int, raw_input('Local bias simulation correction, for '
                                       'mean (0/1), for variance (0/1): ')
                        .split())
        self.xx = map(int, raw_input('XX: number of nodes, min., spacing: ')
                      .split())
        self.yy = map(int, raw_input('YY: number of nodes, min., spacing: ')
                      .split())
        self.zz = map(int, raw_input('ZZ: number of nodes, min., spacing: ')
                      .split())
        self.nd = float(raw_input('Value for unsimulated nodes: '))
        self.seed = int(raw_input('Seed for pseudo-random numbers: '))
        self.nsamples = map(int, raw_input('Number of search samples '
                                           '(min, max): ').split())
        self.maxsim = int(raw_input('Max. number of previously simulated '
                                    'nodes: '))
        self.strategy = int(raw_input('Search strategy (0 = two-part search, '
                                      '1 = data nodes): '))
        self.simset = map(int, raw_input('Two-step simulation (0/1), number of'
                                         ' multiple grids: ').split())
        self.octant = int(raw_input('Samples number per octant '
                                    '(0 = no octant): '))
        self.srchradius = map(int, raw_input('Search radius (dir. 1, dir. 2, '
                                             'dir. 3) in the data scale: ')
                              .split())
        self.srchangles = map(int, raw_input('Search anisotropy angles: ')
                              .split())
        self.krig = map(int, raw_input('Kriging type, global correlation index'
                                      ' if = 4: ').split())
        self.corrpath = raw_input('Local correlation indexes path/filename'
                                  ': ').strip()
        self.secpath = raw_input('Secondary information path/filename:'
                                 ' ').strip()
        self.seccol = map(int, raw_input('Number of columns in secondary file,'
                                         ' column of secondary variable: ')
                          .split())
        self.nstruct = raw_input('Number of variogram structures, nugget '
                                 'effect (C0) (normalised variance): ').split()
        self.struct = [raw_input('Structure 1: Model type, sill (normalised '
                                 'variance), direction angles: ').split()]
        self.ranges = [raw_input('Structure 1: Ranges (dir.1, dir. 2, dir. 3),'
                                 ' in the data scale: ').split()]
        for i in xrange(1, int(self.nstruct[0])):
            self.struct.append(raw_input('Structure {}: Model type, sill '
                                         '(normalised variance), direction '
                                         'angles: '.format(i)).split())
            self.ranges.append(raw_input('Structure {}: Ranges (dir.1, dir. 2,'
                                          ' dir. 3), in the data scale: '
                                          .format(i)).split())


if __name__ == '__main__':
    parfile = '/home/julio/Testes/DSSim.par'
    newpar = '/home/julio/Testes/teste_update.par'
    dataset = '/home/julio/Testes/snirh.prn'
    pars = DssParam()
    pars.load_old(parfile)
    # pars.update(['output'], ['yeah.out'])
    # pars.ask_new()
    pars.data2update(dataset, -999.9, False)
    pars.save(newpar)
    print 'done'
