# -*- coding: utf-8 -*-
"""
Created on 14/05/2015

@author: julio
"""
from PySide import QtGui, QtCore
from collections import namedtuple
import os
import sys
import warnings

from external_libs.pyside_dynamic import loadUi
from interface.checktable import TableModel, TableView
# from interface.ui_utils import pylist_to_qlist
import numpy as np
import pandas as pd
from tools.grid import PointSet


base = os.path.dirname(os.path.dirname(__file__))
_selected_stations = namedtuple('Stations', ['ID', 'X', 'Y'])


class SelectStations(QtGui.QDialog):

    """Dialog to the user to select stations among the existing in a PointSet
    file.

    """

    def __init__(self, parent=None):
        """Constructor.

        """
        super(SelectStations, self).__init__(parent)
        self.parent = parent
        # load ui file
        loadUi(os.path.join(base, "interface", "select_stations.ui"), self)
        if parent is not None:
            pos = self.mapToGlobal(parent.window().frameGeometry().center())
            self.move(pos.x() - self.width() / 2, pos.y() - self.height() / 2)

        if hasattr(self.parent, "default_dir"):
            self.default_dir = self.parent.default_dir
        else:
            self.default_dir = os.path.expanduser('~/')

        # buttons
        self.buttonBrowse.clicked.connect(self.browse_stations)

        # checkbox
        self.header = self.checkHeader.isChecked()
        self.checkHeader.toggled.connect(self.enable_header)
        self.checkAll.toggled.connect(self.select_all)

        # line
        self.linePath.editingFinished.connect(self.preview_data_file)
        self.linePath.editingFinished.connect(self.refresh)

        # list
        self.tableStations.currentItemChanged.connect(self.toggle_all)

        # spin
        self.spinCol.valueChanged.connect(self.refresh)

        # table, only if non existent
        if not hasattr(self, 'tableStationsModel'):
            self.create_table()

    def accept(self):
        """Custom accept event. Save the selected candidate stations.

        """
        self.stations = self.tableStationsModel.get_key('Station ID', True)
        self.x = self.tableStationsModel.get_key('X', True)
        self.y = self.tableStationsModel.get_key('Y', True)
        self.n_selected = self.stations.shape[0]
        QtGui.QDialog.accept(self)

    def browse_stations(self):
        """Dialog to select the file with the stations.
        Connected to the browse pushbutton.

        """
        caption = "Select the stations file"
        filters = "PointSet files (*.prn *.txt);;All files (*)"
        filepath = QtGui.QFileDialog.getOpenFileName(self, caption,
                                                     dir=self.default_dir,
                                                     filter=filters)
        if filepath[0]:
            self.default_dir = os.path.dirname(filepath[0])
            self.linePath.setText(filepath[0])
            self.preview_data_file()
            self.guess_column()
            self.refresh()

    def create_table(self):
        """Set up the table model and view.

        """
        self.tableStationsModel = TableModel(3, self, auto_row=False)
        self.tableStationsView = TableView(3, self)
        # initialise the table
        columns = ['Station ID', 'X', 'Y', 'Use']
        table = pd.DataFrame(columns=columns)
        self.tableStationsModel.update(table)
        self.tableStations.close()
        view = self.tableStationsView
        view.setModel(self.tableStationsModel)
        view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.layout().insertWidget(5, self.tableStationsView)
        self.hheader = self.tableStationsView.horizontalHeader()
        self.hheader.setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.hheader.setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.hheader.setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.hheader.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

    def enable_header(self, toggle):
        """Connected to the header checkbox.

        """
        self.header = toggle
        self.guess_column()
        self.refresh()

    def get_selected(self):
        """Return the selected stations.

        """
        return _selected_stations(self.stations, self.x, self.y)

    def guess_column(self):
        """Try to set the IDs column based if the file has a header. It will
        look for the keyword 'station'.

        """
        if self.header:
            try:
                id_col = self.pset.varnames.index('station')
            except ValueError:
                return None
            except AttributeError:
                return None
            else:
                self.spinCol.setValue(id_col + 1)
        else:
            return None

    def load_data(self):
        """Load the PointSet data file.

        """
        try:
            self.pset = PointSet()
            self.pset.load(self.path, header=self.header)
        except ValueError, e:
            # error loading PointSet, perhaps the header information is wrong
            self.checkHeader.toggle()
            pos = self.checkHeader.mapToGlobal(QtCore.QPoint(0, 0))
            text = ("Header should be like this, otherwise an error occurs "
                    "while loading the PointSet:\n" + unicode(e))
            QtGui.QToolTip.showText(pos, text, self)
        except AttributeError:
            self.pset = None
            return None
        else:
            self.spinCol.setMaximum(self.pset.nvars)

    def locations(self, stations=None):
        """Retrieve the coordinates of a given list of stations' ID's. If no
        list is given, try to fetch the previously selected stations.

        DEPRECATED
        """
        if stations is None and hasattr(self, "selected"):
            stations = self.selected
        locs = {}
        idcol = self.spinCol.value() - 1
        vals = self.pset.values
        for station in stations:
            st = vals[vals.ix[:, idcol] == station]
            # assuming X and Y are the first 2 columns
            locs[station] = st.iloc[0, :2]
        self.locs = locs

    def preview_data_file(self):
        """Set the QPlainTextEdit to preview the first 10 lines of a data file.
        Connected to the data path line edit.

        """
        filepath = self.linePath.text()
        if not len(filepath):
            return None
        try:
            with open(filepath, 'r+') as datafile:
                lines = str()
                for i in xrange(10):  # @UnusedVariable
                    lines += datafile.readline()
        except IOError:
            lines = "Error loading file: " + filepath
        self.plainPreview.setPlainText(lines)
        self.path = filepath

    def refresh(self):
        """Call the required methods to refresh the file preview and the
        stations list.

        """
        self.tableStationsModel.clear()
        self.preview_data_file()
        self.load_data()
        self.set_list()

    def select_all(self, toggle):
        """Select all the stations in the list.
        Connected to the selectAll checkbox.

        """
        for row in range(self.tableStationsModel.rowCount()):
            index = self.tableStationsModel.index(row, 3)
            self.tableStationsModel.setData(index, toggle)

    def set_list(self):
        """Build the list with the stations' IDs.

        """
        id_col = self.spinCol.value() - 1
        try:
            stations = np.unique(self.pset.values.ix[:, id_col])
            # stations_list = map(int, stations)
        except AttributeError:
            warnings.warn('the point set was not correctly loaded yet.')
        except KeyError:
            warnings.warn('the ID column may be wrong.')
        else:
            # stations_list = map(unicode, stations.astype('int'))
            self.locations(stations)
            for station in stations:
                x, y = self.locs[station]
                item = [station, x, y, False]
                self.tableStationsModel.addItem(item)

            self.labelFound.setText(
                unicode(self.tableStationsModel.rowCount()))

    def toggle_all(self, cur, prev):
        """Uncheck the selectAll checkbox if any station is unselected.
        Connected to the stations list.

        """
        if self.checkAll.isChecked():
            self.checkAll.blockSignals(True)
            self.checkAll.setChecked(False)
            self.checkAll.blockSignals(False)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    dialog = SelectStations()
    dialog.show()
    sys.exit(app.exec_())
