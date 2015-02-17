# -*- coding: utf-8 -*-
"""
Created on 13/01/2015

@author: julio
"""
from PySide import QtGui, QtCore
import glob2
import os
import sys

from external_libs.pyside_dynamic import loadUi
from external_libs.ui import CheckBoxDelegate
import interface.ui_utils as ui
import pandas as pd
import tools.scores as scores
from tools.utils import path_up


base = os.path.dirname(os.path.dirname(__file__))


class TableModel(QtCore.QAbstractTableModel):
    dataChanged = QtCore.Signal(QtCore.QModelIndex, QtCore.QModelIndex)

    def __init__(self, checkbox_col, parent=None):
        super(TableModel, self).__init__(parent)
        self.table = None
        self.header = None
        self.checkbox_col = checkbox_col

    def addItem(self, item):
        count = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), count, count)
        self.table.loc[count] = item
        self.endInsertRows()

    def columnCount(self, parent=QtCore.QModelIndex()):
        if self.table is not None:
            return self.table.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            i = index.row()
            j = index.column()
            if j == self.checkbox_col:
                return self.table.iloc[i, j]
            else:
                return unicode(self.table.iloc[i, j])

    def flags(self, index):
        if index.column() == self.checkbox_col:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled  # @IgnorePep8

    def headerData(self, col, orientation, role):
        if (orientation == QtCore.Qt.Horizontal and
                role == QtCore.Qt.DisplayRole):
            return str(self.header[col])

    def getKey(self, key, filter_selected=False):
        if filter_selected:
            values = self.table.query(self.checkbox_key)[key]
        else:
            values = self.table[key]

        return values

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        if row < 0 or row > self.rowCount():
            return False

        self.beginRemoveRows(parent, row, row)
        self.table.drop(row, axis=0, inplace=True)
        self.table.reset_index(drop=True, inplace=True)
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        if self.table is not None:
            return self.table.shape[0]

    def setChecked(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            self.table.iloc[index.row(), self.checkbox_col] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            i = index.row()
            j = index.column()
            self.table.iloc[i, j] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setHeaderData(self, section, value, orientation=QtCore.Qt.Horizontal,
                      role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole and orientation == QtCore.Qt.Horizontal:
            self.header[section] = value
            self.headerDataChanged.emit(orientation, section, section)

    def update(self, data_in):
        self.table = data_in
        headers = data_in.columns
        self.header = [str(field) for field in headers]
        self.checkbox_key = self.table.columns[self.checkbox_col]


class TableView(QtGui.QTableView):
    def __init__(self, checkbox_col, parent=None):
        super(TableView, self).__init__(parent)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        act = QtGui.QAction("Delete selected row(s)", self)
        act.triggered.connect(self.onTriggered)
        self.addAction(act)
        self.setItemDelegateForColumn(checkbox_col, CheckBoxDelegate(self))

    def onTriggered(self):
        self.model().removeRows(self.currentIndex().row(), 1)
        if self.model().rowCount() < 1:
            self.model().addItem(['', '', '', True])


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
        if hasattr(self.parent, "default_dir"):
            self.default_dir = self.parent.default_dir
        else:
            self.default_dir = os.path.expanduser('~/')

        # buttons
        self.buttonCalculate.clicked.connect(self.calculate_scores)
        self.buttonOrig.clicked.connect(self.browse_folder)
        self.buttonInho.clicked.connect(self.browse_folder)
        self.buttonSaveCost.clicked.connect(self.browse_folder)
        self.buttonSaveResults.clicked.connect(self.save_results)

        # check boxes
        self.checkSaveCost.toggled.connect(self.enable_save_cost)
        self.groupNetwork.toggled.connect(self.enable_scores_network)
        self.groupStation.toggled.connect(self.enable_scores_station)
        self.checkUseAll.toggled.connect(self.set_use_all)

        # combo boxes
        self.comboResolution.currentIndexChanged.connect(self.time_resolution)
        self.comboFormat.currentIndexChanged.connect(self.file_format)

        # table
        self.tableResultsModel = TableModel(3, self)
        self.tableResultsView = TableView(3, self)
        columns = ['Results file', 'Network ID', 'Keys file', 'Use']
        table = pd.DataFrame(index=range(5), columns=columns)
        table.fillna('', inplace=True)
        table['Use'] = True
        self.tableResultsModel.update(table)
        self.tableResults.close()
        self.tableResultsView.setModel(self.tableResultsModel)
        self.layout().insertWidget(3, self.tableResultsView)
        self.hheader = self.tableResultsView.horizontalHeader()
        self.tableResultsModel.dataChanged.connect(self.add_rows_auto)
        self.tableResultsView.doubleClicked.connect(self.browse_cell)
        # self.set_table_menu()
        self.hheader.setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.hheader.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        self.hheader.setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.hheader.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

        # hidden widgets by default
        ui.hide([self.labelSaveCost, self.lineSaveCost, self.buttonSaveCost,
                 self.progressBar
                 ])

        self.time_resolution()

    def add_rows_auto(self, index):
        """Automatically add a new row after entering data in the last row.
        Connected to the tableResults Model.

        """
        row = index.row()
        rows = self.tableResultsModel.rowCount()
        row_content = self.tableResultsModel.table.values[row, :-1]
        if row == rows - 1 and all(row_content):
            self.tableResultsModel.addItem(['', '', '', True])

    def browse_cell(self, index):
        col = index.column()
        if self.resolution == "yearly" or col != 0:
            self.browse_file(index)
        elif self.resolution == "monthly":
            self.browse_dir(index)

    def browse_dir(self, index):
        caption = "Select homogenisation results directory"
        filepath = QtGui.QFileDialog.getExistingDirectory(self, caption,
                                                          dir=self.default_dir)

        if filepath:
            self.tableResultsModel.setData(index, filepath)
            self.default_dir = filepath

    def browse_file(self, index):
        """Interface to browse a file.
        Connected to the tableResults Model.

        """
        col = index.column()
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
            filepath = QtGui.QFileDialog.getOpenFileName(self, caption,
                                                         dir=self.default_dir)

            if filepath[0]:
                self.tableResultsModel.setData(index, filepath[0])
                self.default_dir = os.path.dirname(filepath[0])

    def browse_file_action(self):
        """Wrapper to call browse_file from the tableResults' context menu.

        """
        index = self.tableResultsView.currentIndex()
        row = index.row()
        col = index.column()
        self.browse_file(row, col)

    def browse_folder(self):
        """Interface to browse a folder.
        Connected to the browse buttons of: orig data; inho data; cost-home
        files directory.

        """
        who = self.sender().objectName().lower()
        if "orig" in who:
            what = "with the original data (separated by networks)"
            target = self.lineOrig
        elif "inho" in who:
            what = "with the inhomogenous data (separated by networks)"
            target = self.lineInho
        elif "savecost" in who:
            what = "to save the converted files"
            target = self.lineSaveCost

        caption = "Select the directory {}".format(what)
        path = QtGui.QFileDialog.getExistingDirectory(self, caption,
                                                      dir=self.default_dir)

        if path:
            target.setText(path)
            self.default_dir = os.path.abspath(path)

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
              'keys_path': self.keys,
              'costhome_path': self.lineSaveCost.text(),
              'orig_path': self.lineOrig.text(),
              'inho_path': self.lineInho.text(),
              'yearly': self.resolution == 'yearly',
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
#         rows = self.tableResultsModel.rowCount()
#         keys = list()
#         for row in xrange(rows):
#             item = self.tableResults.item(row, 2)
#             if item is not None:
#                 keys.append(item.text())

        keys = self.tableResultsModel.getKey("Keys file")

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
        tableResults Model.

        """
#         results = list()
#         network_ids = list()
#         keys = list()
#
#         for row in xrange(self.tableResults.rowCount()):
#             item = self.tableResults.item
#             res = item(row, 0)
#             nid = item(row, 1)
#             key = item(row, 2)
#             if res and res.text():
#                 results.append(res.text())
#             if nid and nid.text():
#                 network_ids.append(nid.text())
#             if key and key.text():
#                 keys.append(key.text())

        results = self.tableResultsModel.getKey('Results file', True)
        network_ids = self.tableResultsModel.getKey('Network ID', True)
        keys = self.tableResultsModel.getKey('Keys file', True)

        if self.resolution == "yearly":
            gsimcli_results = results
        elif self.resolution == "monthly":
            networks = list()
            for network in results:
                networks.append(self.find_results(network))
            gsimcli_results = networks
        self.gsimcli_results = dict(zip(network_ids, gsimcli_results))
        self.network_ids = network_ids
        self.keys = keys

    def file_format(self):
        fformat = self.comboFormat.currentText()
        if fformat == "gsimcli":
            toggle_save = True
        elif fformat == "COST-HOME":
            toggle_save = False

        self.enable_save_cost(toggle_save and self.checkSaveCost.isChecked())
        self.checkSaveCost.setEnabled(toggle_save)

    def find_results(self, path):
        """Find gsimcli results files.

        """
        return glob2.glob(os.path.join(path, '**/*.xls'))

    def print_results(self):
        over_network = self.groupNetwork.isChecked()
        over_station = self.groupStation.isChecked()
        self.results = self.office.results

        if over_network:
            self.network_crmse = str(self.results[0][0])
            self.network_improvement = str(self.results[2][0])
            self.lineNetworkCRMSE.setText(self.network_crmse)
            self.lineNetworkImprov.setText(self.network_improvement)
        if over_station:
            self.station_crmse = str(self.results[0][int(over_network)])
            self.station_improvement = str(self.results[2][int(over_network)])
            self.lineStationCRMSE.setText(self.station_crmse)
            self.lineStationImprov.setText(self.station_improvement)

        self.show_status(False)
        self.buttonSaveResults.setEnabled(True)

#     def remove_rows(self):
#         """Remove the selected rows from the table.
#         Connected to the tableResults context menu.
#
#         """
#         indexes = self.tableResults.selectedIndexes()
#         rows = sorted(set([index.row() for index in indexes]))
#         for n, row in enumerate(rows):
#             self.tableResults.removeRow(row - n)
#
#         # keep one row
#         if not self.tableResults.rowCount():
#             self.tableResults.insertRow(0)

    def save_results(self):
        """Save the calculated results to a simple text file (TSV).
        Connected to the SaveResults button.

        """
        caption = "Select file to save the results"
        index = self.tableResultsModel.index(0, 0)
        tag = path_up(self.tableResultsModel.data(index), 2)[1]
        default_name = " ".join(["scores"] + tag.split(os.sep)) + ".txt"
        default_path = os.path.join(self.default_dir, default_name)

        filepath = QtGui.QFileDialog.getSaveFileName(self, caption,
                                                     dir=default_path)

        if filepath[0]:
            self.default_dir = os.path.dirname(filepath[0])
            text = ("gsimcli :: benchmark scores\n" +
                    "*" * 27 + "\n"
                    "\t\tStation\t\tNetwork\n"
                    "CRMSE:\t\t{}\t{}\n".format(self.station_crmse,
                                                self.network_crmse) +
                    "Improvement:\t{}\t{}".format(self.station_improvement,
                                                  self.network_improvement))
            with open(filepath[0], 'w') as afile:
                afile.write(text)

    def set_gui_params(self):
        self.guiparams = list()
        add = self.guiparams.extend

        gp = "tools_benchmark"
        res = ui.GuiParam("temporal_resolution", self.comboResolution, gp)
        fformat = ui.GuiParam("file_format", self.comboFormat, gp)
        # table = ui.GuiParam("table_results", self.tableResults, gp)  # FIXME:
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

        add([res, fformat, no_data, orig, inho, save_cost, cost_path,  # table
             over_station, over_network, yearly_sum, skip_missing,
             skip_outlier])

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
        # extra option for monthly data
        # if self.resolution == "monthly":
        show_months = QtGui.QAction("Show included files", self)
        show_months.triggered.connect(self.show_months)
        self.tableResults.addAction(show_months)
        # vertical header
        vheader = self.tableResults.verticalHeader()
        vheader.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        vheader.addAction(del_row)

    def set_use_all(self, toggle):
        """Select all or none of the rows to be used.
        Connected to the Use all checkbox.

        """
        for row in range(self.tableResultsModel.rowCount()):
            index = self.tableResultsModel.index(row, 3)
            self.tableResultsModel.setData(index, toggle)

    def show_months(self):
        """Launch a widget to show the monthly files included in the selected
        directory.

        """
        # row = self.tableResults.currentRow()
        row = self.tableResultsView.currentIndex().row()
        # item = self.tableResults.item(row, 0)
        index = self.tableResultsModel.index(row, 0)
        item = self.tableResultsModel.data(index)
        popup = QtGui.QListWidget(self)
        if item:  # and item.text():
            network = item  # .text()
            files = self.find_results(network)
            ui.pylist_to_qlist(files, popup)
            popup.setWindowFlags(QtCore.Qt.Window)
            popup.setWindowTitle("Files with monthly results")
            popup.setMinimumWidth(popup.sizeHintForColumn(0) + 15)
            popup.show()

    def show_status(self, toggle):
        self.progressBar.setValue(0)
        self.progressBar.setVisible(toggle)
        self.buttonCalculate.setEnabled(not toggle)

    def time_resolution(self):
        resolution = self.comboResolution.currentText()

        if resolution == "Monthly":
            label = "Results directory"
            toggle_sum = False
            toggle_show = True
            self.resolution = "monthly"
        elif resolution == "Yearly":
            label = "Results file"
            toggle_sum = True
            toggle_show = False
            self.resolution = "yearly"

        self.tableResultsModel.setHeaderData(0, label)
        # self.tableResultsView.horizontalHeaderItem(0).setText(label)
        for action in self.tableResultsView.actions():
            if action.text().startswith("Show included"):
                action.setVisible(toggle_show)
        self.checkAverageYearly.setEnabled(toggle_sum)

    def update_bench(self):
        benchmark_path = self.sender().benchmark_path
        precip = os.path.join("precip", "sur1")
        if not self.lineOrig.text():
            self.lineOrig.setText(os.path.join(benchmark_path, "orig", precip))
        if not self.lineInho.text():
            self.lineInho.setText(os.path.join(benchmark_path, "inho", precip))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Scores()
    window.show()
    sys.exit(app.exec_())
