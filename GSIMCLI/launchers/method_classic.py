# -*- coding: utf-8 -*-
"""
This module provides different ways to run GSIMCLI in its initial version,
which consists in the geostatistical simulation approach [1]_ with the classic
version of Direct Sequential Simulation [2]_.

References
----------
.. [1] Costa, A., & Soares, A. (2009). Homogenization of climate data review
    and new perspectives using geostatistics. Mathematical Geosciences, 41(3),
    291–305. doi:10.1007/s11004-008-9203-3

.. [2] Soares, A. (2001). Direct sequential simulation and cosimulation.
    Mathematical Geology, 33(8), 911–926. doi:10.1023/A:1012246006212

Created on 22 de Out de 2013

@author: julio

"""

import glob
import ntpath
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import launchers.dss as dss
import multiprocessing as mp
import numpy as np
import pandas as pd
import parsers.dss as pdss
import parsers.gsimcli as pgc
# import parsers.spreadsheet as ss
import tools.grid as gr
import tools.homog as hmg
import tools.utils as ut


is_alive = True


def gsimcli(stations_file, stations_header, no_data, stations_order,
            correct_method, detect_prob, detect_flag, detect_save, exe_path,
            par_file, outfolder, purge_sims, correct_skew=None,
            correct_percentile=None, cores=None, dbgfile=None,
            print_status=False, skip_dss=False):
    """Main routine to run GSIMCLI homogenisation procedure in a set of
    stations.

    Parameters
    ----------
    stations_file : string or PointSet object
        Stations file path or PointSet instance.
    stations_header : boolean
        Stations file has the GSLIB standard header lines.
    no_data : number
        Missing data value.
    stations_order : array_like
        Stations' ID's in the order that they will be homogenised.
    correct_method : {'mean', 'median', 'skewness', 'percentile'} string,
        default 'mean'
        Method for the inhomogeneities correction:
            - mean: replace detected irregularities with the mean of simulated
                values;
            - median: replace detected irregularities with the median of
                simulated values;
            - skewness: use the sample skewness to decide whether detected
                irregularities will be replaced by the mean or by the median of
                simulated values.
            - percentile : replace detected irregularities with the percentile
                `100 * (1 - p)`, which is the same value used in the detection.
    detect_prob : float
        Probability value to build the detection interval centred in the local
        PDF.
    detect_flag : boolean
        DEPRECATED
    detect_save : boolean
        Save generated files in the procedure\: intermediary PointSet files
        containing candidate and reference stations, homogenised and simulated
        values, and DSS parameters files.
    exe_path : string
        DSS binary file path.
    par_file : string or DssParam object
        DSS parameters file path or DssParam instance.
    outfolder : string
        Directory to save the results.
    purge_sims : boolean
        Remove all simulated maps in the end.
    correct_skew : float, optional
        Samples skewness threshold, used if `correct_method == 'skewness'`.
    correct_percentile: float, optional
        p value used if correct_method == 'percentile'.
    cores : int, optional
        Maximum number of cores to be used. If None, it will use all available
        cores.
    dbgfile : string, optional
        Debug output file path. Write DSS console output to a file.
    print_status : boolean, default False
        Print some messages with the procedure status while it is running.
    skip_dss : boolean, default False
        Do not run DSS. Choose if the simulated maps are already in place and
        only the homogenisation process is needed.

    Returns
    -------
    homogenised_file : string
        Homogenised data file path. The generated file name ends with
        *_homogenised_data.csv*.
    dnumber_list : list of int
        Number of detected breakpoints in each candidate station.
    fnumber_list : list of int
        Number of missing data that were interpolated in each candidate
        station.

    """
    global is_alive

    if not cores or cores > mp.cpu_count():
        cores = mp.cpu_count()
    if print_status:
        print 'GSIMCLI using {} cores'.format(cores)

    # load data and prepare the iterative process
    if isinstance(stations_file, gr.PointSet):
        stations_pset = stations_file
    else:
        stations_pset = gr.PointSet()
        stations_pset.load(stations_file, nd=no_data, header=stations_header)

    if isinstance(par_file, pdss.DssParam):
        dsspar = par_file
    else:
        dsspar = pdss.DssParam()
        dsspar.load_old(par_file)  # TODO: old
    dnumber_list = list()
    fnumber_list = list()

    # workaround for Qt forcing backslash
    if os.name == "nt":
        exe_path = ntpath.abspath(exe_path)

    commonpath = os.path.commonprefix((outfolder, exe_path))
    # start iterative process
    for i in xrange(len(stations_order)):
        if not is_alive:
            raise SystemError("process aborted")
        if print_status:
            print ('Processing candidate {} out of {} with ID {}.'.
                   format(i + 1, len(stations_order), stations_order[i]))
        print "STATUS: candidate {}".format(stations_order[i])
        # manage stations
        candidate, references = hmg.take_candidate(stations_pset,
                                                   stations_order[i])
        # prepare and launch DSS
        basename = os.path.basename(outfolder)
        refname = basename + '_references_' + str(i) + '.prn'
        outname = basename + '_dss_map_st' + str(i) + '_sim.out'  # TODO: +1
        parname = basename + '_dss_par_st' + str(i) + '.par'
        candname = basename + '_candidate_' + str(i) + '.prn'
        reffile = os.path.join(outfolder, refname)
        outfile = os.path.join(outfolder, outname)
        reffile_nt = ntpath.relpath(os.path.join(outfolder, refname),
                                    commonpath)
        outfile_nt = ntpath.relpath(os.path.join(outfolder, outname),
                                    commonpath)
        # workaround for mp_exec, it needs one less directory in the tree
        reffile_nt = reffile_nt[reffile_nt.index('\\') + 1:]
        outfile_nt = outfile_nt[outfile_nt.index('\\') + 1:]

        parfile = os.path.join(outfolder, parname)
        references.save(psetfile=reffile, header=False)
        if detect_save:
            candfile = os.path.join(outfolder, candname)
            candidate.save(psetfile=candfile, header=True)
        if not skip_dss:
            dsspar.update(['datapath', 'output'], [reffile_nt, outfile_nt])
            dsspar.save_old(parfile)  # TODO: old
            oldpar = pdss.DssParam()
            oldpar.load_old(parfile)
            oldpar.nsim = 1
            purge_temp = False
            for sim in xrange(1, dsspar.nsim + 1, cores):
                if not is_alive:
                    raise SystemError("process aborted")
                if print_status:
                    print ('[{}/{}] Working on realization {}'.
                           format(i + 1, len(stations_order), sim))
                print "STATUS: realization {}".format(sim)
                if sim >= dsspar.nsim + 1 - cores:
                    purge_temp = True
                dss.mp_exec(dss_path=exe_path, par_path=oldpar, dbg=dbgfile,
                            output=outfile_nt, simnum=sim, cores=cores,
                            purge=purge_temp, totalsim=dsspar.nsim)

        # prepare detection
        intermediary_files = os.path.join(outfolder, basename + '_homogenised_'
                                          + str(i) + '.prn')
        dims = [dsspar.xx[0], dsspar.yy[0], dsspar.zz[0]]
        first_coord = [dsspar.xx[1], dsspar.yy[1], dsspar.zz[1]]
        cells_size = [dsspar.xx[2], dsspar.yy[2], dsspar.zz[2]]
        sim_maps = gr.GridFiles()
        sim_maps.load(outfile, dsspar.nsim, dims, first_coord, cells_size,
                      no_data, headerin=0)

        # detect and fix inhomogeneities
        if print_status:
            print 'Detecting inhomogeneities...'
        homogenisation = hmg.detect(grids=sim_maps, obs_file=candidate,
                                 method=correct_method, prob=detect_prob,
                                 flag=detect_flag, save=detect_save,
                                 outfile=intermediary_files, header=True,
                                 skewness=correct_skew,
                                 percentile=correct_percentile)
        homogenised, detected_number, filled_number = homogenisation
        if print_status:
            print 'Inhomogeneities detected: {}'.format(detected_number)
        dnumber_list.append(detected_number)
        fnumber_list.append(filled_number)
        # prepare next iteration
        stations_pset = hmg.append_homog_station(references, homogenised)
        if not detect_save:
            [os.remove(fpath) for fpath in
             [reffile, parfile]]  # , dsspar.transfile]]
        if purge_sims:
            sim_maps.purge()
        else:
            sim_maps.dump()

    # save results
    if print_status:
        print 'Process completed.'
        print 'Detections: ', ', '.join(map(str, dnumber_list))
        print 'Missing data filled: ', ', '.join(map(str, fnumber_list))
        print 'Saving results...'
    homogenised_file = os.path.join(outfolder, basename +
                                    '_homogenised_data.csv')
    hmg.save_output(pset_file=stations_pset, outfile=homogenised_file,
                    fformat='gsimcli', header=True, save_stations=True)

    return homogenised_file, dnumber_list, fnumber_list


def run_par(par_path, print_status=False, skip_dss=False, cores=None):
    """Run GSIMCLI using the settings included in a parameters file.

    Parameters
    ----------
    par_path : string or GsimcliParam object
        File path or GsimcliParam instance with GSIMCLI parameters.
    print_status : boolean, default False
        Print some messages with the procedure status while it is running.
    skip_dss : boolean, default False
        Do not run DSS. Choose if the simulated maps are already in place and
        only the homogenisation process is needed.
    cores : int, optional
        Maximum number of cores to be used. If None, it will use all available
        cores.

    Returns
    -------
    results : list
        Homogenised data file path, stations order, number of detected
        breakpoints in each candidate station, and number of missing data that
        were interpolated in each candidate station.

    See Also
    --------
    batch_decade : Run GSIMCLI with data files divided in decades.
    batch_networks : Run GSIMCLI along different networks.

    """
    if isinstance(par_path, pgc.GsimcliParam):
        gscpar = par_path
    else:
        gscpar = pgc.GsimcliParam(par_path)

    # dsspar_path = os.path.join(os.path.dirname(gscpar.dss_exe), 'DSSim.par')
    # dsspar = gscpar.update_dsspar(True, dsspar_path)
    dsspar = gscpar.update_dsspar(False)

    stations_pset = gr.PointSet()
    stations_pset.load(gscpar.data, gscpar.no_data, gscpar.data_header)
    stations_pset.flush_varnames(gscpar.variables)

    if hasattr(gscpar, 'name'):
        stations_pset.name = gscpar.name
    if hasattr(gscpar, 'variables'):
        stations_pset.varnames = gscpar.variables

    if gscpar.st_order == 'user':
        stations_set = gscpar.st_user
    else:
        stations_set = None
    stations_order = (hmg.station_order
                      (method=gscpar.st_order, nd=gscpar.no_data,
                       pset_file=stations_pset, header=gscpar.data_header,
                       userset=stations_set, ascending=gscpar.ascending,
                       md_last=gscpar.md_last))

    detect_flag = True
    skew = None
    perc = None
    if gscpar.correct_method.lower() == 'skewness':
        skew = gscpar.skewness
    elif gscpar.correct_method.lower() == 'percentile':
        perc = gscpar.percentile

    if print_status:
        print 'Candidates order: ', ', '.join(map(str, stations_order))
        print 'Set up complete. Running GSIMCLI...'
    results = gsimcli(stations_pset, gscpar.data_header, gscpar.no_data,
                      stations_order, gscpar.correct_method,
                      gscpar.detect_prob, detect_flag, gscpar.detect_save,
                      gscpar.dss_exe, dsspar, gscpar.results, gscpar.sim_purge,
                      skew, perc, cores=cores, print_status=print_status,
                      skip_dss=skip_dss)

    # FIXME: workaround for merge dependence
    results = list(results)
    results.insert(1, stations_order)

    return results


def batch_decade(par_path, variograms_file, print_status=False,
                 skip_dss=False, network_id=None, cores=None):
    """Batch process to run GSIMCLI with data files divided in decades.

    Parameters
    ----------
    par_path : string or GsimcliParam object
        File path or GsimcliParam instance with GSIMCLI parameters.
    variograms_file : string
        Variograms file path.
    print_status : boolean, default False
        Print some messages with the procedure status while it is running.
    skip_dss : boolean, default False
        Do not run DSS. Choose if the simulated maps are already in place and
        only the homogenisation process is needed.
    network_id : string, optional
        Network ID. If not given, will try to deduce from 'data' field, which
        should be passed in par_path.
    cores : int, optional
        Maximum number of cores to be used. If None, it will use all available
        cores.

    See Also
    --------
    run_par : Run GSIMCLI using the settings included in a parameters file.
    batch_networks : Run GSIMCLI along different networks.

    Notes
    -----
    The variograms file must follow these specifications\:
        - comma separated values (CSV)
        - nine labelled columns (not case sensitive)\:
            - variance
            - decade: decade in the format aaXX-aaYY (*aa* is optional)
            - model: {'S', 'E', 'G'}, (S = spherical, E = exponential,
                G = gaussian)
            - nugget: nugget effect
            - range
            - partial sill
            - nugget_norm: variance-normalised nugget effect
            - psill_norm: variance-normalised partial sill
            - sill_norm: variance-normalised total sill
            - other columns will be ignored

    The directory containing the decadal data files, which should be passed in
    the field 'data' of par_path, must have data files containing, at least,
    the first year of each decade in their file names.

    The variogram is assumed to be isotropic in the horizontal direction and
    with range 1 in the vertical (time) direction. It will default its angles
    to (0, 0, 0).

    """
    if isinstance(par_path, pgc.GsimcliParam):
        gscpar = par_path
    else:
        gscpar = pgc.GsimcliParam(par_path)

    variograms = pd.read_csv(variograms_file)
    # make case insensitive
    variograms.rename(columns=lambda x: x.lower(), inplace=True)

    results = list()
    outpath = str(gscpar.results)
    if not network_id:
        network_id = os.path.basename(os.path.dirname(gscpar.data))

    for decade in variograms.iterrows():
        if print_status:
            print "Processing decade: ", decade[1].ix['decade']
        print "STATUS: decade {}".format(decade[1].ix['decade'])
        os.chdir(os.path.dirname(variograms_file))
        first_year = decade[1].ix['decade'].split('-')[0].strip()
        # try to use the directory containing the decadal data, otherwise try
        # to find it in the same directory as the variograms file
        if os.path.exists(gscpar.data):
            if os.path.isfile(gscpar.data):
                data_folder = os.path.dirname(gscpar.data)
            else:
                data_folder = str(gscpar.data)
        else:
            data_folder = os.path.join(os.getcwd(), glob.glob('dec*')[0])

        data_file = os.path.join(data_folder, glob.glob
                                 (data_folder + '/*' + first_year + '*')[0])

        pset = gr.PointSet(psetpath=data_file, header=gscpar.data_header)
        if ('nugget_norm' in variograms.columns and
                'psill_norm' in variograms.columns):
            nugget = decade[1].ix['nugget_norm']
            psill = decade[1].ix['psill_norm']
        else:
            climcol = gscpar.variables.index('clim')
            psetvalues = pset.values.iloc[:, climcol].replace(pset.nodata,
                                                              np.nan)
            variance = psetvalues.var()
            nugget = decade[1].ix['nugget'] / variance
            psill = decade[1].ix['partial sill'] / variance

        results_folder = os.path.join(outpath, decade[1].ix['decade'])
        if not os.path.isdir(results_folder):
            os.mkdir(results_folder)
        fields = ['data', 'model', 'nugget', 'sill', 'ranges', 'zz_minimum',
                  'results']
        values = [data_file, decade[1].ix['model'][0],
                  str(nugget), str(psill),
                  ', '.join(map(str, ([decade[1].ix['range'],
                                       decade[1].ix['range'], 1]))),
                  first_year, results_folder]
#         new_par = os.path.join(gscpar.results, os.path.basename(gscpar.path))
#         gscpar.update(fields, values, True, ut.filename_indexing
#                       (new_par, decade[1].ix['decade']))
        gscpar.update(fields, values)
        results.append(run_par(gscpar, print_status, skip_dss, cores))

    # results_path = os.path.join(outpath, 'gsimcli_results.xls')
    # try to merge paths or use the second
    results_path = os.path.join(outpath, gscpar.results_file)
    hmg.merge_output(results, results_path)
#     ss.xls2costhome(xlspath=gsimclipath, outpath=outpath, nd=gscpar.no_data,
#                     sheet='All stations', header=False, skip_rows=[1],
#                     network_id=network_id, status='ho', variable='vv',
#                     resolution='y', content='d', ftype='data', yearly_sum=True)


def batch_networks(par_path, networks, decades=False, print_status=False,
                   skip_dss=False, cores=None):
    """Batch process to run GSIMCLI along different networks.
    
    WARNING: it is only working for decades=True

    Parameters
    ----------
    par_path : string or GsimcliParam object
        File path or GsimcliParam instance with GSIMCLI parameters.
    networks : list of string
        List with the networks' directories. Each network directory must have a
        file with the grid properties, and this file name must be of the type
        *\*grid\*.csv*.
    decades : boolean, default False
        Run GSIMCLI by decades separately. Each network directory must have a
        variogram file within it, and this file name must be of the type
        *\*variog\*.csv*.
    print_status : boolean, default False
        Print some messages with the procedure status while it is running.
    skip_dss : boolean, default False
        Do not run DSS. Choose if the simulated maps are already in place and
        only the homogenisation process is needed.
    cores : int, optional
        Maximum number of cores to be used. If None, it will use all available
        cores.

    See Also
    --------
    run_par : Run GSIMCLI using the settings included in a parameters file.
    batch_decade : Run GSIMCLI with data files divided in decades.

    Notes
    -----
    The file with the grid properties must follow these specifications\:
        - comma separated values (CSV)
        - seven labelled columns (not case sensitive)\:
            - xmin: initial value in X-axis
            - ymin: initial value in Y-axis
            - xnodes: number of nodes in X-axis
            - ynodes: number of nodes in Y-axis
            - znodes: number of nodes in Z-axis
            - xsize: node size in X-axis
            - ysize: node size in Y-axis
            - other columns will be ignored

    """
    gscpar = pgc.GsimcliParam(par_path)
    results_dir = str(gscpar.results)
    results_file = os.path.basename(gscpar.results_file)

    for network in networks:
        network_id = os.path.basename(network)
        if print_status:
            print "Processing network: ", network_id
        print "STATUS: network {}".format(network_id)
        os.chdir(network)
        specfile = os.path.join(network, glob.glob('*grid*.csv')[0])
        network_results = os.path.join(results_dir, network_id)
        if not os.path.isdir(network_results):
            os.mkdir(network_results)
        results_this_network = ut.filename_indexing(results_file, network_id)
        grid = hmg.read_specfile(specfile)
        fields = ['XX_nodes_number', 'XX_minimum', 'XX_spacing',
                 'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                 'ZZ_nodes_number', 'ZZ_spacing', 'results', 'results_file']
        values = [grid.xnodes, grid.xmin, grid.xsize,
                  grid.ynodes, grid.ymin, grid.ysize,
                  str(10), str(1), network_results, results_this_network]

        gscpar.update(fields, values, True, ut.filename_indexing
                      (par_path, network_id))

        if decades:
            variogram_file = os.path.join(network,
                                          glob.glob('*variog*.csv')[0])
            batch_decade(gscpar, variogram_file, print_status, skip_dss,
                         cores=cores)
        else:
            run_par(par_path, print_status, skip_dss, cores)


if __name__ == '__main__':
    # main()

    par = '/home/julio/Testes/cost-home/gsimcli.par'
    par = '/home/julio/Área de Trabalho/teste3.par'
    # run_par(par)

    base = '/home/julio/Testes/cost-home'
    """
    networks = [os.path.join(base, 'rede000004'),
                os.path.join(base, 'rede000005'),
                os.path.join(base, 'rede000008'),
                os.path.join(base, 'rede000010'),
                os.path.join(base, 'rede000020')]
    #"""
    networks = [os.path.join(base, 'rede000009')]
    batch_networks(par, networks, decades=True,
                   print_status=True, skip_dss=True)
#     variog = os.path.join(networks[0], "rede09_variografia_media.csv")
#     batch_decade(par, variog, print_status=True, skip_dss=False)
    print 'done'
