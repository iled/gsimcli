# -*- coding: utf-8 -*-
"""
Created on 05/03/2015

@author: julio
"""
from PySide import QtGui, QtCore
import glob2
import os
import sys

from external_libs.pyside_dynamic import loadUi
import interface.ui_utils as ui
from tools.homog import read_specfile

base = os.path.dirname(os.path.dirname(__file__))


class SimStats(QtGui.QWidget):
    """Interface to the calculation of statistics across simulated maps.

    """
    def __init__(self, parent=None):
        """Constructor.

        """
        super(SimStats, self).__init__(parent)
        # load ui file
        loadUi(os.path.join(base, "interface", "tools.simstats.ui"), self)

        # set params
        self.set_gui_params()
        if hasattr(self.parent, "default_dir"):
            self.default_dir = self.parent.default_dir
        else:
            self.default_dir = os.path.expanduser('~/')

        # buttons
#         self.buttonCalculate.clicked.connect(self.calculate_stats)
        self.buttonSimsPath.clicked.connect(self.browse_simdir)
        self.buttonSavePath.clicked.connect(self.browse_savedir)
        self.buttonAddSim.clicked.connect(self.browse_simfile)
        self.buttonRemoveSim.clicked.connect(self.remove_sims)

        # label
        self.sim_label = self.labelSimFiles.text()

        # line
        self.lineSimsPath.editingFinished.connect(self.set_simmaps)

        # radio
        self.radioGridManual.toggled.connect(self.enable_manualspec)
        self.radioGridFile.toggled.connect(self.browse_gridfile)
        # self.radioGridSame.toggled.connect(self.set_samegrid)

    def browse_gridfile(self, toggle):
        """Dialog to select the file with the grid specifications.
        Connected to the GridFile radio button.

        """
        if toggle:
            caption = "Select the grid specifications file"
            filters = "Grid spec (*grid*.csv);;CSV files (*.csv)"
            filepath = QtGui.QFileDialog.getOpenFileName(self, caption,
                                                         dir=self.default_dir,
                                                         filter=filters)
            if filepath[0]:
                tooltip = ("Value for the Z coordinate missing, please specify"
                           " it manually.")
                spec = read_specfile(filepath[0])
                # number of nodes
                nodes = "{}, {}".format(spec.xnodes.values[0],
                                        spec.ynodes.values[0])
                if hasattr(spec, "znodes"):
                    nodes += ", {}".format(spec.znodes.values[0])
                else:
#                     self.lineGridNodes.setToolTip(tooltip)
#                     self.lineGridNodes.toolTip().showText()
                    QtGui.QToolTip.showText(self.lineGridNodes.mapToGlobal(QtCore.QPoint(0,0)), tooltip)
    #QToolTip::showText( widget->mapToGlobal( QPoint( 0, 0 ) ), errorString );@
                self.lineGridNodes.setText(nodes)
                # cell size
                sizes = "{}, {}".format(spec.xsize.values[0],
                                        spec.ysize.values[0])
                if hasattr(spec, "zsize"):
                    sizes += ", {}".format(spec.zsize.values[0])
                self.lineGridSize.setText(sizes)
                # origin coordinates
                origins = "{}, {}".format(spec.xmin.values[0],
                                          spec.ymin.values[0])
                if hasattr(spec, "zmin"):
                    origins += ", {}".format(spec.zmin.values[0])
                self.lineGridOrig.setText(origins)

    def browse_simdir(self):
        """Dialog to select the directory with the simulated maps.
        Connected to the SimsPath button.

        """
        caption = "Select the directory with the homogenisation simulated maps"
        dirpath = QtGui.QFileDialog.getExistingDirectory(self, caption,
                                                         dir=self.default_dir)

        if dirpath:
            self.lineSimsPath.setText(dirpath)
            self.default_dir = dirpath
            self.set_simmaps()

    def browse_simfile(self):
        """Dialog to select simulated map files.
        Connected to the AddSim button.

        Use non native dialog in order to allow multiple selection.
        Update networks and stations lists.

        """
        caption = "Select simulated map file(s)"
        filters = "Simulated maps (*.out);;All files (*)"
        filepath = QtGui.QFileDialog.getOpenFileNames(self, caption,
                                                      dir=self.default_dir,
                                                      filter=filters)

        if filepath[0]:
            self.listSimFiles.addItems(filepath[0])
            self.default_dir = os.path.dirname(filepath[0][0])
            self.update_sim_label()

    def browse_savedir(self):
        """Dialog to select the directory where the results will be saved.
        Connected to the SavePath button.

        """
        caption = "Select the directory where the results will be saved"
        dirpath = QtGui.QFileDialog.getExistingDirectory(self, caption,
                                                         dir=self.default_dir)

        if dirpath:
            self.lineSavePath.setText(dirpath)
            self.default_dir = dirpath

    def enable_manualspec(self, toggle):
        """Enable the line edits related to the grid specifications.
        Connected to the radio button to Set manually.

        """
        self.lineGridNodes.setReadOnly(not toggle)
        self.lineGridSize.setReadOnly(not toggle)
        self.lineGridOrig.setReadOnly(not toggle)

    def remove_sims(self):
        """Remove selected simulated map files from the files list.
        Connected to the RemoveSim button

        """
        for simfile in self.listSimFiles.selectedItems():
            item = self.listSimFiles.row(simfile)
            self.listSimFiles.takeItem(item)
        self.update_sim_label()

    def set_gui_params(self):
        """Set the GUI parameters.

        """
        self.guiparams = list()
        add = self.guiparams.extend

        gp = "tools_simstats"

    def set_simmaps(self, ext="out"):
        """Find and set the simulated maps in the SimFiles list.
        Connected to the SimsPath lineEdit.

        """
        simdir = self.lineSimsPath.text()
        if not len(simdir):
            return
        elif os.path.isdir(simdir):
            simfiles = glob2.glob(os.path.join(simdir, "**/*." + ext))
            ui.pylist_to_qlist(simfiles, self.listSimFiles)
            self.update_sim_label()
        else:
            self.listSimFiles.clear()
            self.listSimFiles.addItem("Invalid directory.")

    def update_sim_label(self):
        """Update the text in the SimFiles label.

        """
        self.labelSimFiles.setText(self.sim_label + " ({} files found)".
                                   format(self.listSimFiles.count()))


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = SimStats()
    window.show()
    sys.exit(app.exec_())
