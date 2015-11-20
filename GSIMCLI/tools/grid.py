# -*- coding: utf-8 -*-
"""
Class definitions to support grid and point-set objects, as defined in GSLIB_.

.. _GSLIB: http://www.gslib.com

Created on 12 de Out de 2013

@author: julio
"""

import os
import time

import bottleneck as bn
import numpy as np
import pandas as pd
from tools.utils import skip_lines, filename_indexing


class PointSet(object):

    """Class for storing point-set data (irregular mesh).

    Attributes
    ----------
    path : string
        File path.
    name : string
        Descriptive name.
    nvars : int
        Number of variables.
    nodata : number
        Missing data value.
    varnames : list of string
        Variables names.
    values : pandas.DataFrame
        Variables values.

    Notes
    -----
    According to the GSLIB standard, a point-set file has the following format
        - descriptive name
        - number of variables
        - variables names, one per line (must have two LOCATION variables)
        - variables values, one per column, numeric values, space separated

    Examples
    --------
    snirh_data_set
    5
    x
    y
    year
    station
    wetdayscount
    271329 260536 1981 1   54
    271329 260536 1982 1   52
    271329 260536 1983 1   53
    271329 260536 1984 1   65
    271329 260536 1985 1   63

    References
    ----------
    GSLIB Help Page: File Formats : http://www.gslib.com/gslib_help/format.html

    """

    def __init__(self, name='', nodata=-999.9, nvars=0, varnames=list(),
                 values=np.zeros((0, 0)), psetpath=str(), header=True):
        """Constructor to initialise a PointSet instance.

        Parameters
        __________
        name : string
            Descriptive name.
        nvars : int
            Number of variables.
        varnames : list of string
            Variables names.
        values : pandas.DataFrame
            Variables values.
        psetpath : string
            File path.
        header : boolean, default True
            PointSet file has the GSLIB standard header lines.

        """
        self.path = psetpath
        if os.path.isfile(self.path):
            self.load(self.path, nodata, header)
        else:
            self.name = name
            self.nvars = nvars
            self.nodata = nodata
            self.varnames = varnames
            self.values = pd.DataFrame(values)
            if len(self.values.columns) == len(self.varnames):
                self.values.columns = self.varnames

    def add_var(self, values, varname=None):
        """Append a new variable to an existing PointSet.

        Parameters
        ----------
        values : array_like
            Set of values that will be added to the PointSet as a new variable.
        varname : string, optional
            The name of the new variable. If not provided, the new variable
            will be named as 'varNUMBER', according to the total NUMBER of
            variables in the PointSet. If there is an existing variable with
            the same name, it will not be overwritten, and the variable will
            be added with name `'varname' + '_new'`.

        """
        self.nvars += 1
        if varname is None:
            varname = 'var{}'.format(self.nvars)
        if varname in self.varnames:
            varname += '_new'
        self.varnames.append(varname)
        self.values[varname] = values

    def __repr__(self):
        return str(self.values)

    def load(self, psetfile, nd=-999.9, header=True):
        """Load a point-set from a file in GSLIB format.

        Parameters
        ----------
        psetfile : string
            File path.
        nd : number
            Missing data value.
        header : boolean, default True
            PointSet file has the GSLIB standard header lines.

        Notes
        -----
        If `header` is False, all variables will have name 'varNUMBER'.

        """
        self.path = psetfile
        self.nodata = nd
        self.varnames = list()
        fid = open(psetfile, 'r')
        if header:
            self.name = fid.readline().strip()
            self.nvars = int(fid.readline())
            for i in xrange(self.nvars):  # @UnusedVariable
                self.varnames.append(fid.readline().strip())
        values = np.loadtxt(fid)  # TODO: pd.read_table
        if not header:
            self.name = os.path.splitext(os.path.basename(psetfile))[0]
            self.nvars = values.shape[1]
            self.varnames = ['var{}'.format(i)
                             for i in xrange(1, self.nvars + 1)]
        self.values = pd.DataFrame(values, columns=self.varnames)
        fid.close()

    def save(self, psetfile=None, header=True):
        """Write a point-set to a file in GSLIB format.

        Parameters
        ----------
        psetfile : string, optional
            File path. If not specified, will rewrite the original file.
        header : boolean, default True
            PointSet file has the GSLIB standard header lines.

        """
        if not psetfile:
            psetfile = self.path
        else:
            self.path = psetfile
        fid = open(psetfile, 'w')
        if header:
            fid.write(self.name + '\n' + str(self.nvars) + '\n' +
                      '\n'.join(self.varnames) + '\n')
        np.savetxt(fid, self.values, fmt='%-10.6f')
        fid.close()

    def flush_varnames(self, varnames=None):
        """Update the DataFrame column labels with the current varnames list or
        with a given list of names.

        Parameters
        ----------
        varnames : list of string, optional
            Variables names.

        """
        if varnames:
            if 'Flag' in varnames:
                varnames.remove('Flag')  # TODO: this is a hack!
            self.values.columns = varnames
            self.varnames = varnames
        else:
            self.values.columns = self.varnames

#     def to_costhome(self, ftype='data', status='xx', variable='vv',
#                     resolution='r', station_id='ssssssss', content='c'):
#         """Convert a point-set to the COST-HOME format.
#
#         """
#         station = ch.Station(spec=(ftype, status, variable, resolution,
#                                    station_id, content), md=self.nodata)
#         station.data


class GridArr(object):

    """Class to store a grid (regular mesh).

    Attributes
    ----------
    name : string
        Descriptive name.
    dx : int
        Number of nodes in X-axis.
    dy : int
        Number of nodes in Y-axis.
    dz : int
        Number of nodes in Z-axis.
    xi : number
        Initial value in X-axis.
    yi : number
        Initial value in Y-axis.
    zi : number
        Initial value in Z-axis.
    cellx : number
        Node size in X-axis.
    celly : number
        Node size in Y-axis.
    cellz : number
        Node size in Z-axis.
    nodata : number
        Missing data value.
    val : ndarray
        One dimension array containing the grid values.

    Notes
    -----
    According to the GSLIB standard, a grid file has the following format
        - descriptive name
        - number of variables
        - variables names, one per line
        - variables values, one per column, numeric values, space separated,
          does not need coordinates, location is deduced by a special ordering,
          point by point towards the east, then row by row to the north, and
          finally level by level upward, i.e., x cycles fastest, then y, and
          finally z (FORTRAN-like order).

    Examples
    --------
    snirh_simulated
    1
    wetdayscount
    85.3
    93.1
    65.2
    72.4

    References
    ----------
    GSLIB Help Page: File Formats : http://www.gslib.com/gslib_help/format.html

    .. TODO: support multiple variables in the same grid.

    """

    def __init__(self, name='', dx=0, dy=0, dz=0, xi=0, yi=0, zi=0, cellx=1,
                 celly=1, cellz=1, nodata=-999.9, val=np.zeros(1)):
        """
        Constructor to initialise a GridArr instance.

        """
        self.name = name
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.xi = xi
        self.yi = yi
        self.zi = zi
        self.cellx = cellx
        self.celly = celly
        self.cellz = cellz
        self.nodata = nodata
        self.val = val

    def load(self, gridfile, dims, first, cells_size, nd=-999.9, skipheader=3):
        """Load a grid from a file in GSLIB format.

        Parameters
        ----------
        gridfile : string
            File path.
        dims : array_like of int
            Same as (dx, dy, dz).
        first : array_like of number
            Same as (xi, yi, zi).
        cells_size : array_like of number
            Same as (cellx, celly, cellz)
        nd : number, default -999.9
            Missing data value.
        skipheader : int, default 3
            Number of lines in the header.

        """
        self.dx = dims[0]
        self.dy = dims[1]
        self.dz = dims[2]
        self.xi = first[0]
        self.yi = first[1]
        self.zi = first[2]
        self.cellx = cells_size[0]
        self.celly = cells_size[1]
        self.cellz = cells_size[2]
        self.nodata = nd
        self.val = np.loadtxt(gridfile, skiprows=skipheader)

    def save(self, outfile, varname='var', header=True):
        """Write a grid to a file in GSLIB format.

        Parameters
        ----------
        outfile : string
            File path.
        varname : string, default 'var'
            Variable name.
        header : boolean, default True
            PointSet file has the GSLIB standard header lines.

        """
        fid = open(outfile, 'w')
        if header:
            fid.write(os.path.splitext(os.path.basename(outfile))[0] +
                      '\n1\n' + varname + '\n')
        # np.savetxt(fid, outvar.reshape(outvar.shape, order='F'), fmt='%10.4')
        np.savetxt(fid, self.val, fmt='%-10.6f')
        fid.close()

    def drill(self, wellxy, save=False, outfile=None, header=True):
        """Extract a vertical line from a grid.

        Parameters
        ----------
        wellxy : array_like
            Coordinates (x, y) of the drilling location.
        save : boolean, default False
            Write the result into a file.
        outfile : string, optional
            File path.
        header : boolean, default True
            PointSet file has the GSLIB standard header lines.

        .. TODO: needs fix, it is not drilling in the right place

        """
        well = PointSet()
        well.name = self.name + ' drilled at ' + str(wellxy)
        well.nodata = self.nodata
        well.nvars = 4
        well.varnames = ['x', 'y', 'z', 'var']
        well.values = pd.DataFrame(np.zeros((self.dz, 4)))
        well.values.iloc[:, :3] = (np.column_stack
                                   (((np.repeat(np.array(wellxy)
                                                [np.newaxis, :], self.dz,
                                                axis=0)),
                                     np.arange(1, self.dz + 1))))
        xy_nodes = coord_to_grid(wellxy, [self.cellx, self.celly, self.cellz],
                                 [self.xi, self.yi, self.zi])
        for z in xrange(self.dz):
            p = (xy_nodes[0] + self.dx * (xy_nodes[1] - 1) +
                 self.dx * self.dy * z)
            well.values.iloc[z, 3] = self.val[p]
        if save and outfile is not None:
            well.save(outfile, header)
        return well


class GridFiles(object):

    """This class keeps track of all the files containing simulation results,
    i.e., Direct Sequential Simulation (DSS) realisations.

    All PointSet files must have the same properties.

    Attributes
    ----------
    files : list of file
        List containing the files handler (type 'file').
    nfiles : int
        Number of files.
    dx : int
        Number of nodes in X-axis.
    dy : int
        Number of nodes in Y-axis.
    dz : int
        Number of nodes in Z-axis.
    xi : number
        Initial value in X-axis.
    yi : number
        Initial value in Y-axis.
    zi : number
        Initial value in Z-axis.
    cellx : number
        Node size in X-axis.
    celly : number
        Node size in Y-axis.
    cellz : number
        Node size in Z-axis.
    cells : int
        Total number of nodes in each grid.
    header : boolean, default True
        PointSet file has the GSLIB standard header lines.
    nodata : number
        Missing data value.

    .. TODO: make class child of GridArr?

    """

    def __init__(self):
        """Constructor to initialise a GridFiles instance.

        """
        self.files = list()
        self.nfiles = 0
        self.dx = 0
        self.dy = 0
        self.dz = 0
        self.xi = 0
        self.yi = 0
        self.zi = 0
        self.cellx = 1
        self.celly = 1
        self.cellz = 1
        self.cells = 0
        self.header = 0
        self.nodata = -999.9

    def load(self, first_file, n, dims, first_coord, cells_size, no_data,
             headerin=3):
        """Open several grid files and provide a list containing each file
        handler (delivered in the `files` attribute).

        Parameters
        ----------
        first_file : string
            File path to the first file to be opened. See notes for file names
            format.
        n : int
            Number of files.
        dims : array_like
            Number of nodes in each direction, [dx, dy, dz]
        first_coord : array_like
            First coordinate in each direction, [xi, yi, zi].
        cells_size : array_like
            Nodes size in each direction, [cellx, celly, cellz].
        no_data : number
            Missing data value.
        headerin : int, default 3
            Number of lines in the header.

        Raises
        ------
        IOError
            Could not find a file with an expected file name.

        Notes
        -----
        It is assumed that the files are numbered in the following manner:

        - 1st file_with_this_name.extension
        - 2nd file_with_this_name2.extension
        - 3rd file_with_this_name3.extension
        - nth file_with_this_namen.extension

        """
        self.nfiles = n
        self.dx = dims[0]
        self.dy = dims[1]
        self.dz = dims[2]
        self.xi = first_coord[0]
        self.yi = first_coord[1]
        self.zi = first_coord[2]
        self.cellx = cells_size[0]
        self.celly = cells_size[1]
        self.cellz = cells_size[2]
        self.cells = np.prod(dims)
        self.header = headerin
        self.nodata = no_data
        self.files.append(open(first_file, 'rb'))
        for i in xrange(2, n + 1):
            another = filename_indexing(first_file, i)
            if os.path.isfile(another):
                self.files.append(open(another, 'rb'))
            else:
                raise IOError('File {} not found.'.
                              format(os.path.basename(another)))

    def open_files(self, files_list, dims, first_coord, cells_size, no_data,
                   headerin=3, only_paths=False):
        """Open a list of given grid files and provide a list containing each
        file handler (delivered in the `files` attribute).

        Parameters
        ----------
        files_list : list
            List of file paths to the files to be opened
        dims : array_like
            Number of nodes in each direction, [dx, dy, dz]
        first_coord : array_like
            First coordinate in each direction, [xi, yi, zi].
        cells_size : array_like
            Nodes size in each direction, [cellx, celly, cellz].
        no_data : number
            Missing data value.
        headerin : int, default 3
            Number of lines in the header.
        only_paths : bool
            Do not open the files, just save their paths.

        Raises
        ------
        IOError
            Could not find a file with an expected file name.

        Notes
        -----
        It is assumed that the files are numbered in the following manner:

        - 1st file_with_this_name.extension
        - 2nd file_with_this_name2.extension
        - 3rd file_with_this_name3.extension
        - nth file_with_this_namen.extension

        """
        def append_opened(path):
            "Auxiliary function to minimise the number of conditions verified."
            self.files.append(open(path, 'rb'))

        self.nfiles = len(files_list)
        self.dx = dims[0]
        self.dy = dims[1]
        self.dz = dims[2]
        self.xi = first_coord[0]
        self.yi = first_coord[1]
        self.zi = first_coord[2]
        self.cellx = cells_size[0]
        self.celly = cells_size[1]
        self.cellz = cells_size[2]
        self.cells = np.prod(dims)
        self.header = headerin
        self.nodata = no_data

        if only_paths:
            open_file = self.files.append
        else:
            open_file = append_opened

        for gridfile in files_list:
            try:
                open_file(gridfile)
            except IOError, msg:
                print(msg)
                raise IOError('File {} not found.'.format(gridfile))

    def reset_read(self):
        """Reset the  pointer that reads each file to the beginning.

        """
        for grid in self.files:
            grid.seek(os.SEEK_SET)

    def dump(self):
        """Close all files.

        """
        for grid in self.files:
            grid.close()
        self.nfiles = 0

    def purge(self):
        """Remove all simulated map files from the filesystem permanently.

        """
        self.dump()
        # workaround for delay issue on NT systems
        time.sleep(1)
        for grid in self.files:
            os.remove(grid.name)

    def stats(self, lmean=False, lmed=False, lskew=False, lvar=False,
              lstd=False, lcoefvar=False, lperc=False, p=0.95):
        """Calculate some statistics among every realisation.

        Each statistic is calculated node-wise along the complete number of
        realisations.

        Parameters
        ----------
        lmean : boolean, default False
            Calculate the mean.
        lmed : boolean, default False
            Calculate the median.
        lskew : boolean, default False
            Calculate skewness.
        lvar : boolean, default False
            Calculate the variance.
        lstd : boolean, default False
            Calculate the standard deviation.
        lcoefvar : boolean, default False
            Calculate the coefficient of variation.
        lperc : boolean, default False
            Calculate the percentile `100 * (1 - p)`.
        p : number, default 0.95
            Probability value.

        Returns
        -------
        retdict : dict of GridArr
            Dictionary containing one GridArr for each calculated statistic.

        See Also
        --------
        stats_area : same but considering a circular (and horizontal) area of
        a specified radius around a given point.

        """
        # check if the map files are already opened or not
        if isinstance(self.files[0], file):
            opened_files = True
        else:
            opened_files = False

        if lmean:
            meanmap = np.zeros(self.cells)
        if lmed:
            medmap = np.zeros(self.cells)
        if lskew:
            skewmap = np.zeros(self.cells)
        if lvar:
            varmap = np.zeros(self.cells)
        if lstd:
            stdmap = np.zeros(self.cells)
        if lcoefvar:
            coefvarmap = np.zeros(self.cells)
        if lperc:
            percmap = np.zeros((self.cells, 2))

        arr = np.zeros(self.nfiles)
        skip = True
        offset = os.SEEK_SET
        for cell in xrange(self.cells - self.header):
            for i, gridfile in enumerate(self.files):
                # deal with map files not open yet
                if opened_files:
                    grid = gridfile
                else:
                    grid = open(gridfile, 'rb')
                    grid.seek(offset)

                if skip:
                    skip_lines(grid, self.header)
                arr[i] = grid.readline()

            if not opened_files:
                offset = grid.tell()
                grid.close()

            skip = False
            # replace no data's with NaN
            bn.replace(arr, self.nodata, np.nan)
            if lmean:
                meanmap[cell] = bn.nanmean(arr)
            if lmed:
                medmap[cell] = bn.nanmedian(arr)
            if lskew:
                skewmap[cell] = pd.Series(arr).skew()
            if lvar:
                varmap[cell] = bn.nanvar(arr, ddof=1)
            if lstd:
                stdmap[cell] = bn.nanstd(arr, ddof=1)
            if lcoefvar:
                if lstd and lmean:
                    coefvarmap[cell] = stdmap[cell] / meanmap[cell] * 100
                else:
                    std = bn.nanstd(arr, ddof=1)
                    mean = bn.nanmean(arr)
                    coefvarmap[cell] = std / mean * 100
            if lperc:
                percmap[cell] = pd.Series(arr).quantile([(1 - p) / 2,
                                                         1 - (1 - p) / 2])

        retdict = dict()

        if lmean:
            meangrid = GridArr(name='meanmap', dx=self.dx, dy=self.dy,
                               dz=self.dz, nodata=self.nodata, val=meanmap)
            retdict['meanmap'] = meangrid
        if lmed:
            medgrid = GridArr(name='medianmap', dx=self.dx, dy=self.dy,
                              dz=self.dz, nodata=self.nodata, val=medmap)
            retdict['medianmap'] = medgrid
        if lskew:
            skewgrid = GridArr(name='skewmap', dx=self.dx, dy=self.dy,
                               dz=self.dz, nodata=self.nodata, val=skewmap)
            retdict['skewmap'] = skewgrid
        if lvar:
            vargrid = GridArr(name='varmap', dx=self.dx, dy=self.dy,
                              dz=self.dz, nodata=self.nodata, val=varmap)
            retdict['varmap'] = vargrid
        if lstd:
            stdgrid = GridArr(name='stdmap', dx=self.dx, dy=self.dy,
                              dz=self.dz, nodata=self.nodata, val=stdmap)
            retdict['stdmap'] = stdgrid
        if lcoefvar:
            coefvargrid = GridArr(name='coefvarmap', dx=self.dx, dy=self.dy,
                              dz=self.dz, nodata=self.nodata, val=coefvarmap)
            retdict['coefvarmap'] = coefvargrid
        if lperc:
            percgrid = GridArr(name='percmap', dx=self.dx, dy=self.dy,
                               dz=self.dz, nodata=self.nodata, val=percmap)
            retdict['percmap'] = percgrid

        return retdict

    def stats_area(self, loc, tol=0, lmean=False, lmed=False, lskew=False,
                   lvar=False, lstd=False, lcoefvar=False, lperc=False,
                   p=0.95, save=False):
        """Calculate some statistics among every realisation, considering a
        circular (only horizontaly) area of radius `tol` around the point
        located at `loc`.

        Parameters
        ----------
        loc : array_like
            Location of the vertical line [x, y].
        tol : number, default 0
            Tolerance radius used to search for neighbour nodes.
        lmean : boolean, default False
            Calculate the mean.
        lmed : boolean, default False
            Calculate the median.
        lskew : boolean, default False
            Calculate skewness.
        lvar : boolean, default False
            Calculate the variance.
        lstd : boolean, default False
            Calculate the standard deviation.
        lcoefvar : boolean, default False
            Calculate the coefficient of variation.
        lperc : boolean, default False
            Calculate the percentile `100 * (1 - p)`.
        p : number, default 0.95
            Probability value.
        save : boolean, default False
            Write the points used to calculate the chosen statistics in
            PointSet format to a file named 'sim values at (x, y, line).prn'.

        Returns
        -------
        statspset : PointSet
            PointSet instance containing the calculated statistics.

        .. TODO: checkar stats variance com geoms

        """
        if lmean:
            meanline = np.zeros(self.dz)
        if lmed:
            medline = np.zeros(self.dz)
        if lskew:
            skewline = np.zeros(self.dz)
        if lvar:
            varline = np.zeros(self.dz)
        if lstd:
            stdline = np.zeros(self.dz)
        if lcoefvar:
            coefvarline = np.zeros(self.dz)
        if lperc:
            percline = np.zeros((self.dz, 2))

        # convert the coordinates of the first point to grid nodes
        loc = coord_to_grid(loc, [self.cellx, self.celly, self.cellz],
                            [self.xi, self.yi, self.zi])[:2]
        # find the nodes coordinates within a circle centred in the first point
        neighbours_nodes = circle(loc[0], loc[1], tol)
        # compute the lines numbers for each point in the neighbourhood, across
        # each grid layer. this yields a N*M matrix, with N equal to the number
        # of neighbour nodes, and M equal to the number of layers in the grid.
        neighbours_lines = [line_zmirror(node, [self.dx, self.dy, self.dz])
                            for node in neighbours_nodes]
        # sort the lines in ascending order
        neighbours_lines = np.sort(neighbours_lines, axis=0)
        # create an array to store the neighbour nodes in each grid file
        nnodes = neighbours_lines.shape[0]
        arr = np.zeros(self.nfiles * nnodes)

        skip = True
        curr_line = np.zeros(self.nfiles)

        for layer in xrange(neighbours_lines.shape[1]):
            for i, line in enumerate(neighbours_lines[:, layer]):
                for j, grid in enumerate(self.files):
                    # skip header lines only once per grid file
                    if skip and self.header:
                        skip_lines(grid, self.header)

                    # advance to the next line with a neighbour node
                    skip_lines(grid, int(line - curr_line[j] - 1))
                    # read the line and store its value
                    a = grid.readline()
                    arr[i + j * nnodes] = float(a)

                    curr_line[j] = line
                    skip = False

            # replace no data's with NaN
            bn.replace(arr, self.nodata, np.nan)
            # compute the required statistics
            if lmean:
                meanline[layer] = bn.nanmean(arr)
            if lmed:
                medline[layer] = bn.nanmedian(arr)
            if lskew:
                skewline[layer] = pd.Series(arr).skew()
            if lvar:
                varline[layer] = bn.nanvar(arr, ddof=1)
            if lstd:
                stdline[layer] = bn.nanstd(arr, ddof=1)
            if lcoefvar:
                if lstd and lmean:
                    coefvarline[layer] = stdline[layer] / meanline[layer] * 100
                else:
                    std = bn.nanstd(arr, ddof=1)
                    mean = bn.nanmean(arr)
                    coefvarline[layer] = std / mean * 100
            if lperc:
                percline[layer] = pd.Series(arr).quantile([(1 - p) / 2,
                                                           1 - (1 - p) / 2])
            if save and tol == 0:
                # FIXME: not working with the tolerance feature
                # need to adjust the arrpset or cherry-pick arr
                arrpset = PointSet('realisations at location ({}, {}, {})'.
                                   format(loc[0], loc[1], layer * self.cellz +
                                          self.zi), self.nodata, 3,
                                   ['x', 'y', 'value'],
                                   values=np.zeros((self.nfiles, 3)))
                arrout = os.path.join(os.path.dirname(self.files[0].name),
                                      'sim values at ({}, {}, {}).prn'.
                                   format(loc[0], loc[1], layer * self.cellz
                                          + self.zi))
                arrpset.values.iloc[:, 2] = arr
                arrpset.values.iloc[:, :2] = np.repeat(np.array(loc)
                                                       [np.newaxis, :],
                                                       self.nfiles, axis=0)
                arrpset.save(arrout, header=True)

        ncols = sum((lmean, lmed, lvar, lstd, lcoefvar, lskew))
        if lperc:
            ncols += 2
        statspset = PointSet(name='vertical line stats at (x,y) = ({},{})'.
                             format(loc[0], loc[1]), nodata=self.nodata,
                             nvars=3 + ncols, varnames=['x', 'y', 'z'],
                             values=np.zeros((self.dz, 3 + ncols)))

        statspset.values.iloc[:, :3] = (np.column_stack
                                        (((np.repeat(np.array(loc)
                                                     [np.newaxis, :], self.dz,
                                                     axis=0)),
                                          np.arange(self.zi, self.zi +
                                                    self.cellz * self.dz))))

        j = 3
        if lmean:
            statspset.varnames.append('mean')
            statspset.values.iloc[:, j] = meanline
            j += 1
        if lmed:
            statspset.varnames.append('median')
            statspset.values.iloc[:, j] = medline
            j += 1
        if lskew:
            statspset.varnames.append('skewness')
            statspset.values.iloc[:, j] = skewline
            j += 1
        if lvar:
            statspset.varnames.append('variance')
            statspset.values.iloc[:, j] = varline
            j += 1
        if lstd:
            statspset.varnames.append('std')
            statspset.values.iloc[:, j] = stdline
            j += 1
        if lcoefvar:
            statspset.varnames.append('coefvar')
            statspset.values.iloc[:, j] = coefvarline
            j += 1
        if lperc:
            statspset.varnames.append('lperc')
            statspset.varnames.append('rperc')
            statspset.values.iloc[:, -2:] = percline

        # reset the reading pointer in each grid file
        self.reset_read()
        # update varnames
        statspset.flush_varnames()
        return statspset


def coord_to_grid(coord, cells_size, first):
    """Upscale the given coordinates to the grid coordinate system (in number
    of nodes).

    It accepts coordinates in 2D (x, y) or 3D (x, y, z).

    Parameters
    ----------
    coord : array_like
        Coordinates to convert.
    cells_size : array_like
        Nodes dimension in each direction.
    first : array_like
        Initial coordinate value in each direction.

    Returns
    -------
    grid_coord : ndarray
        Upscaled coordinates.

    Notes
    -----
    The result is always in 3D (x, y, z).

    """
    if len(coord) < len(first):
        coord = list(coord)
        coord.append(first[2])
    coord = np.array(coord).astype('float')
    cells_size = np.array(cells_size)
    first = np.array(first)

    grid_coord = np.around((coord - first) / cells_size + 1).astype('int')
    return grid_coord


def grid_to_line(coord, dims):
    """Convert the coordinates of a point in a grid into the number of the line
    where it is located in the a grid file which follows the GSLIB standard.

    The header lines are not considered.

    Parameters
    ----------
    coord : array_like
        Coordinates to convert (x, y, z).
    dims : array_like
        Number of nodes in the grid, in each direction (x, y). The third
        dimension is not needed.

    Returns
    -------
    int
        Number of the line where the given point is located, given that the
        grid file is in the GSLIB standard.

    """
    return (coord[0] + dims[0] * (coord[1] - 1) +
            dims[0] * dims[1] * (coord[2] - 1))


def line_zmirror(loc, dims):
    """Compute the lines numbers corresponding to the vertical line starting
    in a given point.

    Parameters
    ----------
    loc : array_like
        Grid coordinates of the starting point (x, y). The third dimension is
        not needed.
    dims : array_like
        Number of nodes in the grid, in each direction (x, y, z).

    Returns
    -------
    list
        List of the number of the lines below the given point, in a vertical
        line.

    """
    return [grid_to_line([loc[0], loc[1], z], dims)
            for z in xrange(1, dims[2] + 1)]


def loadcheck(s, header):
    """Check if s is a file path or PointSet instance.

    Parameters
    ----------
    s : PointSet object or string
        Instance of PointSet type or string with the full path to the PointSet
        file.
    header : string
        True if `obs_file` has the GSLIB standard header lines.

    Returns
    -------
    PointSet

    Raises
    ------
    IOError
        `s` does not refer to an existing file.
    TypeError
        `s` must be a string or PointSet.

    """
    if isinstance(s, PointSet):
        return s
    elif isinstance(s, str):
        if not os.path.isfile(s):
            raise IOError("file {} not found".format(s))
        pset = PointSet()
        pset.load(s, header)
        return pset
    else:
        raise TypeError("need string or PointSet, {} found".format(type(s)))


def add_header(path, name=None, varnames=None, out=None):
    """Add standard GSLIB header to a file.

    Parameters
    ----------
    path : string or PointSet object
        File path or instance of PointSet type.
    name : string, optional
        Data set name. If not specified, it will write the file name.
    varnames : list of string, optional
        Variables names. If not specified, it will write *var*.
    out : string, optional
        File path. If not specified, it will write to a copy with *_nohead*
        appended to the file name.

    """
    with open(path, 'r+') as f:
        values = np.loadtxt(f)

    if out is None:
        fname, ext = os.path.splitext(path)
        out = fname + '_head' + ext

    with open(out, 'w+') as f:
        if name is None:
            name = os.path.splitext(os.path.basename(path))[0]
        f.write(name + '\n')
        if varnames is None:
            nvars = values.shape[1]
            varnames = ['var {}'.format(i) for i in xrange(nvars)]
        else:
            nvars = len(varnames)
        f.write(str(nvars) + '\n')
        for varname in varnames:
            f.write(varname + '\n')
        np.savetxt(f, values, fmt='%-10.6f')


def remove_header(path, out=None):
    """Remove standard GSLIB header from a file.

    Parameters
    ----------
    path : string or PointSet object
        File path or instance of PointSet type.
    out : string, optional
        File path. If not specified, it will write to a copy with *_nohead*
        appended to the file name.

    """
    if has_header(path):
        with open(path, 'r+') as f:
            f.readline()
            nvars = int(f.readline())
            skip_lines(f, nvars)
            values = np.loadtxt(f)

        if out is None:
            fname, ext = os.path.splitext(path)
            out = fname + '_nohead' + ext

        np.savetxt(out, values, fmt='%-10.6f')


def has_header(path):
    """Try to detect if standard GSLIB header is present.

    It checks for
        - second line value is an integer
        - that integer is equal to the number of columns

    Parameters
    ----------
    path : string
        File path.

    Returns
    -------
    boolean

    Notes
    -----
    It will return True in a case where there is not a header but is seems so,
    for instance

    `
    4
    1
    5
    2
    2
    4
    ...
    `

    """
    checklist = list()
    fh = open(path, 'r+')
    fh.readline()
    # check if the value in the 2nd line is integer
    nvars = fh.readline()
    try:
        checklist.append(nvars.strip() == str(int(nvars)))
    except ValueError:
        return False

    nvars = int(nvars)
    skip_lines(fh, nvars)

    # check if the number of variables matches with the number of columns
    first_values = fh.readline()
    checklist.append(len(first_values.split()) == nvars)

    return all(checklist)


def circle(xc, yc, r):
    """Compute a circle in a grid, centred in the point (xc, yc) and with
    radius equal to r. Return the coordinates of the nodes which are inside
    the circle.

    Parameteres
    -----------
    xc : int
        First coordinate (in nodes) of the circle centre.
    yc : int
        Second coordinate (in nodes) of the circle centre.
    r : int
        Circle radius (in nodes).

    Returns
    -------
    ndarray
        2D Matrix with the first and second coordinates of the nodes which are
        inside the circle.

    """
    # squared grid of the circle centre neighbourhood
    xx, yy = np.mgrid[xc - r:xc + r + 1, yc - r:yc + r + 1].astype('float32')
    # eliminate negative values
    xx[xx < 0] = np.nan
    yy[yy < 0] = np.nan
    # squared distance
    circle = (xx - xc) ** 2 + (yy - yc) ** 2
    # retrieve the points inside the circle
    inside = circle <= r ** 2

    return np.column_stack((xx[inside], yy[inside])).astype('int')


def _wrap1():
    # print 'loading grids'
    grids = GridFiles()
    grids.load(fstpar, 10, [50, 50, 10], [0, 0, 0], [1, 1, 1], -999.9, 0)
    # print 'calculating stats'
    gstats = grids.stats(lmean=True, lvar=True, lperc=True, p=0.95)
    # print 'saving output'
    meangrid = GridArr(name='meanmap', dx=50, dy=50, dz=10, val=gstats[0])
    meangrid.save(os.path.join(outpath, 'meanmap.out'), 'mean')
    vargrid = GridArr(name='varmap', dx=50, dy=50, dz=10, val=gstats[1])
    vargrid.save(os.path.join(outpath, 'varmap.out'), 'var')
    grids.dump()
    # print 'drilling'
    vline = meangrid.drill((5, 5), True, os.path.join(outpath,
                                                      'psetout.prn'))
    return vline


def _wrap2():
    # print 'loading grids'
    grids = GridFiles()
    grids.load(fstpar, nsims, griddims, fstcoord, nodesize, -999.9, 0)
    vstats = grids.stats_area(pointloc, tol=rad, lmean=True, lvar=True, lperc=True,
                              p=0.95)
    vstats.save(os.path.join(outpath, 'statsmap_t' + str(rad) + '.out'), 'var')
    grids.dump()
    return vstats


if __name__ == '__main__':
    import timeit
    fstpar = '/home/julio/Testes/cost-home/rede000010_work/1990-1999/1990-1999_dss_map_st0_sim.out'
    outpath = '/home/julio/Testes/cost-home/rede000010_work/test'
    psetpath = '/home/julio/Testes/cost-home/rede000010_work/1990-1999/1990-1999_candidate_0.prn'
    nsims = 500
    pointloc = [1815109.147, 7190958.185]
    griddims = [81, 122, 10]
    fstcoord = [1770000, 7094000, 1990]
    nodesize = [1000, 1000, 1]

    rad = 0
    print(timeit.timeit("_wrap2()", setup="from __main__ import _wrap2",
                    number=10))
    for rad in xrange(0, 5):  # (0, 3):

        # """ timer
        #     print 'calculating grid stats + drill'
        #     print(timeit.timeit("_wrap1()", setup="from __main__ import _wrap1",
        #                         number=100))
        print 'calculating vline stats'
        print 'tolerance: ', rad
        print(timeit.timeit("_wrap2()", setup="from __main__ import _wrap2",
                            number=10))
    # """

#     snirh = '/home/julio/Testes/snirh500_dssim_narrow/snirh.prn'
#     bench = '/Users/julio/Desktop/testes/cost-home/rede000005/1900_1909.txt'
#
# """
#     pset = PointSet()
# pset.load(snirh, header=False)
#     pset.load(bench, header=True)
    # pset.save(os.path.join(outpath, 'psetout.prn'))
    # """
    # pset.to_costhome()
    print 'done'
