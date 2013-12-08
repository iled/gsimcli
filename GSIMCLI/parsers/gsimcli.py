# -*- coding: utf-8 -*-
'''
Created on 5 de Dez de 2013

@author: julio
'''
from tools.parameters import ParametersFile


class GsimcliParam(ParametersFile):
    """GSIMCLI parameters

        dss_par: path to the DSS parameters file
        data: path to the file containing the stations data
        data_header: header lines on the data file ('y'/'n')
        if not, specify
        name: data set name
        variables: variables name (e.g, 'x, y, z, var1, var2')
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
        detect_save: save intermediary files ('y'/'n'), which are:
                    - candidates point-set
                    - references point-set
                    - local simulated values
                    - homogenized candidates
                    - dss parameters
                    - dss debug
        sim_purge: delete simulated maps ('y'/'n')
        results: path to the folder where results will be saved
        dss_exe: path to the DSS executable

    """
    def __init__(self, par_path=None):
        par_set = 'GSIMCLI'
        text = ['dss_par', 'data', 'st_order', 'detect_method', 'results',
                'dss_exe']
        real_n = ['detect_prob']
        boolean = ['data_header', 'detect_save', 'sim_purge']
        optional = ['name', 'variables', 'st_user', 'skewness']
        order = ['dss_par', 'dss_exe', 'results', 'data', 'data_header',
                 'name', 'variables', 'detect_method', 'detect_prob',
                 'skewness', 'st_order', 'st_user', 'detect_save', 'sim_purge']
        ParametersFile.__init__(self, sep=':', par_set=par_set, text=text,
                                real_n=real_n, boolean=boolean,
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
