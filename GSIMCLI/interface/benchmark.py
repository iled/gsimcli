# -*- coding: utf-8 -*-
"""
Created on 13/01/2015

@author: julio
"""
from PySide import QtGui, QtCore
import os
import sys

from external_libs.pyside_dynamic import loadUi
import interface.ui_utils as ui
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

        # set params
        self.set_gui_params()

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
        ui.hide([self.labelSaveCost, self.lineSaveCost, self.buttonSaveCost,
                 self.progressBar
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
        self.show_status(True)
        self.extract_results()
        self.set_progress_max()

        kwargs = {
              'gsimcli_results': self.gsimcli_results,
              'no_data': self.spinNoData.value(),
              'network_ids': self.network_ids,
              'keys': self.keys,
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

        # set up the job
        job = scores.gsimcli_improvement
        updater = scores.update.progress
        self.office = ui.Office(self, job, updater=updater, **kwargs)
        # self.office.worker.time_elapsed.connect(self.set_time)
        self.office.worker.update_progress.connect(self.set_progress)
        self.office.finished.connect(self.print_results)
        self.office.start()

    def count_stations(self):
        """Try to find the total number of stations in the submission from the
        keys files.

        """
        rows = self.tableResults.rowCount()
        keys = list()
        for row in xrange(rows):
            item = self.tableResults.item(row, 2)
            if item is not None:
                keys.append(item.text())

        stations = 0
        for key in keys:
            stations += sum(1 for line in open(key)) - 1  # @UnusedVariable

        return stations

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

        self.gsimcli_results = results
        self.network_ids = network_ids
        self.keys = keys

    def print_results(self):
        over_network = self.groupNetwork.isChecked()
        over_station = self.groupStation.isChecked()
        self.results = self.office.results

        if over_network:
            network_crmse = str(self.results[0][0])
            network_improvement = str(self.results[2][0])
            self.lineNetworkCRMSE.setText(network_crmse)
            self.lineNetworkImprov.setText(network_improvement)
        if over_station:
            station_crmse = str(self.results[0][int(over_network)])
            station_improvement = str(self.results[2][int(over_network)])
            self.lineStationCRMSE.setText(station_crmse)
            self.lineStationImprov.setText(station_improvement)

        self.show_status(False)

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

    def set_gui_params(self):
        self.guiparams = list()
        add = self.guiparams.extend

        gp = "tools_benchmark"
        table = ui.GuiParam("table_results", self.tableResults, gp)
        no_data = ui.GuiParam("no_data", self.spinNoData, gp)
        orig = ui.GuiParam("orig_path", self.lineOrig, gp)
        inho = ui.GuiParam("inho_path", self.lineInho, gp)
        save_cost = ui.GuiParam("save_cost", self.checkSaveCost, gp)
        cost_path = ui.GuiParam("cost_path", self.lineSaveCost, gp, save_cost)
        over_station = ui.GuiParam("over_station", self.groupStation, gp)
        over_network = ui.GuiParam("over_network", self.groupNetwork, gp)
        yearly_sum = ui.GuiParam("yearly_sum", self.checkAverageYearly, gp)
        skip_missing = ui.GuiParam("skip_missing", self.checkSkipMissing, gp,
                                   over_network)
        skip_outlier = ui.GuiParam("skip_outlier", self.checkSkipOutlier, gp)

        add([table, no_data, orig, inho, save_cost, cost_path, over_station,
             over_network, yearly_sum, skip_missing, skip_outlier])

    def set_progress(self, current):
        progress = 100 * current / self.total
        self.progressBar.setValue(progress)

    def set_progress_max(self):
        over_network = self.groupNetwork.isChecked()
        over_station = self.groupStation.isChecked()

        networks = len(self.gsimcli_results)
        stations = self.count_stations()
        total = networks + 1
        if over_network:
            total += networks * 2
        if over_station:
            total += stations * 2

        self.total = total

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

    def show_status(self, toggle):
        self.progressBar.setValue(0)
        self.progressBar.setVisible(toggle)
        self.buttonCalculate.setEnabled(not toggle)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Scores()
    # on exit
    window.show()
    sys.exit(app.exec_())