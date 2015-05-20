# -*- coding: utf-8 -*-
"""
Created on 14/05/2015

@author: julio
"""
from PySide import QtGui, QtCore
import os
import sys

from external_libs.pyside_dynamic import loadUi
from interface.checktable import TableModel, TableView
# from interface.ui_utils import pylist_to_qlist
import numpy as np
import pandas as pd
from tools.grid import PointSet
from PyQt4.Qt import QPoint


base = os.path.dirname(os.path.dirname(__file__))


# class TableModel(QtCore.QAbstractTableModel):
#     """Table model with 3 columns and a variable number of rows. The columns
#     are : `Station ID` number; `X` coordinate; and `Y` coordinate.
#
#     """
#
#     def __init__(self, parent=None):
#         """Constructor.
#
#         parent : QObject, optional
#             Parent of the model.
#
#         """
#         super(TableModel, self).__init__(parent)
#         self.table = None
#
#     def addItem(self, item):
#         """Append a row to the table.
#
#         item : array_like
#             Row to be inserted after the last row in the table.
#
#         """
#         count = self.rowCount()
#         self.beginInsertRows(QtCore.QModelIndex(), count, count)
#         self.table.loc[count] = item
#         self.endInsertRows()
#
#     def columnCount(self, parent=QtCore.QModelIndex()):
#         """Return the number of columns in the table.
#
#         """
#         if self.table is not None:
#             return self.table.shape[1]
#
#     def data(self, index, role=QtCore.Qt.DisplayRole):
#         """Return the value in the given index of the table.
#
#         """
#         if role == QtCore.Qt.DisplayRole:
#             i = index.row()
#             j = index.column()
#             return self.table.iloc[i, j]
#
#     def get_row(self, row):
#         """Return the data in the given `row` number.
#
#         Parameters
#         ----------
#         row : int
#             Row number
#
#         """
#         return self.table.loc[row]
#
#     def setData(self, index, value, role=QtCore.Qt.EditRole):
#         """Set the `role` data for the item at `index` to `value`.
#
#         """
#         if role == QtCore.Qt.EditRole:
#             j = index.row()
#             j = index.column()
#             self.table.iloc[i, j] = value
#             self.dataChanged.emit(index, index)
#             return True
#         return False
#
#
# class TableView(QtGui.QTableView):
#     """A table view to show and manage the data in the table model with three
#     columns.
#
#     The table has alternating row colours.
#
#     """
#     def __init__(self, parent=None):
#         """Constructor

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

        self.load_settings()

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

        # table
        # model and view
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

    def accept(self):
        """Custom accept event. Save the selected candidate stations.

        """
        self.selected = [i.text() for i in self.tableStations.selectedItems()]
        self.locations()
        self.save_settings()
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

    def enable_header(self, toggle):
        """Connected to the header checkbox.

        """
        self.header = toggle
        self.guess_column()
        self.refresh()

    def get_selected(self):
        """Return the selected stations.

        """
        return self.selected

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

    def load_settings(self):
        """Load settings from a dictionary.

        FIXME: not working
        """
        if hasattr(self, "settings"):
            s = self.settings
            self.linePath.setText(s['path'])
            self.checkHeader.setChecked(s['header'])
            self.spinCol.setValue(s['idcol'])
            self.checkAll.setChecked(s['all'])
            self.tableStations.setSelectionModel(s[''])

    def locations(self, stations=None):
        """Retrieve the coordinates of a given list of stations' ID's. If no
        list is given, try to fetch the previously selected stations.

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
        # print locs

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

    def save_settings(self):
        """Use a dictionary to save current settings.

        FIXME: not working
        """
        if self.parent:
            settings = {
                'path': self.linePath.text(),
                'header': self.checkHeader.isChecked(),
                'idcol': self.spinCol.value(),
                'all': self.checkAll.isChecked(),
                'selected': self.tableStations.selectionModel()
            }
            self.parent.select_stations_settings = settings

    def select_all(self, toggle):
        """Select all the stations in the list.
        Connected to the selectAll checkbox.

        """
#         if toggle:
#             self.tableStations.selectAll()
#         else:
#             self.tableStations.clearSelection()
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
            # the point set was not correctly loaded yet
            pass
        except KeyError:
            # the ID column must be wrong
            pass
        else:
            # stations_list = map(unicode, stations.astype('int'))

            # pylist_to_qlist(stations_list, self.tableStations)
            self.locations(stations)
            #item = QtGui.QTableWidgetItem
            for i, station in enumerate(stations):
                x, y = self.locs[station]
#                 self.tableStations.insertRow(i)
#                 self.tableStations.setItem(i, 0, item(station))
#                 self.tableStations.setItem(i, 1, item(x))
#                 self.tableStations.setItem(i, 2, item(y))
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
