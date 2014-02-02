# -*- coding: utf-8 -*-
'''
Created on 22 de Out de 2013

@author: julio

Basic command line interface for launching homogenization method as of
Costa, C. (2008).
It uses geostatistical simulation approach with classic DSS.
'''
import glob
import ntpath
import os
import sys

sys.path.append('/home/julio/git/gsimcli/GSIMCLI')

import launchers.dss as dss
import numpy as np
import pandas as pd
import parsers.cost as pcost
import parsers.dss as pdss
import parsers.gsimcli as pgc
import parsers.spreadsheet as ss
import tools.grid as gr
import tools.homog as hmg
import tools.utils as ut


def ask_add_header(pset):
    """Ask for the header when a point-set does not have any."""
    print 'Insert the point-set header metadata'
    pset.name = raw_input('Point-set name: ')
    for i in xrange(pset.nvars):
        pset.varnames[i] = (raw_input('Variable {} name: '.format(i + 1)).
                            strip())
    return pset


def ask_format(way):
    """Asks for input/output file format.
    input: 1 or True
    output: 0 or False
    """
    if way:
        print 'Select input format:\n'
        print '1. COST-HOME'
        print '2. GSLIB'
        print '3. SNIRH'
        i = raw_input('\nOption number: ')
        if i == str(1):
            pass
        elif i == str(2):
            print 'Option {} not implemented yet.\n'.format(i)
            ask_format(1)
        elif i == str(3):
            print 'Option {} not implemented yet.\n'.format(i)
            ask_format(1)
        else:
            print 'Option {} not available.\n'.format(i)
            ask_format(1)
        return i
    else:
        print 'Select output format:\n'
        print '1. COST-HOME'
        print '2. GSLIB'
        print '3. SNIRH'
        i = raw_input('\nOption number: ')
        if i == str(1):
            pass
        elif i == str(2):
            print 'Option {} not implemented yet.\n'.format(i)
            ask_format(1)
        elif i == str(3):
            print 'Option {} not implemented yet.\n'.format(i)
            ask_format(1)
        else:
            print 'Option {} not available.\n'.format(i)
            ask_format(1)
        return i


def ask_merge():
    print 'Group stations of the same network in one single file?'
    m = raw_input('Y/N: ')
    if m.lower() == 'y':
        return True
    elif m.lower == 'n':
        return False
    else:
        ask_merge()


def convert_files():
    """Options for converting files format.

    TODO: other formats
    """
    print '·' * 21
    print 'Convert files format\n'
    print '1. COST-HOME to GSLIB'
    print '2. COST-HOME to CSV'
    print '3. GSLIB to COST-HOME'
    print '4. GSLIB to CSV'
    print '5. CSV to GSLIB'
    print '6. XLS to GSLIB'
    print '7. Add header to GSLIB'
    print '8. Remove header from GSLIB '
    print '\n0. Back'
    i = raw_input('\nOption number: ')

    if i == 1:
        print '·' * 21
        print 'Convert files from COST-HOME format to GSLIB\n'
        print 'Insert arguments and press [ENTER]\n'
        folder = raw_input('Full path to the folder containing data: ')
        var = raw_input('Variable (dd, ff, nn, tm, tn, tx, pp, rr, sd): ')
        amerge = ask_merge()

        for root, dirs, files in os.walk(folder):  # @UnusedVariable
            if (len(dirs) > 0 and
                all([len(d) == 6 and d.isdigit() for d in dirs])):
                print 'processing ' + root
                parsed_files = pcost.directory_walk_v1(root)
                selected_files = pcost.files_select(parsed_files, ftype='data',
                                              variable=var, content='d')
                if selected_files:
                    pcost.convert_gslib(selected_files, merge=amerge)
        print 'done'
        convert_files()

    elif i == str(2):
        pass

    elif i == str(6):
        print '·' * 21
        print 'Convert files from XLS format to GSLIB\n'
        print 'Insert arguments and press [ENTER]\n'
        xlspath = raw_input('Full path to the XLS file: ')
        nd = raw_input('Place holder for missing data (default: -999.9): ')
        cols = raw_input('Which columns to convert (e.g., 0, 1, 4; '
                         'default: all): ')
        sheet = raw_input('Which sheet (number) to convert (e.g., 0; '
                          'default: first): ')
        header = raw_input('Which line has the header (e.g., 0; '
                           'default: none): ')
        if len(nd) == 0:
            nd = -999.9
        if len(cols) == 0:
            cols = None
        if len(sheet) == 0:
            sheet = 0
        if len(header) == 0:
            header = None
        else:
            header = int(header)
        pointset, keys = ss.xls2gslib(xlspath, nd, cols, sheet, header)
        pointset.save(os.path.splitext(xlspath)[0] + '.prn', header=True)
        if keys:
            keys.to_excel(os.path.splitext(xlspath)[0] + '_keys.xls',
                          sheet_name=pointset.name)

    elif i == str(0):
        main()
    else:
        print 'Invalid option: "{}". Press [ENTER] to try again.'.format(i)
        raw_input()
        convert_files()


def dss_par():
    print '·' * 21
    print 'DSS Parameters\n'
    print '1. Use previously defined parameters file'
    print '2. Load a parameters file as a default and adjust it'
    print '3. Set up a new file'
    print '\n0. Main menu'
    i = raw_input('\nOption number: ')

    par = pdss.DssParam()

    if i == str(1):
        parfile = raw_input('Full path to the existing parameter file: ')
        par.load(parfile)
    elif i == str(2):
        parfile = raw_input('Full path to the default parameter file: ')
        print 'Insert new value or press [ENTER] to leave the default value.\n'
        par.load(parfile)
        par.ask_update_default()
        outfile = raw_input('Full path to where to save the new parameter '
                            'file or press [ENTER] to rewrite the default: ')
        if outfile:
            parfile = outfile
        par.save(parfile)
    elif i == str(3):
        parfile = raw_input('Full path to the existing parameter file: ')
        print 'Insert value for each parameter.\n'
        par.ask_new()
        par.save(parfile)
    elif i == str(0):
        main()
    else:
        print 'Invalid option: "{}". Press [ENTER] to try again.'.format(i)
        raw_input()
        par = dss_par()

    return par


def ask_save_vars(pset):
    """Asks which variables should be written in the output file.
    """
    print 'Select which variables should be written in the output file.\n'
    for i, var in enumerate(pset.varnames):
        print '{}. {}'.format(i, var)
    lvars = raw_input('\nChoose by writing each variable number in the desired'
                     ' order (separated with [SPACE]): ')
    return [int(v) for v in lvars.split()]


def ask_stations_method(pset, header=True):
    """Asks which method will be used to select candidate stations.

    TODO:
        . escolhe uma e depois faz por proximidade
        . investigar outros métodos
        . precisa do no data para o station_order
    """
    print '·' * 21
    print 'Stations are homogenized one by one. Each homogenized station will'
    print 'be included as a reference station to the others.'
    print 'Select which stations will be considered as candidates and in'
    print 'which order.\n'
    print '1. List stations ID'
    print '2. Use all stations randomly sorted'
    print '3. Sort all stations in ascending order'
    print '4. Specify which stations will be candidates and their order'
    print '\n0. Main menu'
    i = raw_input('\nOption number: ')

    stations_list = hmg.list_stations(pset, header)
    if i == str(1):
        print stations_list
        raw_input('Press [ENTER] to continue.')
        stations = ask_stations_method(pset, header)
    elif i == str(2):
        stations = hmg.station_order(stations_list, method='random')
    elif i == str(3):
        stations = hmg.station_order(stations_list, method='sorted')
    elif i == str(4):
        stations_user = raw_input('Write stations ID in the desired order '
                                 '(e.g., 72 10 59 56): ')
        stations_set = [int(i) for i in stations_user.split()]
        stations = hmg.station_order(stations_list, method='user',
                                     userset=stations_set)
    elif i == str(0):
        main()
    else:
        print 'Invalid option: "{}". Press [ENTER] to try again.'.format(i)
        raw_input()
        stations = ask_stations_method(pset, header)

    return stations


def gsimcli(stations_file, stations_h, no_data, stations_order, detect_method,
         detect_prob, detect_flag, detect_save, exe_path, par_file, outfolder,
         purge_sims, detect_skew=None):
    """Main cycle to run GSIMCLI homogenization procedure in a set of stations

    """
    dbgfile = os.path.join(outfolder, 'dsscmd.txt')  # TODO: opt for dbg
    if os.path.isfile(dbgfile):
        os.remove(dbgfile)
    # load data and prepare the iterative process
    if isinstance(stations_file, gr.PointSet):
        stations_pset = stations_file
    else:
        stations_pset = gr.PointSet()
        stations_pset.load(stations_file, nd=no_data, header=stations_h)

    if isinstance(par_file, pdss.DssParam):
        dsspar = par_file
    else:
        dsspar = pdss.DssParam()
        dsspar.load_old(par_file)  # TODO: old
    dnumber_list = list()
    fnumber_list = list()

    commonpath = os.path.commonprefix((outfolder, exe_path))
    # start iterative process
    for i in xrange(len(stations_order)):
        print ('Processing candidate {} out of {} with ID {}.'.
               format(i + 1, len(stations_order), stations_order[i]))
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
        parfile = os.path.join(outfolder, parname)
        references.save(psetfile=reffile, header=False)
        if detect_save:
            candfile = os.path.join(outfolder, candname)
            candidate.save(psetfile=candfile, header=True)
        dsspar.update(['datapath', 'output'], [reffile_nt, outfile_nt])
        dsspar.save_old(parfile)  # TODO: old
        oldpar = pdss.DssParam()
        oldpar.load_old(parfile)
        oldpar.nsim = 1
        for sim in xrange(1, dsspar.nsim + 1):
            print ('[{}/{}] Working on realization {}'.
                   format(i + 1, len(stations_order), sim))
            oldpar.save_old(os.path.join(os.path.dirname(exe_path),
                                         'DSSim.par'))
            dss.exec_ssdir(exe_path, parfile, dbgfile)
            oldfilent = (ntpath.splitext(outfile_nt)[0] + str(sim + 1) +
                         ntpath.splitext(outfile_nt)[1])
            oldpar.update(['output', 'seed'], [oldfilent, oldpar.seed + 2])

        # raw_input('Go and run DSS with these parameters: {}'.format(parfile))
        # prepare detection
        intermediary_files = os.path.join(outfolder, basename + '_homogenized_'
                                          + str(i) + '.prn')
        dims = [dsspar.xx[0], dsspar.yy[0], dsspar.zz[0]]
        first_coord = [dsspar.xx[1], dsspar.yy[1], dsspar.zz[1]]
        cells_size = [dsspar.xx[2], dsspar.yy[2], dsspar.zz[2]]
        sim_maps = gr.GridFiles()
        sim_maps.load(outfile, dsspar.nsim, dims, first_coord, cells_size,
                      no_data, headerin=0)
        print 'Detecting inhomogeneities...'
        # detect and fix inhomogeneities
        homogenization = hmg.detect(grids=sim_maps, obs_file=candidate,
                                 method=detect_method, prob=detect_prob,
                                 flag=detect_flag, save=detect_save,
                                 outfile=intermediary_files, header=True,
                                 skewness=detect_skew)
        homogenized, detected_number, filled_number = homogenization
        print 'Inhomogeneities detected: {}'.format(detected_number)
        dnumber_list.append(detected_number)
        fnumber_list.append(filled_number)
        # prepare next iteration
        stations_pset = hmg.append_homog_station(references, homogenized)
        if not detect_save:
            [os.remove(fpath) for fpath in
             [reffile, parfile, dbgfile, dsspar.transfile]]
        if purge_sims:
            sim_maps.purge()
        else:
            sim_maps.dump()

    # save results
    print 'Process completed.'
    print 'Detections: ', ', '.join(map(str, dnumber_list))
    print 'Missing data filled: ', ', '.join(map(str, fnumber_list))
    print 'Saving results...'
    homogenized_file = os.path.join(outfolder, basename +
                                    '_homogenized_data.csv')
    hmg.save_output(pset_file=stations_pset, outfile=homogenized_file,
                    fformat='gsimcli', header=True, station_split=True,
                    save_stations=True)

    return homogenized_file, stations_order, dnumber_list, fnumber_list


def run_par(par_path):
    """Run GSIMCLI using the settings included in a parameters file.

    """
    if isinstance(par_path, pgc.GsimcliParam):
        gscpar = par_path
    else:
        gscpar = pgc.GsimcliParam(par_path)

    dsspar_path = os.path.join(os.path.dirname(gscpar.dss_exe), 'DSSim.par')
    dsspar = gscpar.update_dsspar(True, dsspar_path)

    stations_pset = gr.PointSet()
    stations_pset.load(gscpar.data, gscpar.no_data, gscpar.data_header)
    stations_pset.flush_varnames(gscpar.variables)

    if hasattr(gscpar, 'name'):
        stations_pset.name = gscpar.name
    if hasattr(gscpar, 'variables'):
        stations_pset.varnames = gscpar.variables
        # for i in xrange(len(stations_pset.varnames)):
        #    stations_pset.varnames[i] = gscpar.variables.split(',')[i].strip()

    if gscpar.st_order == 'user':
        stations_set = gscpar.st_user
    else:
        stations_set = None
    stations_order = (hmg.station_order
                      (method=gscpar.st_order, nd=gscpar.no_data,
                       pset_path=stations_pset, header=gscpar.data_header,
                       userset=stations_set, md_last=gscpar.md_last))

    detect_flag = True
    if gscpar.detect_method.lower() == 'skewness':
        skew = gscpar.skewness
    else:
        skew = None

    print 'Candidates order: ', ', '.join(map(str, stations_order))
    print 'Set up complete. Running GSIMCLI...'
    results = gsimcli(stations_pset, gscpar.data_header, gscpar.no_data,
                      stations_order, gscpar.detect_method, gscpar.detect_prob,
                      detect_flag, gscpar.detect_save, gscpar.dss_exe, dsspar,
                      gscpar.results, gscpar.sim_purge, skew)

    return results


def batch_decade(par_path, variograms_file):
    """Batch process to run gsimcli with data files divided in decades.

          .receber variância já normalizada
    """
    if isinstance(par_path, pgc.GsimcliParam):
        gscpar = par_path
    else:
        gscpar = pgc.GsimcliParam(par_path)

    network_parpath = gscpar.path
    variograms = pd.read_csv(variograms_file)
    os.chdir(os.path.dirname(variograms_file))
    results = list()

    for decade in variograms.iterrows():
        first_year = decade[1].ix['Decade'].split('-')[0].strip()
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
            nugget = decade[1].ix['Nugget'] / variance
            psill = decade[1].ix['Partial Sill'] / variance

        results_folder = os.path.join(os.path.dirname(variograms_file),
                                      decade[1].ix['Decade'])
        if not os.path.isdir(results_folder):
            os.mkdir(results_folder)
        fields = ['data', 'model', 'nugget', 'sill', 'ranges', 'ZZ_minimum',
                  'results']
        values = [data_file, decade[1].ix['Model'][0],
                  str(nugget), str(psill),
                  ', '.join(map(str, ([decade[1].ix['Range'],
                                       decade[1].ix['Range'], 1]))),
                  first_year, results_folder]
        gscpar.update(fields, values, True, ut.filename_indexing
                      (network_parpath, decade[1].ix['Decade']))
        results.append(run_par(gscpar))

    hmg.merge_output(results, os.path.join(os.path.dirname(variograms_file),
                     'gsimcli_results.xls'))


def batch_networks(par_path, networks, decades=False):
    """Batch process to run gscimcli at different networks.

    """
    gscpar = pgc.GsimcliParam(par_path)

    for network in networks:
        os.chdir(network)
        specfile = os.path.join(network, glob.glob('*grid*.csv')[0])
        grid = pd.read_csv(specfile)
        fields = ['XX_nodes_number', 'XX_minimum', 'XX_spacing',
                 'YY_nodes_number', 'YY_minimum', 'YY_spacing',
                 'ZZ_nodes_number', 'ZZ_spacing', 'results']
        values = [grid.xnodes, grid.xmin, grid.xsize,
                  grid.ynodes, grid.ymin, grid.ysize,
                  str(10), str(1), network]
        gscpar.update(fields, values, True, ut.filename_indexing
                      (par_path, os.path.basename(network)))

        if decades:
            variogram_file = os.path.join(network,
                                          glob.glob('*variog*.csv')[0])
            batch_decade(gscpar, variogram_file)
        else:
            run_par(par_path)


def main():
    """Text interface: main menu

    """
    print '······ GSIMCLI ······\n'
    print 'Main menu\n'
    print '1. Convert files'
    print '2. Locate DSS binary'
    print '3. Set up DSS parameters'
    print '4. Homogenize network'
    print '5. Homogenize multiple networks'
    i = raw_input('\nOption number: ')

    if i == str(1):
        convert_files()
    elif i == str(2):
        exe_path = raw_input('Full path to DSS binary file: ')
    elif i == str(3):
        parfile = dss_par()
    elif i == str(4):
        # check if *.par file exists
        try:
            parfile
        except NameError:
            print 'DSS parameters are not set up yet. Press [ENTER] to do it.'
            raw_input()
            parfile = dss_par()

        # hard-data
        # TODO: pode ler isso no PAR
        stations_file = raw_input('Full path to stations point-set file: ')
        stations_pset = gr.PointSet()
        no_data = parfile.nd
        stations_h = raw_input('Does that file have a header? (Y/N) ')
        if stations_h.lower() == 'y':
            stations_h = True
        else:
            stations_h = False
        stations_pset.load(stations_file, no_data, stations_h)
        if not stations_h:
            stations_pset = ask_add_header(stations_pset)
        # candidate stations order
        stations_order = ask_stations_method(stations_pset, stations_h)
        # inhomogeneities detection settings
        detect_method = raw_input('Detection method (mean/median): ').lower()
        detect_prob = float(raw_input('Probability for detection interval: '))
        detect_flag = True
        # results
        detect_save = raw_input('Save intermediary homogenized files? (Y/N) ')
        if detect_save.lower() == 'y':
            detect_save = True
        else:
            detect_save = False
        outfolder = raw_input('Full path to results folder: ')
        # simulation binary
        try:
            exe_path
        except NameError:
            exe_path = raw_input('Full path to DSS binary file: ')
        # let's go!
        print 'Set up complete. Running GSIMCLI...'
        gsimcli(stations_pset, stations_h, no_data, stations_order,
                detect_method, detect_prob, detect_flag, detect_save, exe_path,
                parfile, outfolder)
    elif i == str(5):
        pass
    else:
        print 'Invalid option: "{}". Press [ENTER] to try again.'.format(i)
        raw_input()
        main()

    print 'Done.\nPress [ENTER] to continue.'
    raw_input()
    main()


if __name__ == '__main__':
    # main()

    par = '/home/julio/Testes/cost-home/gsimcli.par'
    # run_par(par)

    # decvars = '/home/julio/Testes/rede000005/resumo_variografia_rede05_csv.csv'
    # batch_decade(par, decvars)
    base = '/home/julio/Testes/cost-home'
    """
    networks = [os.path.join(base, 'rede000004'),
                os.path.join(base, 'rede000005'),
                os.path.join(base, 'rede000008'),
                os.path.join(base, 'rede000010'),
                os.path.join(base, 'rede000020')]
    #"""
    networks = [os.path.join(base, 'rede000009')]
    batch_networks(par, networks, decades=True)
    print 'done'
