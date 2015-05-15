# -*- coding: utf-8 -*-
"""
Created on 05/03/2015

@author: julio
"""
from PySide import QtGui
import glob2
import os
import sys

from external_libs.pyside_dynamic import loadUi
from interface.select_stations import SelectStations
import interface.ui_utils as ui
from tools.grid import GridFiles
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
        self.buttonCalculate.clicked.connect(self.calculate_stats)
        self.buttonSimsPath.clicked.connect(self.browse_simdir)
        self.buttonSavePath.clicked.connect(self.browse_savedir)
        self.buttonAddSim.clicked.connect(self.browse_simfile)
        self.buttonRemoveSim.clicked.connect(self.remove_sims)

        # check boxes
        self.checkPercentile.toggled.connect(self.enable_percentile)

        # label
        self.sim_label = self.labelSimFiles.text()

        # line
        self.lineSimsPath.editingFinished.connect(self.set_simmaps)

        # radio
        self.radioGridManual.toggled.connect(self.enable_manualspec)
        self.radioGridFile.clicked.connect(self.browse_gridfile)
        self.radioGridSame.toggled.connect(self.set_samegrid)
        self.radioCandidates.clicked.connect(self.select_stations)
        self.full_grid = self.radioFullGrid.isChecked()
        self.radioFullGrid.toggled.connect(self.enable_full_grid)
        self.radioRadius.toggled.connect(self.enable_radius)

        # hidden widgets by default
        ui.hide([self.progressBar])

    def browse_gridfile(self):
        """Dialog to select the file with the grid specifications.
        Connected to the GridFile radio button.

        """
        if self.radioGridFile.isChecked():
            caption = "Select the grid specifications file"
            filters = "Grid spec (*grid*.csv);;CSV files (*.csv)"
            filepath = QtGui.QFileDialog.getOpenFileName(self, caption,
                                                         dir=self.default_dir,
                                                         filter=filters)
            if filepath[0]:
                self.default_dir = os.path.dirname(filepath[0])
                spec = read_specfile(filepath[0])
                missing = []
                # number of nodes
                nodes = [spec.xnodes.values[0], spec.ynodes.values[0]]
                if hasattr(spec, "znodes"):
                    nodes.append(spec.znodes.values[0])
                    missing.append(False)
                else:
                    missing.append(True)
                # cell size
                sizes = [spec.xsize.values[0], spec.ysize.values[0]]
                if hasattr(spec, "zsize"):
                    sizes.append(spec.zsize.values[0])
                    missing.append(False)
                else:
                    missing.append(True)
                # origin coordinates
                origins = [spec.xmin.values[0], spec.ymin.values[0]]
                if hasattr(spec, "zmin"):
                    origins.append(spec.zmin.values[0])
                    missing.append(False)
                else:
                    missing.append(True)

                if any(missing):
                    opt = self.show_msgbox_missingz()
                    if opt == QtGui.QMessageBox.Ok:
                        self.radioGridManual.setChecked(True)
                        save = True
                    elif opt == QtGui.QMessageBox.Cancel:
                        save = False
                else:
                    save = True

                if save:
                    self.save_gridspecs(nodes, sizes, origins)

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

    def calculate_stats(self):
        """Calculate the selected stats of the listed simulated maps.
        Connected to the calculate button.

        """
        # open all grid files
        kwargs = {
            'files_list': ui.qlist_to_pylist(self.listSimFiles),
            'dims': map(int, self.lineGridNodes.text().split(", ")),
            'first_coord': map(float, self.lineGridOrig.text().split(", ")),
            'cells_size': map(float, self.lineGridSize.text().split(", ")),
            'no_data': float(self.spinNoData.value()),
            'headerin': self.checkHeader.isChecked() * 3,
            'only_paths': True,
        }
        self.grids = GridFiles()
        self.grids.open_files(**kwargs)
        # calculate stats
        kwargs = self.fetch_stats()
        if self.full_grid:
            self.results = self.grids.stats(**kwargs)
        else:
            # TODO: missing arguments
            self.results = self.grids.stats_area(loc, tol, save)
        self.save_results()

    def enable_full_grid(self, toggle):
        """Save the setting to use the complete grid to calculate the chosen
        statistics.
        Connected to the fullgrid radio button.

        """
        self.full_grid = toggle

    def enable_manualspec(self, toggle):
        """Enable the line edits related to the grid specifications.
        Connected to the radio button to Set manually.

        """
        self.lineGridNodes.setReadOnly(not toggle)
        self.lineGridSize.setReadOnly(not toggle)
        self.lineGridOrig.setReadOnly(not toggle)

    def enable_percentile(self, toggle):
        """Enable/disable the spinbox related to the percentile.
        Connected to the percentile checkbox.

        """
        self.spinPercentile.setEnabled(toggle)

    def enable_radius(self, toggle):
        """Enable/disable the spinbox related to the option to calculate
        the statistics in a radius around the candidate stations.
        Connected to the radius radio button.

        """
        self.spinRadius.setEnabled(toggle)

    def fetch_stats(self):
        """Retrieve which stats should be calculated. They are saved in the
        form of keyword arguments, according to the stats function in the
        grid module.

        """
        self.stats_kwargs = {
            'lmean': self.checkMean.isChecked(),
            'lmed': self.checkMedian.isChecked(),
            'lskew': self.checkSkewness.isChecked(),
            'lvar': self.checkVariance.isChecked(),
            'lstd': self.checkSD.isChecked(),
            'lcoefvar': self.checkCoefVar.isChecked(),
            'lperc': self.checkPercentile.isChecked(),
            'p': self.spinPercentile.value(),
        }
        return self.stats_kwargs

    def remove_sims(self):
        """Remove selected simulated map files from the files list.
        Connected to the RemoveSim button

        """
        for simfile in self.listSimFiles.selectedItems():
            item = self.listSimFiles.row(simfile)
            self.listSimFiles.takeItem(item)
        self.update_sim_label()

    def save_gridspecs(self, nodes, sizes, origins):
        """Update the widgets with the grid specifications.

        """
        self.lineGridNodes.setText(", ".join(map(str, nodes)))
        self.lineGridSize.setText(", ".join(map(str, sizes)))
        self.lineGridOrig.setText(", ".join(map(str, origins)))

    def save_results(self):
        """Save the resulting grids with the calculated statistics.

        """
        savepath = self.lineSavePath.text()
        for key, value in self.results.iteritems():
            value.save(os.path.join(savepath, key + ".out"), key)

    def select_stations(self):
        """Pop up the dialog to select stations from a PointSet file.
        Connected to the candidates radio button.

        """
        self.select_dialog = SelectStations(self)
        self.select_dialog.accepted.connect(self.set_stations)
        self.select_dialog.open()

    def set_gui_params(self):
        """Set the GUI parameters.

        """
        self.guiparams = list()
        add = self.guiparams.extend

        gp = "tools_simstats"

    def set_samegrid(self, toggle):
        """Use the grid specifications that were previously set in the
        simulation settings.
        Connected to the GridSame radio button.

        """
        grid = self.parent()
        if toggle and grid is not None:
            nodes = (grid.SG_spinXXNodes.value(),
                     grid.SG_spinYYNodes.value(),
                     grid.SG_spinZZNodes.value())
            sizes = (grid.SG_spinXXSize.value(),
                     grid.SG_spinYYSize.value(),
                     grid.SG_spinZZSize.value())
            origins = (grid.SG_spinXXOrig.value(),
                       grid.SG_spinYYOrig.value(),
                       grid.SG_spinZZOrig.value())
            self.save_gridspecs(nodes, sizes, origins)
            self.checkHeader.setChecked(grid.DL_checkHeader.isChecked())
            self.spinNoData.setValue(grid.DL_spinNoData.value())

    def set_simmaps(self, ext="out"):
        """Find and set the simulated maps in the SimFiles list.
        Connected to the SimsPath lineEdit.

        """
        simdir = self.lineSimsPath.text()
        if not len(simdir):
            return None
        elif os.path.isdir(simdir):
            simfiles = glob2.glob(os.path.join(simdir, "**/*." + ext))
            ui.pylist_to_qlist(simfiles, self.listSimFiles)
            self.update_sim_label()
        else:
            self.listSimFiles.clear()
            self.listSimFiles.addItem("Invalid directory.")

    def set_stations(self):
        """Save the selected candidate stations.
        Connected to the select dialog.

        """
        self.stations = self.select_dialog.get_selected()

    def show_msgbox_missingz(self):
        msgbox = QtGui.QMessageBox(self)
        msgbox.setText("At least one value for the Z coordinate is missing.")
        msgbox.setInformativeText("Do you want to specify it manually?")
        msgbox.setStandardButtons(msgbox.Ok | msgbox.Cancel)
        msgbox.setDefaultButton(msgbox.Ok)
        msgbox.setWindowTitle("Specify missing value manually?")
        msgbox.setIcon(msgbox.Warning)
        return msgbox.exec_()

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
