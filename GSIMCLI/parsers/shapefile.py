# -*- coding: utf-8 -*-
'''
Created on 17/02/2014

@author: julio
'''

# import pandas as pd
import os

import numpy as np
import tools.grid as gr


class Shapefile(object):
    def __init__(self):
        pass

    def load_ascii(self, path, dz=10, zi=1900, cellz=1):
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
