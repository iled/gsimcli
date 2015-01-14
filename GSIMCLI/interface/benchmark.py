# -*- coding: utf-8 -*-
"""
Created on 13/01/2015

@author: julio
"""
from PySide import QtGui, QtCore
import os
import sys

from external_libs.pyside_dynamic import loadUi
from interface.ui_utils import hide
import tools.scores as scores


base = os.path.dirname(os.path.dirname(__file__))


class Scores(QtGui.QWidget):
    """Interface to the calculation of benchmark scores of a homogenisation
    process.

    """
    def __init__(self, parent=None):
        """Constructor

        """
        super(Scores, self).__init__(parent)
        # load ui file
        # QtGui.QMainWindow.__init__(self, parent)
        loadUi(os.path.join(base, "interface", "tools.benchmark.ui"), self)

        # buttons
        self.buttonCalculate.clicked.connect(self.calculate_scores)

        # check boxes
        self.checkSaveCost.toggled.connect(self.enable_save_cost)
        self.groupNetwork.toggled.connect(self.enable_scores_network)
        self.groupStation.toggled.connect(self.enable_scores_station)

        # table
        self.tableResults.cellChanged.connect(self.add_rows_auto)
        self.tableResults.cellDoubleClicked.connect(self.browse_file)
        self.set_table_menu()

        # hidden widgets by default
        hide([self.labelSaveCost, self.lineSaveCost,
              self.buttonSaveCost,
              ])

    def add_rows_auto(self, row, col):
        """Automatically add a new row after entering data in the last row.
        Connected to the tableResults widget.

        """
        rows = self.tableResults.rowCount()
        if row == rows - 1:
            self.tableResults.insertRow(row + 1)

    def browse_file(self, row, col):
        """Interface to browse a file.
        Connected to the tableResults widget.

        """
        # open results file
        if col == 0:
            target = "homogenisation results"
        # open keys file
        elif col == 2:
            target = "keys"
        # otherwise ignore
        else:
            return

        # open file
        if col in [0, 2]:
            caption = "Select {} file".format(target)
            filepath = QtGui.QFileDialog.getOpenFileName(self, caption)

            if filepath[0]:
                item = QtGui.QTableWidgetItem(filepath[0])
                self.tableResults.setItem(row, col, item)

    def browse_file_action(self):
        """Wrapper to call browse_file from the tableResults' context menu.

        """
        row = self.tableResults.currentRow()
        col = self.tableResults.currentColumn()
        self.browse_file(row, col)

    def calculate_scores(self):
        """Gather the necessary arguments and call the function to calculate
        the benchmark scores.
        Connected to the buttonCalculate widget.

        """
        over_network = self.groupNetwork.isChecked()
        over_station = self.groupStation.isChecked()

        results, network_ids, keys = self.extract_results()

        kwargs = {
              'gsimcli_results': results,
              'no_data': self.spinNoData.value(),
              'network_ids': network_ids,
              'keys': keys,
              'costhome_path': self.lineSaveCost.text(),
              'costhome_save': self.checkSaveCost.isChecked(),
              'orig_path': self.lineOrig.text(),
              'inho_path': self.lineInho.text(),
              'yearly_sum': self.checkAverageYearly.isChecked(),
              'over_network': self.groupNetwork.isChecked(),
              'over_station': self.groupStation.isChecked(),
              'skip_missing': self.checkSkipMissing.isChecked(),
              'skip_outlier': self.checkSkipOutlier.isChecked(),
                }
        results = scores.gsimcli_improvement(**kwargs)

        if over_network:
            self.lineNetworkCRMSE.setText(str(results[0][0]))
            self.lineNetworkImprov.setText(str(results[2][0]))
        if over_station:
            self.lineStationCRMSE.setText(str(results[0][int(over_network)]))
            self.lineStationImprov.setText(str(results[2][int(over_network)]))

    def enable_save_cost(self, toggle):
        """Hide/unhide widgets related to the SaveCosts checkbox: label, line
        and button.
        Connected to the SaveCosts checkbox.

        """
        self.labelSaveCost.setVisible(toggle)
        self.lineSaveCost.setVisible(toggle)
        self.buttonSaveCost.setVisible(toggle)

    def enable_scores_network(self, toggle):
        """Toggle widgets related to the network scores group: crmse and
        improvement labels and lines.
        Connected to the groupNetwork checkbox.

        """
        self.labelNetworkCRMSE.setEnabled(toggle)
        self.lineNetworkCRMSE.setEnabled(toggle)
        self.labelNetworkImprov.setEnabled(toggle)
        self.lineNetworkImprov.setEnabled(toggle)
        self.checkSkipMissing.setEnabled(toggle)

    def enable_scores_station(self, toggle):
        """Toggle widgets related to the station scores group: crmse and
        improvement labels and lines.
        Connected to the groupStation checkbox.

        """
        self.labelStationCRMSE.setEnabled(toggle)
        self.lineStationCRMSE.setEnabled(toggle)
        self.labelStationImprov.setEnabled(toggle)
        self.lineStationImprov.setEnabled(toggle)

    def extract_results(self):
        """Extract the results files, network ids and keys files from the
        tableResults widget.

        """
        results = list()
        network_ids = list()
        keys = list()

        for row in xrange(self.tableResults.rowCount()):
            item = self.tableResults.item
            res = item(row, 0)
            nid = item(row, 1)
            key = item(row, 2)
            if res and res.text():
                results.append(res.text())
            if nid and nid.text():
                network_ids.append(nid.text())
            if key and key.text():
                keys.append(key.text())

        return results, network_ids, keys

    def remove_rows(self):
        """Remove the selected rows from the table.
        Connected to the tableResults context menu.

        """
        indexes = self.tableResults.selectedIndexes()
        rows = sorted(set([index.row() for index in indexes]))
        for n, row in enumerate(rows):
            self.tableResults.removeRow(row - n)

        # keep one row
        if not self.tableResults.rowCount():
            self.tableResults.insertRow(0)

    def set_table_menu(self):
        """Set up the context menu of the tableResults widget, in its cells
        and vertical header.

        """
        # set up actions
        browse_file = QtGui.QAction("Browse file", self)
        del_row = QtGui.QAction("Remove selected row(s)", self)
        browse_file.triggered.connect(self.browse_file_action)
        del_row.triggered.connect(self.remove_rows)
        # cells
        self.tableResults.addAction(browse_file)
        self.tableResults.addAction(del_row)
        # vertical header
        vheader = self.tableResults.verticalHeader()
        vheader.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        vheader.addAction(del_row)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Scores()
    # on exit
    window.show()
    sys.exit(app.exec_())
