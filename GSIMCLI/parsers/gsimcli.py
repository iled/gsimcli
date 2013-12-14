# -*- coding: utf-8 -*-
'''
Created on 5 de Dez de 2013

@author: julio
'''
from tools.parameters import ParametersFile


class GsimcliParam(ParametersFile):
    """GSIMCLI parameters

        --- DATA ---
        dss_par: path to the DSS parameters file (optional; if none, default
                 values will be used)
        data: path to the file containing the stations data
        data_header: header lines on the data file ('y'/'n')
        if not, specify
        name: data set name
        variables: variables name (e.g, 'x, y, z, var1, var2')
        
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
        par_set = 'GSIMCLI'
        text = ['data', 'st_order', 'detect_method', 'results',
                'dss_exe', 'krig_type', 'model']
        real_n = ['detect_prob', 'nugget', 'sill', 'ranges']
        boolean = ['data_header', 'detect_save', 'sim_purge']
        optional = ['dss_par', 'name', 'variables', 'st_user', 'skewness']
        int_n = ['x_column', 'y_column', 'time_column', 'station_column',
                 'climvariable_column', 'number_simulations',
                 'XX_nodes_number', 'XX_minimum', 'XX_spacing',
                 'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                 'ZZ_nodes_number', 'ZZ_minimum', 'ZZ_spacing',
                 'max_search_nodes', 'variogram_angles']
        order = ['dss_par', 'data', 'data_header', 'name', 'variables',
                 'st_order', 'st_user', 'detect_method', 'skewness',
                 'detect_prob', 'detect_save', 'sim_purge', 'results',
                 'dss_exe', 'number_simulations', 'krig_type', 'model',
                 'nugget', 'sill', 'ranges', 'angles', 'max_search_nodes',
                 'XX_nodes_number', 'XX_minimum', 'XX_spacing',
                 'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                 'ZZ_nodes_number', 'ZZ_minimum', 'ZZ_spacing']
        ParametersFile.__init__(self, sep=':', par_set=par_set, text=text,
                                int_n=int_n, real_n=real_n, boolean=boolean,
                                optional=optional, order=order)
        if par_path:
            self.load(par_path)


if __name__ == '__main__':
    ta = '/home/julio/Testes/gsimcli.par'
    ta2 = '/home/julio/Testes/gsimcli2.par'
    tb = '/Users/julio/Desktop/testes/gsimcli.par'
    tb2 = '/Users/julio/Desktop/testes/gsimcli2.par'
    bla = GsimcliParam(tb)
    # bla.template(tb)
    # bla.load(ta2)
    bla.update(['skewness'], ['kuku'], save=True, par_path=tb2)
    # bla.save(tb)
