# -*- coding: utf-8 -*-
'''
Class definitions to support grid and point-set objects, as defined in GSLIB_.

.. _GSLIB: www.gslib.com

Created on 12 de Out de 2013

@author: julio
'''

import os
from scipy.stats import skew

import numpy as np
import pandas as pd
from tools.utils import skip_lines


class PointSet(object):
    """Class for storing point-set data (irregular mesh).

    Attributes
    ----------
    path : string
        File path.
    name: string
        Descriptive name.
    nvars: int
        Number of variables.
    nodata: number
        Missing data value.
    varnames: list of string
        Variables names.
    values: DataFrame
        Variables values.

    Notes
    -----
    According to GSLIB standard, a point-set file has the following format
        - descriptive name
        - number of variables
        - variables names, one per line (must have two LOCATION variables)
        - variables values, one per column, numeric values, space separated

    Example
    -------
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
        values : DataFrame
            Variables values.
        psetpath : string
            File path.
        header : boolean, default True
            PointSet file have the GSLIB standard header lines.

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

    def load(self, psetfile, nd=-999.9, header=True):
        """Load a point-set from a file in GSLIB format.

        Parameters
        ----------
        psetfile : string
            File path.
        nd : number
            Missing data value.
        header : boolean, default True
            PointSet file have the GSLIB standard header lines.

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

    def save(self, psetfile, header=True):
        """Write a point-set to a file in GSLIB format.

        Parameters
        ----------
        psetfile : string
            File path.
        header : boolean, default True
            PointSet file have the GSLIB standard header lines.

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
        varnames: list of string, optional
            Variables names.

        """
        if varnames:
            if 'Flag' in varnames:
                varnames.remove('Flag')  # TODO: this is a hack!
            self.values.columns = varnames
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
    """Class for storing a grid (regular mesh).

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
        Initial value in X coordinate.
    yi : number
        Initial value in Y coordinate.
    zi : number
        Initial value in Z coordinate.
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
    According to GSLIB standard, a grid file has the following format
        - descriptive name
        - number of variables
        - variables names, one per line
        - variables values, one per column, numeric values, space separated,
          does not need coordinates, location is deduced by a special ordering,
          point by point to the east, then row by row to the north, and finally
          level by level upward, i.e., x cycles fastest, then y, and finally z
          (FORTRAN-like order).

    Example
    -------
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

    TODO: support multiple variables in the same grid.
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
            PointSet file have the GSLIB standard header lines.

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
            PointSet file have the GSLIB standard header lines.


        TODO: needs fix, it is not drilling in the right place
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
    i.e., DSS realizations.

    TODO: make child of GridArr
    """
    def __init__(self):
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
        """Opens n files and provides a list containing each file handler.
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
        fpath, ext = os.path.splitext(first_file)
        for i in xrange(2, n + 1):
            another = fpath + str(i) + ext
            if os.path.isfile(another):
                self.files.append(open(another, 'rb'))
            else:
                raise IOError('File {0} not found.'.
                              format(os.path.basename(another)))

    def dump(self):
        """Close all files.
        """
        for grid in self.files:
            grid.close()
        self.nfiles = 0

    def purge(self):
        """Delete permanently all files from the filesystem.
        """
        self.dump()
        for grid in self.files:
            os.remove(grid.name)

    def stats(self, lmean=False, lmed=False, lvar=False, lstd=False,
              lcoefvar=False, lperc=False, p=0):
        """Calculate some statistics amongst every realization.

        TODO: - devolver em GridArr
              - handle no data
        """
        if lmean:
            meanmap = np.zeros(self.cells)
        if lmed:
            medmap = np.zeros(self.cells)
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
        for cell in xrange(self.cells - self.header):
            for i, grid in enumerate(self.files):
                if skip:
                    skip_lines(grid, self.header)
                arr[i] = grid.readline()

            skip = False
            if lmean:
                meanmap[cell] = arr.mean()
            if lmed:
                medmap[cell] = np.median(arr)
                # comparar com bottleneck.median()
            if lvar:
                varmap[cell] = np.nanvar(arr, ddof=1)
            if lstd:
                stdmap[cell] = arr.std()
            if lcoefvar:
                if lstd and lmean:
                    coefvarmap[cell] = stdmap[cell] / meanmap[cell] * 100
                else:
                    coefvarmap[cell] = arr.std() / arr.mean() * 100
            if lperc:
                percmap[cell] = np.percentile(arr, [(100 - p * 100) / 2,
                                                    100 - (100 - p * 100) / 2])

        retlist = list()

        if lmean:
            retlist.append(meanmap)
        if lmed:
            retlist.append(medmap)
        if lvar:
            retlist.append(varmap)
        if lstd:
            retlist.append(stdmap)
        if lcoefvar:
            retlist.append(coefvarmap)
        if lperc:
            retlist.append(percmap)

        return retlist

    def stats_vline(self, loc, lmean=False, lmed=False, lskew=False,
                    lvar=False, lstd=False, lcoefvar=False, lperc=False, p=0,
                    save=False):
        """Calculate some statistics amongst every realization, but only for
        the given location (vertical line).

        TODO: checkar stats variance com geoms

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

        arr = np.zeros(self.nfiles)
        skip = True

        z0 = 0
        loc = coord_to_grid(loc, [self.cellx, self.celly, self.cellz],
                    [self.xi, self.yi, self.zi])[:2]
        z_list = (loc[0] + self.dx * (loc[1] - 1) + self.dx * self.dy * z
                  for z in xrange(self.dz))

        for j, z in enumerate(z_list):
            for i, grid in enumerate(self.files):
                if skip:
                    skip_lines(grid, self.header)
                skip_lines(grid, int(z - z0 - 1))
                arr[i] = grid.readline()
            z0 = z
            skip = False
            if lmean:
                meanline[j] = arr.mean()
            if lmed:
                medline[j] = np.median(arr)
                # TODO: comparar com bottleneck.median()
            if lskew:
                skewline[j] = skew(arr)
            if lvar:
                varline[j] = np.nanvar(arr, ddof=1)
            if lstd:
                stdline[j] = arr.std()
            if lcoefvar:
                if lstd and lmean:
                    coefvarline[j] = stdline[z] / meanline[z] * 100
                else:
                    coefvarline[j] = arr.std() / arr.mean() * 100
            if lperc:
                percline[j] = np.percentile(arr, [(100 - p * 100) / 2,
                                                    100 - (100 - p * 100) / 2])
            if save:
                arrpset = PointSet('realizations at location ({}, {}, {})'.
                                   format(loc[0], loc[1], j * self.cellz +
                                          self.zi), self.nodata, 3,
                                   ['x', 'y', 'value'],
                                   values=np.zeros((self.nfiles, 3)))
                arrout = os.path.join(os.path.dirname(self.files[0].name),
                                      'sim values at ({}, {}, {}).prn'.
                                   format(loc[0], loc[1], j * self.cellz
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

        statspset.flush_varnames()
        return statspset


def coord_to_grid(coord, cells_size, first):
    """ Converte coordenadas cartesianas para coordenadas da grid (em número
    de nós).

    """
    if len(coord) < len(first):
        coord = list(coord)
        coord.append(first[2])
    coord = np.array(coord).astype('float')
    cells_size = np.array(cells_size)
    first = np.array(first)

    grid_coord = np.around((coord - first) / cells_size + 1).astype('int')
    return grid_coord


def wrap1():
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


def wrap2():
    # print 'loading grids'
    grids = GridFiles()
    grids.load(fstpar, 10, [50, 50, 10], [0, 0, 0], [1, 1, 1], -999.9, 0)
    vstats = grids.stats_vline((5, 5), lmean=True, lvar=True, lperc=True,
                               p=0.95)
    grids.dump()
    return vstats


if __name__ == '__main__':
    # import timeit
    fstpar = '/home/julio/Testes/test/test.out'
    outpath = '/home/julio/Testes/test'
    psetpath = '/home/julio/Testes/test/wells10.prn'

    """ timer
    print 'calculating grid stats + drill'
    print(timeit.timeit("wrap1()", setup="from __main__ import wrap1",
                        number=100))
    print 'calculating vline stats'
    print(timeit.timeit("wrap2()", setup="from __main__ import wrap2",
                        number=100))
    # """

    snirh = '/home/julio/Testes/snirh500_dssim_narrow/snirh.prn'
    bench = '/Users/julio/Desktop/testes/cost-home/rede000005/1900_1909.txt'

    # """
    pset = PointSet()
    # pset.load(snirh, header=False)
    pset.load(bench, header=True)
    # pset.save(os.path.join(outpath, 'psetout.prn'))
    # """
    # pset.to_costhome()
    print 'done'
