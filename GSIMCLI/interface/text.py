# -*- coding: utf-8 -*-
"""
This module contains the text interface (interactive command line).

Notes
-----
It is not working, for now it is only the refactoring result (separated text
interface from the method launcher).

Created on 25/02/2014

@author: julio

"""

import os
import sys

sys.path.append('/home/julio/git/gsimcli/GSIMCLI')

import launchers.method_classic as mc
import parsers.cost as pcost
import parsers.dss as pdss
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
    print '7. GSIMCLI to COST-HOME'
    print '8. Add header to GSLIB'
    print '9. Remove header from GSLIB '
    print '\n0. Back'
    i = raw_input('\nOption number: ')

    if i == 1:
        print '·' * 21
        print 'Convert files from COST-HOME format to GSLIB\n'
        print 'Insert arguments and press [ENTER]\n'
        folder = raw_input('Full path to the folder containing data: ')
        var = raw_input('Variable (dd, ff, nn, tm, tn, tx, pp, rr, sd): ')
        amerge = False

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

    elif i == str(3):
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
        if not nd:
            nd = -999.9
        if not cols:
            cols = None
        if not sheet:
            sheet = 0
        if not header:
            header = None
        else:
            header = int(header)
        pointset, keys = ss.xls2gslib(xlspath, nd, cols, sheet, header)
        pointset.save(os.path.splitext(xlspath)[0] + '.prn', header=True)
        if keys:
            keys.to_excel(os.path.splitext(xlspath)[0] + '_keys.xls',
                          sheet_name=pointset.name)

    elif i == str(7):
        print '.' * 21
        print 'Convert files from GSIMCLI format to COST-HOME\n'
        print 'Insert arguments and press [ENTER]\n'
        gsimclipath = raw_input('Full path to the GSIMCLI file: ')
        outpath = raw_input('')
        nd = raw_input('Place holder for missing data (default: -999.9): ')
        sheet = raw_input('Sheet name or number containing the data to convert'
                          '(default: All stations): ')
        network_id = os.path.basename(os.path.dirname(gsimclipath))
        status = raw_input('Data status (default: ho): ')
        variable = raw_input('Data variable (default: rr): ')
        resolution = raw_input('Data temporal resolution (default: y): ')
        content = raw_input('Data content (default: d): ')
        # TODO: yearly_sum, keys_path
        ss.xls2costhome(xlspath=gsimclipath, outpath=outpath, nd=no_data,
                        sheet=sheet, header=False, skip_rows=None, cols=None,
                        network_id=network_id, status=status,
                        variable=variable, resolution=resolution,
                        content=content, ftype='data', yearly_sum=False,
                        keys_path=None)

        if not nd:
            nd = -999.9
        if not sheet:
            sheet = 'All stations'
        if not status:
            status = 'ho'
        if not variable:
            variable = 'rr'
        if not resolution:
            resolution = 'y'
        if not content:
            content = 'd'

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
        . ascrescentar as outras opções desenvolvidas
        . interface para o station_order outdated
    """
    print '·' * 21
    print 'Stations are homogenised one by one. Each homogenised station will'
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


def main():
    """Text interface: main menu

    TODO: outdated
    """
    print '······ GSIMCLI ······\n'
    print 'Main menu\n'
    print '1. Convert files'
    print '2. Locate DSS binary'
    print '3. Set up DSS parameters'
    print '4. homogenise network'
    print '5. homogenise multiple networks'
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
        stations_h = ut.yes_no(stations_h)
        stations_pset.load(stations_file, no_data, stations_h)
        if not stations_h:
            stations_pset = ask_add_header(stations_pset)
        # candidate stations order
        stations_order = ask_stations_method(stations_pset, stations_h)
        # inhomogeneities detection settings
        correct_method = raw_input('Detection method (mean/median): ').lower()
        detect_prob = float(raw_input('Probability for detection interval: '))
        detect_flag = True
        # results
        detect_save = raw_input('Save intermediary homogenised files? (Y/N) ')
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
        mc.gsimcli(stations_pset, stations_h, no_data, stations_order,
                   correct_method, detect_prob, detect_flag, detect_save,
                   exe_path, parfile, outfolder)
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
    pass
