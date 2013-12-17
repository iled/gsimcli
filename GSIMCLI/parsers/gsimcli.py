# -*- coding: utf-8 -*-
'''
Created on 5 de Dez de 2013

@author: julio
'''
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
        The following variables are mandatory, here or in the header line of
        the data file:
        - 'x' coordinate X
        - 'y' coordinate Y
        - 'time' unit of time
        - 'station' stations IDs
        - 'clim' climatic variable to homogenize
        
        --- DETECTION ---
        st_order: method for setting candidates order:
                - 'random' all stations are randomly sorted;
                - 'sorted' sorts all stations in ascending order;
                - 'variance' sorts all stations by greater variance;
                - 'user' the user specifies which stations and their order.
        st_user: stations IDs in order if storder == 'user' (e.g., '3 10 1 2')
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
        krig_type: krigging type
        
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
        text = ['data', 'st_order', 'detect_method', 'results',
                'dss_exe', 'krig_type', 'model']
        real_n = ['detect_prob', 'nugget', 'sill', 'ranges', 'no_data']
        boolean = ['data_header', 'detect_save', 'sim_purge']
        optional = ['dss_par', 'name', 'variables', 'st_user', 'skewness']
        int_n = ['number_simulations', 'max_search_nodes', 'angles',
                 'XX_nodes_number', 'XX_minimum', 'XX_spacing',
                 'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                 'ZZ_nodes_number', 'ZZ_minimum', 'ZZ_spacing']
        order = ['data', 'no_data', 'data_header', 'name',
                 'variables', 'st_order', 'st_user', 'detect_method',
                 'skewness', 'detect_prob', 'detect_save', 'sim_purge',
                 'results', 'dss_par', 'dss_exe', 'number_simulations',
                 'krig_type', 'model', 'nugget', 'sill', 'ranges', 'angles',
                 'max_search_nodes',
                 'XX_nodes_number', 'XX_minimum', 'XX_spacing',
                 'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                 'ZZ_nodes_number', 'ZZ_minimum', 'ZZ_spacing']
        ParametersFile.__init__(self, sep=':', par_set=par_set, text=text,
                                int_n=int_n, real_n=real_n, boolean=boolean,
                                optional=optional, order=order)

        if par_path:
            self.load(par_path)
    
    def load(self, par_path):
        ParametersFile.load(self, par_path)
        if not hasattr(self, 'variables') and self.data_header.lower == 'n':
            raise ValueError('Missing header in the data file or \'variables\''
                             'parameter')

    def update_dsspar(self, save=False, par_path=None):
        """Update the DSS parameters file according to the set of parameters
        given in the GSIMCLI parameters file.
    
        """
        if hasattr(self, 'dss_par'):
            dsspar = pdss.DssParam.load_old(self.dss_par)  # TODO: old arg
        else:
            dsspar = pdss.DssParam()

        dsspar.path = os.path.join(os.path.dirname(self.path), 'DSSim.PAR')

        if self.data_header.lower() == 'y':
            header = True
        else:
            header = False
            
        if hasattr(self, 'name') and hasattr(self, 'variables'):
            name = self.name
            varnames = self.variables.split()
        elif header:
            pset = gr.PointSet(psetpath=self.data, header=True)
            name = pset.name
            varnames = pset.varnames
        else:
            raise ValueError  # TODO: just to double check, then delete
        column_set = [varnames.index('x'), varnames.index('y'),
                      varnames.index('time'), varnames.index('clim'), 0, 0]
        radius = [self.XX_nodes_number * self.XX_spacing,
                  self.YY_nodes_number * self.YY_spacing,
                  self.ZZ_nodes_number * self.ZZ_spacing]
                  
        if self.model.lower().strip() == 's':
            model = 1
        elif self.model.lower().strip() == 'e':
            model = 2
        elif self.model.lower().strip() == 'g':
            model = 3

        keywords = ['column_set', 'output', 'nsim', 'xx', 'yy', 'zz', 'nd',
                    'nsamples', 'maxsim', 'srchradius', 'srchangles', 'krig',
                    'nstruct', 'struct', 'ranges', 'datapath']
        values = [column_set, name + '.prn', self.number_simulations,
                  [self.XX_nodes_number, self.XX_minimum, self.XX_spacing],
                  [self.YY_nodes_number, self.YY_minimum, self.YY_spacing],
                  [self.ZZ_nodes_number, self.ZZ_minimum, self.ZZ_spacing],
                  self.no_data, [1, self.max_search_nodes],
                  self.max_search_nodes, radius, self.angles,
                  [self.krig_type, 0], [dsspar.nstruct[0], self.nugget],
                  [model, self.sill, self.angles], self.ranges, self.data]

        dsspar.update(keywords, values)
        dsspar.data2update(self.data, self.no_data, varnames.index('clim'),
                           header, save, par_path)
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
