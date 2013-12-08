# -*- coding: utf-8 -*-
'''
Created on 12 de Out de 2013

@author: julio
'''

import os
from scipy.stats import skew  # , skewtest

import numpy as np
import pandas as pd
from tools.utils import skip_lines


class PointSet:
    """Class for storing point-set data.
    """
    def __init__(self, name='', nodata=-999.9, nvars=0, varnames=list(),
                 values=np.zeros(0)):
        self.name = name
        self.nvars = nvars
        self.nodata = nodata
        self.varnames = varnames
        self.values = values

    def load(self, psetfile, nd=-999.9, header=True):
        """Loads a point-set from a file in GSLIB format.
        """

        fid = open(psetfile, 'r')
        if header:
            self.name = fid.readline().strip()
            self.nvars = int(fid.readline())
            for i in xrange(self.nvars):  # @UnusedVariable
                self.varnames.append(fid.readline().strip())
        self.values = np.loadtxt(fid)
        if not header:
            self.name = os.path.splitext(os.path.basename(psetfile))[0]
            self.nvars = self.values.shape[1]
            self.varnames = ['var{}'.format(i)
                             for i in xrange(1, self.nvars + 1)]
        fid.close()

    def save(self, psetfile, header=True):
        """Writes a point-set to a file in GSLIB format.
        """

        fid = open(psetfile, 'w')
        if header:
            fid.write(self.name + '\n' + str(self.nvars) + '\n' +
                      '\n'.join(self.varnames) + '\n')
        np.savetxt(fid, self.values, fmt='%-10.6f')
        fid.close()


class PointSetDF:
    """Class for storing point-set data.
    """
    def __init__(self, name='', nodata=-999.9, nvars=0, varnames=list(),
                 values=np.zeros((0, 0))):
        self.name = name
        self.nvars = nvars
        self.nodata = nodata
        self.varnames = varnames
        self.values = pd.DataFrame(values, columns=self.varnames)

    def load(self, psetfile, nd=-999.9, header=True):
        """Loads a point-set from a file in GSLIB format.
        """
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
        """Writes a point-set to a file in GSLIB format.
        """

        fid = open(psetfile, 'w')
        if header:
            fid.write(self.name + '\n' + str(self.nvars) + '\n' +
                      '\n'.join(self.varnames) + '\n')
        # self.values.to_csv(fid, header=False, index=False, sep=' ')
        np.savetxt(fid, self.values, fmt='%-10.6f')
        fid.close()


class GridArr:
    """Class for storing a single grid in memory.

    To do: make it possible to interact with multiple variables in same grid.
    """
    def __init__(self, name='', dx=0, dy=0, dz=0, xi=0, yi=0, zi=0, cellx=1,
                 celly=1, cellz=1, nodata=-999.9, val=np.zeros(1)):
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
        """Loads a grid from a file in GSLIB format.
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
        """Writes a grid to an output file in GSLIB format.
        """
        fid = open(outfile, 'w')
        if header:
            fid.write(os.path.splitext(os.path.basename(outfile))[0] +
                      '\n1\n' + varname + '\n')
        # np.savetxt(fid, outvar.reshape(outvar.shape, order='F'), fmt='%10.4')
        np.savetxt(fid, self.val, fmt='%-10.6f')
        fid.close()

    def drill(self, wellxy, save=False, outfile=None, header=True):
        """Extracts a vertical line from a grid.

        TODO: checkar se fura no sítio certo -- NÃO ESTÁ
        """
        well = PointSet()
        well.name = self.name + ' drilled at ' + str(wellxy)
        well.nodata = self.nodata
        well.nvars = 4
        well.varnames = ['x', 'y', 'z', 'var']
        well.values = np.zeros((self.dz, 4))
        well.values[:, :3] = np.column_stack(((np.repeat
                                              (np.array(wellxy)[np.newaxis, :],
                                                self.dz, axis=0)),
                                             np.arange(1, self.dz + 1)))
        xy_nodes = coord_to_grid(wellxy, [self.cellx, self.celly, self.cellz],
                      [self.xi, self.yi, self.zi])
        for z in xrange(self.dz):
            p = (xy_nodes[0] + self.dx * (xy_nodes[1] - 1) +
                 self.dx * self.dy * z)
            well.values[z, 3] = self.val[p]
        if save and outfile is not None:
            well.save(outfile, header)
        return well


class GridFiles:
    """This class keeps track of all the files containing simulation results,
    i.e., DSS realizations.
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
                varmap[cell] = arr.var()
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
                varline[j] = arr.var()
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
                arrpset.values[:, 2] = arr
                arrpset.values[:, :2] = np.repeat(np.array(loc)[np.newaxis, :],
                                               self.nfiles, axis=0)
                arrpset.save(arrout, header=True)

        ncols = sum((lmean, lmed, lvar, lstd, lcoefvar, lskew))
        if lperc:
            ncols += 2
        statspset = PointSet(name='vertical line stats at (x,y) = ({},{})'.
                             format(loc[0], loc[1]), nodata=self.nodata,
                             nvars=3 + ncols, varnames=['x', 'y', 'z'],
                             values=np.zeros((self.dz, 3 + ncols)))

        statspset.values[:, :3] = (np.column_stack
                                  (((np.repeat(np.array(loc)[np.newaxis, :],
                                               self.dz, axis=0)),
                                    np.arange(self.zi, self.zi +
                                              self.cellz * self.dz))))

        j = 3
        if lmean:
            statspset.varnames.append('mean')
            statspset.values[:, j] = meanline
            j += 1
        if lmed:
            statspset.varnames.append('median')
            statspset.values[:, j] = medline
            j += 1
        if lskew:
            statspset.varnames.append('skewness')
            statspset.values[:, j] = skewline
            j += 1
        if lvar:
            statspset.varnames.append('variance')
            statspset.values[:, j] = varline
            j += 1
        if lstd:
            statspset.varnames.append('std')
            statspset.values[:, j] = stdline
            j += 1
        if lcoefvar:
            statspset.varnames.append('coefvar')
            statspset.values[:, j] = coefvarline
            j += 1
        if lperc:
            statspset.varnames.append('lperc')
            statspset.varnames.append('rperc')
            statspset.values[:, -2:] = percline

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
    # print 'done'
    # print vline.values[:, 3]
    return vline


def wrap2():
    # print 'loading grids'
    grids = GridFiles()
    grids.load(fstpar, 10, [50, 50, 10], [0, 0, 0], [1, 1, 1], -999.9, 0)
    vstats = grids.stats_vline((5, 5), lmean=True, lvar=True, lperc=True,
                               p=0.95)
    grids.dump()
    # print vstats.values[:, 3]
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

    # """
    pset = PointSet()
    pset.load(snirh, header=False)
    # pset.save(os.path.join(outpath, 'psetout.prn'))
    # """
    pass
