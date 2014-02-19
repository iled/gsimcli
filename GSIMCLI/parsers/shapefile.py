# -*- coding: utf-8 -*-
'''
Parsers for shapefile (GIS).

Created on 17/02/2014

@author: julio
'''

# import pandas as pd
import os

import numpy as np
import tools.grid as gr


class Shapefile(object):
    """Container for shapefile objects and related functions.

    """
    def __init__(self):
        pass

    def load_ascii(self, path, dz, zi, cellz):
        """Load a shapefile in ASCII format.

        This following format is generated, at least, by ArcGIS 'Export
        Feature Attribute' function:
        - text file (ASCII) with 6 header lines; keyword and value are space
        separated
        - ncols: number of columns (Y-axis)
        - nrows: number of rows (X-axis)
        - xllcorner: initial X coordinate
        - yllcorner: initial Y coordinate
        - cellsize: size of each cell, in every axis
        - NODATA_value: missing data value
        - Matrix with dimensions nrows * ncols

        Parameters
        ----------
        path: string
            File path
        dz: int
            Number of nodes in the Z-axis.
        zi: number
            Initial value for the Z coordinate.
        cellz: number
            Node size in the Z-axis.

        """
        self.path = path
        fid = open(path, 'rb')
        self.dx = int(fid.readline().split()[1])
        self.dy = int(fid.readline().split()[1])
        self.dz = dz
        self.xi = int(fid.readline().split()[1])
        self.yi = int(fid.readline().split()[1])
        self.zi = zi
        self.cellx = int(fid.readline().split()[1])
        self.celly = self.cellx
        self.cellz = cellz
        self.nodata = float(fid.readline().split()[1])
        self.data = np.loadtxt(fid)
        
    def ascii2grid(self):
        """Convert a shapefile in ASCII format to the GridArr format.
        
        Returns
        -------
        grid: GridArr object 
        
        """
        shpgrid = np.rot90(self.data, -1)
        shpgrid = shpgrid.flatten(order='F')
        shpgrid = np.tile(shpgrid, self.dz)
        grid = gr.GridArr(name=os.path.basename(self.path), dx=self.dx,
                          dy=self.dy, dz=self.dz, xi=self.xi, yi=self.yi,
                          zi=self.zi, cellx=self.cellx, celly=self.celly,
                          cellz=self.cellz, nodata=self.nodata, val=shpgrid)

        return grid


if __name__ == '__main__':
    pass
