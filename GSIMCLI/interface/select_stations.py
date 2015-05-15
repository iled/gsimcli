# -*- coding: utf-8 -*-
"""
Created on 14/05/2015

@author: julio
"""
from PySide import QtGui
import os
import sys

from external_libs.pyside_dynamic import loadUi
from interface.ui_utils import pylist_to_qlist
import numpy as np
from tools.grid import PointSet


base = os.path.dirname(os.path.dirname(__file__))


class SelectStations(QtGui.QDialog):

    """Dialog to the user to select stations among the existing in a PointSet
    file.

    """

    def __init__(self, parent=None):
        """Constructor.

        """
        super(SelectStations, self).__init__(parent)
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
        self.listStations.currentItemChanged.connect(self.toggle_all)

        # spin
        self.spinCol.valueChanged.connect(self.refresh)

    def accept(self):
        """Custom accept event. Save the selected candidate stations.

        """
        self.selected = [i.text() for i in self.listStations.selectedItems()]
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
        except ValueError:
            self.pset = None
            return None
        except AttributeError:
            self.pset = None
            return None
        else:
            self.spinCol.setMaximum(self.pset.nvars)

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
        self.preview_data_file()
        self.load_data()
        self.set_list()

    def select_all(self, toggle):
        """Select all the stations in the list.
        Connected to the selectAll checkbox.

        """
        if toggle:
            self.listStations.selectAll()
        else:
            self.listStations.clearSelection()

    def set_list(self):
        """Build the list with the stations' IDs.

        """
        id_col = self.spinCol.value() - 1
        try:
            stations = np.unique(self.pset.values.ix[:, id_col])
            # stations_list = map(int, stations)
        except AttributeError:
            pass
        except KeyError:
            pass
        else:
            stations_list = map(unicode, stations.astype('int'))

            pylist_to_qlist(stations_list, self.listStations)
            self.labelFound.setText(unicode(self.listStations.count()))

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
