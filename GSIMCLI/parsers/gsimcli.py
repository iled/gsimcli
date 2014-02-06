# -*- coding: utf-8 -*-
'''
Created on 5 de Dez de 2013

@author: julio
'''
import ntpath
import os

import parsers.dss as pdss
import tools.grid as gr
from tools.parameters import ParametersFile


class GsimcliParam(ParametersFile):
    """GSIMCLI parameters

        --- DATA ---
        data: path to the file containing the stations data
        no_data: number representing missing data (e.g., -999.9)
        data_header: header lines on the data file ('y'/'n')
        if not, specify
        name: data set name
        variables: variables name (e.g, 'x, y, time, station, var1, var2')
        The following variables are mandatory, here or in the header lines of
        the data file:
        - 'x' coordinate X
        - 'y' coordinate Y
        - 'time' unit of time
        - 'station' stations IDs
        - 'clim' climatic variable to homogenize

        --- DETECTION ---
        st_order: method for setting candidates order:
                - 'random' all stations are randomly sorted;
                - 'sorted' sorts all stations in ascending or descending order;
                - 'variance' sorts all stations by greater or lower variance;
                - 'network deviation' sorts all stations in ascending  or
                descending order according to the difference between the
                station average and the network average;
                - 'user' the user specifies which stations and their order.
        ascending: sort in ascending order ('y'/'n')
        md_last: put missing data at the end of sorted stations ('y'/'n')
        st_user: stations IDs in order if st_order == 'user' (e.g., '3, 10, 2')
        detect_method: detection method (comparison between upper and lower
                       percentiles and the simulated values):
                        - 'mean' compares with the mean
                        - 'median' compares with the median
                        - 'skewness' use the sample skewness to decide whether
                                     it compares with the mean or the median
        skewness: samples skewness threshold, used if detecm == 'skewness'
        detect_prob: probability to build an interval centered in the local pdf

        --- RESULTS ---
        detect_save: save intermediary files ('y'/'n'), which are:
                    - candidates point-set
                    - references point-set
                    - local simulated values
                    - homogenized candidates
                    - dss parameters
                    - dss debug
        sim_purge: delete simulated maps ('y'/'n')
        results: path to the folder where results will be saved

        --- DSS ---
        dss_par: path to the DSS parameters file (optional; if none, default
                 values will be used)
        dss_exe: path to the DSS executable
        number_simulations: number of simulations
        krig_type: krigging type (OK, SK)

        --- DSS: variogram ---
        model: model type (S = spherical, E = exponential, G = gaussian)
        nugget: nugget effect (C0) in normalised variance
        sill: sill in normalised variance
        ranges: ranges (dir. 1, dir. 2, dir. 3), in the data scale
        angles: direction angles

        --- DSS: grid ---
        max_search_nodes: maximum number of nodes to be found
        XX_nodes_number: number of nodes in x-axis
        XX_minimum: minimum coordinate in x-axis
        XX_spacing: distance between nodes (or node size) in x-axis
        YY_nodes_number: number of nodes in y-axis
        YY_minimum: minimum coordinate in y-axis
        YY_spacing: distance between nodes (or node size) in y-axis
        ZZ_nodes_number: number of nodes in z-axis
        ZZ_minimum: minimum coordinate in z-axis
        ZZ_spacing: distance between nodes (or node size) in z-axis

    """
    def __init__(self, par_path=None):
        """Constructor. Include wrapper for the DSS parameters.

        TODO: - for now it just supports one structure in the variogram
              - consider every dss parameters as optional?
        """
        par_set = 'GSIMCLI'
        text = ['data', 'st_order', 'detect_method', 'results', 'dss_exe']
        real_n = ['detect_prob', 'no_data']
        boolean = ['data_header', 'detect_save', 'sim_purge']
        opt_text = ['dss_par', 'name', 'variables', 'krig_type', 'model']
        opt_int = ['st_user', 'number_simulations', 'max_search_nodes',
                   'angles', 'XX_nodes_number', 'XX_minimum', 'XX_spacing',
                   'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                   'ZZ_nodes_number', 'ZZ_minimum', 'ZZ_spacing']
        opt_real = ['skewness', 'nugget', 'sill', 'ranges']
        opt_boolean = ['ascending', 'md_last']
        order = ['data', 'no_data', 'data_header', 'name',
                 'variables', 'st_order', 'ascending', 'md_last', 'st_user',
                 'detect_method', 'skewness', 'detect_prob', 'detect_save',
                 'sim_purge', 'results', 'dss_par', 'dss_exe',
                 'number_simulations', 'krig_type', 'model', 'nugget', 'sill',
                 'ranges', 'angles', 'max_search_nodes',
                 'XX_nodes_number', 'XX_minimum', 'XX_spacing',
                 'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                 'ZZ_nodes_number', 'ZZ_minimum', 'ZZ_spacing']

        ParametersFile.__init__(self, field_sep=':', value_sep=',',
                                par_set=par_set, text=text, real_n=real_n,
                                boolean=boolean, opt_text=opt_text,
                                opt_int=opt_int, opt_real=opt_real,
                                opt_boolean=opt_boolean, order=order)
        if par_path:
            self.load(par_path)

    def load(self, par_path):
        ParametersFile.load(self, par_path)
        if not self.data_header and (not hasattr(self, 'variables') or
                                     not hasattr(self, 'name')):
            raise ValueError('Missing header in the data file or \'variables\''
                             'parameter')

    def update_dsspar(self, save=False, dsspar_path=None):
        """Update the DSS parameters file according to the set of parameters
        given in the GSIMCLI parameters file.

        """
        if hasattr(self, 'dss_par'):
            dsspar = pdss.DssParam.load_old(self.dss_par)  # TODO: old arg
        else:
            dsspar = pdss.DssParam()

        dsspar.path = os.path.join(os.path.dirname(self.path), 'DSSim.par')
        pset = gr.PointSet(psetpath=self.data, header=self.data_header)

        if hasattr(self, 'name'):
            name = self.name
        else:
            self.name = pset.name
            name = pset.name
        if hasattr(self, 'variables'):
            varnames = self.variables  # map(str.strip, self.variables.split(','))
        else:
            self.variables = pset.varnames
            varnames = pset.varnames

        columns_set = [varnames.index('x') + 1, varnames.index('y') + 1,
                      varnames.index('time') + 1, varnames.index('clim') +
                      1, 0, 0]

        gsc_grid = ['XX_nodes_number', 'XX_minimum', 'XX_spacing',
                    'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                    'ZZ_nodes_number', 'ZZ_minimum', 'ZZ_spacing']
        dss_grid = [dsspar.xx[0], dsspar.xx[1], dsspar.xx[2],
                    dsspar.yy[0], dsspar.yy[1], dsspar.yy[2],
                    dsspar.zz[0], dsspar.zz[1], dsspar.zz[2]]
        grid_specs = list()
        for i in xrange(len(dss_grid)):
            if hasattr(self, gsc_grid[i]):
                grid_specs.append(getattr(self, gsc_grid[i]))
            else:
                grid_specs.append(dss_grid[i])

        radius = [grid_specs[0] * grid_specs[2], grid_specs[3] * grid_specs[5],
                  grid_specs[6] * grid_specs[8]]

        keywords = ['datapath', 'columns_set', 'nd', 'output', 'srchradius',
                    'xx', 'yy', 'zz']
        values = [ntpath.normcase(self.data), columns_set, self.no_data,
                  (name + '.prn').replace(' ', '_'), radius,
                  [grid_specs[0], grid_specs[1], grid_specs[2]],
                  [grid_specs[3], grid_specs[4], grid_specs[5]],
                  [grid_specs[6], grid_specs[7], grid_specs[8]]]

        if hasattr(self, 'krig_type'):
            if self.krig_type.lower() == 'ok':
                krig = 0
            elif self.krig_type.lower() == 'sk':
                krig = 1  # TODO: faltam outros tipos
            keywords.append('krig')
            values.append([krig, 0])
        if hasattr(self, 'max_search_nodes'):
            keywords.append('nsamples')
            values.append([1, self.max_search_nodes])
        if hasattr(self, 'nugget'):
            keywords.append('nstruct')
            values.append([dsspar.nstruct[0], self.nugget])
        if hasattr(self, 'ranges'):
            keywords.append('ranges')
            values.append([self.ranges])
        if hasattr(self, 'model'):
            if self.model.lower() == 's':
                model = 1
            elif self.model.lower() == 'e':
                model = 2
            elif self.model.lower() == 'g':
                model = 3
        else:
            model = dsspar.struct[0]
        if hasattr(self, 'sill'):
            sill = self.sill
        else:
            sill = dsspar.struct[1]
        if hasattr(self, 'angles'):
            angles = self.angles
        else:
            angles = dsspar.struct[2:]

        keywords.append('struct')
        values.append([[model, sill] + angles])

        other_keys = ['nsim', 'srchangles', 'maxsim']
        other_values = ['number_simulations', 'angles', 'max_search_nodes']
        for i in xrange(len(other_keys)):
            if hasattr(self, other_values[i]):
                keywords.append(other_keys[i])
                values.append(getattr(self, other_values[i]))

        dsspar.update(keywords, values)
        dsspar.data2update(self.data, self.no_data, varnames.index('clim'),
                           self.data_header, save, dsspar_path)
        return dsspar


if __name__ == '__main__':
    # ta = '/home/julio/Testes/gsimcli.par'
    ta2 = '/home/julio/Testes/gsimcli2.par'
    # tb = '/Users/julio/Desktop/testes/gsimcli.par'
    # tb2 = '/Users/julio/Desktop/testes/gsimcli2.par'
    bla = GsimcliParam()
    bla.template(ta2)
    # bla.load(ta2)
    # bla.update(['skewness'], ['kuku'], save=True, par_path=tb2)
    # bla.save(tb)
