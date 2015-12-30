'''
Created on 17/02/2014

@author: julio
'''
import os
import unittest

import numpy as np
import numpy.testing as nt
import parsers.shapefile as shp


class TestShapefile(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.ascii1_path = 'data/b17000asc.txt'
        cls.ascii1_dx = 81
        cls.ascii1_dy = 122
        cls.ascii1_dz = 10
        cls.ascii1_xi = 1770000
        cls.ascii1_yi = 7094000
        cls.ascii1_zi = 1900
        cls.ascii1_cellx = 1000
        cls.ascii1_celly = 1000
        cls.ascii1_cellz = 1
        cls.ascii1_nodata = -9999
        cls.shpfile = shp.Shapefile()

    @classmethod
    def teardown_class(cls):
        os.remove('data/test_grid_save.out')

    def test_load_ascii_file(self):
        self.shpfile.load_ascii(self.ascii1_path)
        self.assertIsInstance(self.shpfile.data, np.ndarray)
        self.assertEqual(self.shpfile.data.shape,
                         (self.ascii1_dy, self.ascii1_dx))

    def test_fetch_gridspecs(self):
        self.shpfile.load_ascii(self.ascii1_path)
        self.assertEqual(self.shpfile.dx, self.ascii1_dx)
        self.assertEqual(self.shpfile.dy, self.ascii1_dy)
        self.assertEqual(self.shpfile.dz, self.ascii1_dz)
        self.assertEqual(self.shpfile.xi, self.ascii1_xi)
        self.assertEqual(self.shpfile.yi, self.ascii1_yi)
        self.assertEqual(self.shpfile.zi, self.ascii1_zi)
        self.assertEqual(self.shpfile.cellx, self.ascii1_cellx)
        self.assertEqual(self.shpfile.celly, self.ascii1_celly)
        self.assertEqual(self.shpfile.cellz, self.ascii1_cellz)
        self.assertEqual(self.shpfile.nodata, self.ascii1_nodata)

    def test_ascii2grid(self):
        self.shpfile.load_ascii(self.ascii1_path)
        ascii2grid = self.shpfile.ascii2grid()
        self.assertEqual(ascii2grid.val.shape, (self.ascii1_dx * self.ascii1_dy
                                                * self.ascii1_dz,))

    def test_ascii2grid_order(self):
        self.shpfile.load_ascii(self.ascii1_path)
        grid = self.shpfile.ascii2grid()
        grid_2d = grid.val[:self.ascii1_dx * self.ascii1_dy]
        for j in xrange(self.ascii1_dy):
            for i in xrange(self.ascii1_dx):
                at_grid = grid_2d[i + self.ascii1_dx * j]
                at_orig = self.shpfile.data[-1 - j, i]
                self.assertEqual(at_grid, at_orig, 'order mismatch at (i,j) = '
                                 '({0},{1}), {2} != {4}'.
                                 format(i, j, at_grid, (at_orig, -1 - i, j)))

    def test_ascii2grid_save_load(self):
        from tools.grid import GridArr
        self.shpfile.load_ascii(self.ascii1_path)
        grid = self.shpfile.ascii2grid()
        outf = 'data/test_grid_save.out'
        grid.save(outf, grid.name, header=True)
        new_grid = GridArr()
        new_grid.load(outf, (self.ascii1_dx, self.ascii1_dy, self.ascii1_dz),
                      (self.ascii1_xi, self.ascii1_yi, self.ascii1_zi),
                      (self.ascii1_cellx, self.ascii1_cellz,
                       self.ascii1_cellz), self.ascii1_nodata)
        nt.assert_allclose(grid.val, new_grid.val, rtol=0.001,
                           err_msg='saved and loaded grids differ')
        grid2d = new_grid.val[:self.ascii1_dx * self.ascii1_dy]
        grid_ravel = np.rot90(grid2d.reshape((self.ascii1_dx, self.ascii1_dy),
                                             order='F'), 1)
        nt.assert_allclose(self.shpfile.data, grid_ravel, rtol=0.001,
                           err_msg='original and loaded ascii differ')


if __name__ == "__main__":
    import nose
    nose.runmodule(argv=[__file__, '-vvs'], exit=False)
