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
import interface.checktable as ct
import interface.ui_utils as ui
import pandas as pd
import tools.scores as scores
from tools.utils import path_up


base = os.path.dirname(os.path.dirname(__file__))


# class TableModel(QtCore.QAbstractTableModel):
#     """Table model with a column filled with one check box per line. Each check
#     box is centered in the cell and has no text.
#
#     """
#     dataChanged = QtCore.Signal(QtCore.QModelIndex, QtCore.QModelIndex)
#
#     def __init__(self, checkbox_col, parent=None):
#         """Constructor.
#
#         Parameters
#         ----------
#         checkbox_col : int
#             Number of the column with the check boxes.
#         parent : QObject, optional
#             Parent of the model.
#
#         """
#         super(TableModel, self).__init__(parent)
#         self.table = None
#         self.header = None
#         self.vheader = None
#         self.checkbox_col = checkbox_col
# signals
#         self.dataChanged.connect(self.add_rows_auto)
#
#     def addItem(self, item):
#         """Append a row to the table.
#
#         Parameters
#         ----------
#         item : array_like
#             Row to be inserted after the last row in the table.
#
#         """
#         count = self.rowCount()
#         self.beginInsertRows(QtCore.QModelIndex(), count, count)
#         self.table.loc[count] = item
#         self.endInsertRows()
#
#     def add_rows_auto(self, index):
#         """Automatically add a new row after entering data in the last row.
#         Connected to the dataChanged signal.
#         This new row is empty and the check box is not checked.
#
#         Parameters
#         ----------
#         index : QModelIndex
#             Index passed by the dataChanged signal.
#
#         """
#         row = index.row()
#         row_content = self.table.values[row, :-1]
#         if row == (self.rowCount() - 1) and all(row_content):
#             self.addItem(['', '', '', False])
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
#         if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
#             i = index.row()
#             j = index.column()
#             if j == self.checkbox_col:
#                 return self.table.iloc[i, j]
#             else:
#                 return unicode(self.table.iloc[i, j])
#
#     def flags(self, index):
#         """Return the item flags for the given index.
#
#         """
#         if index.column() == self.checkbox_col:
#             return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
#         else:
# return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled  # @IgnorePep8
#
#     def headerData(self, idx, orientation, role):
#         """Return the data for the given `role` and `section` in the header
#         with the specified `orientation`.
#
#         """
#         if (orientation == QtCore.Qt.Horizontal and
#                 role == QtCore.Qt.DisplayRole):
# return unicode(self.header[idx])
#             return self.table.columns.tolist()[idx]
#         if (orientation == QtCore.Qt.Vertical and
#                 role == QtCore.Qt.DisplayRole):
# return unicode(self.vheader[idx])
#             return self.table.index.tolist()[idx]
#
#     def isChecked(self, index):
#         """Return the check box state in the given `index`.
#
#         """
#         return self.table.iloc[index.row(), self.checkbox_col]
#
#     def get_key(self, key, filter_selected=False):
#         """Return the column named `key` in the table.
#
#         Parameters
#         ----------
#         key : string
#             Column name.
#         filter_selected : boolean, default False
#             Return only the rows with a checked check box.
#
#         """
#         if filter_selected:
#             values = self.table.query(self.checkbox_key)[key]
#         else:
#             values = self.table[key]
#
#         return values
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
#     def removeRows(self, row, count, parent=QtCore.QModelIndex()):
#         """Remove the row in the given position.
#
#         """
#         if row < 0 or row > self.rowCount():
#             return False
#
#         self.beginRemoveRows(parent, row, row)
#         self.table.drop(row, axis=0, inplace=True)
#         self.table.reset_index(drop=True, inplace=True)
#         self.endRemoveRows()
#         return True
#
#     def rowCount(self, parent=QtCore.QModelIndex()):
#         """Return the number of rows in the table.
#
#         """
#         if self.table is not None:
#             return self.table.shape[0]
#
#     def setChecked(self, index, value, role=QtCore.Qt.EditRole):
#         """Set the check box in the given `index` with the given `value`.
#
#         """
#         if role == QtCore.Qt.EditRole:
#             self.table.iloc[index.row(), self.checkbox_col] = value
#             self.dataChanged.emit(index, index)
#             return True
#         return False
#
#     def setData(self, index, value, role=QtCore.Qt.EditRole):
#         """Set the `role` data for the item at `index` to `value`.
#
#         """
#         if role == QtCore.Qt.EditRole:
#             i = index.row()
#             j = index.column()
#             self.table.iloc[i, j] = value
#             self.dataChanged.emit(index, index)
#             return True
#         return False
#
#     def setHeaderData(self, section, value, orientation=QtCore.Qt.Horizontal,
#                       role=QtCore.Qt.EditRole):
#         """
#         Set the data for the given `role` and `section` in the header with the
#         specified `orientation` to the `value` supplied.
#
#         """
#         if role == QtCore.Qt.EditRole and orientation == QtCore.Qt.Horizontal:
#             self.header[section] = value
#             self.headerDataChanged.emit(orientation, section, section)
#             return True
#         elif role == QtCore.Qt.EditRole and orientation == QtCore.Qt.Vertical:
#             self.vheader = value
#             self.headerDataChanged.emit(orientation, section, section)
#             return True
#         else:
#             return False
#
#     def update(self, data_in):
#         """Change the whole existing table with `data_in`. Headers will be
#         changed accordingly to the names existing in `data_in` table.
#
#         Existing data will be lost.
#
#         Parameters
#         ----------
#         data_in : pandas.DataFrame
#             Table with the new data and headers.
#
#         """
#         self.table = data_in
#         headers = data_in.columns
#         self.header = [unicode(field) for field in headers]
#         indexes = data_in.index
#         self.vheader = [unicode(index + 1) for index in indexes]
#         self.checkbox_key = self.table.columns[self.checkbox_col]
class TableView(ct.TableView):

    """A table view to show and manage the data in the table model with check
    boxes in one column.

    The table has alternating row colours and a customised context menu.

    """

    def __init__(self, checkbox_col, parent=None):
        """Constructor.

        Parameters
        ----------
        checkbox_col : int
            Number of the column with the check boxes.
        parent : QObject, optional
            Parent of the model.

        """
        super(TableView, self).__init__(checkbox_col=checkbox_col,
                                        parent=parent)
        # self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # signals
        self.customContextMenuRequested.connect(self.context_menu)
        self.doubleClicked.connect(self.browse_cell)
        # set delegate
        # self.setItemDelegateForColumn(checkbox_col, CheckBoxDelegate(self))
        # build context menu
        self.set_context_menu()
        # set edit triggers
        self.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed |
                             QtGui.QAbstractItemView.EditKeyPressed |
                             QtGui.QAbstractItemView.SelectedClicked)

    def browse_cell(self):
        """Wrapper to the dialogs that will open either a File or a Directory
        dialog.

        """
        index = self.currentIndex()
        col = index.column()
        resolution = self.parent().resolution
        if resolution == "yearly" or col != 0:
            self.parent().browse_file(index)
        elif resolution == "monthly":
            self.parent().browse_homog_dir(index)

    def context_menu(self, point):
        """Open a specific context menu depending on which column it was
        requested.

        """
        index = self.indexAt(point)
        column = index.column()
        point = self.mapToGlobal(point)
        if column == 0:
            self.results_menu.exec_(point)
        elif column == 1:
            self.network_menu.exec_(point)
        elif column == 2:
            self.keys_menu.exec_(point)

    def set_context_menu(self):
        """Set up the context menus of the tableResults View, in its cells
        and vertical header. Each column will have its own context menu.

        """
        # a menu for different columns
        self.results_menu = QtGui.QMenu(self)
        self.network_menu = QtGui.QMenu(self)
        self.keys_menu = QtGui.QMenu(self)
        # set up actions
        browse_file = QtGui.QAction("Browse file", self)
        browse_directory = QtGui.QAction("Browse directory", self)
        del_row = QtGui.QAction("Remove selected row(s)", self)
        browse_file.triggered.connect(self.browse_cell)
        browse_directory.triggered.connect(self.browse_cell)
        del_row.triggered.connect(self.remove_rows)
        # extra option for monthly data
        show_months = QtGui.QAction("Show included files", self)
        show_months.triggered.connect(self.show_months_popup)
        # compose menus
        self.results_menu.addActions([browse_directory,
                                      del_row,
                                      show_months,
                                      ])
        self.network_menu.addActions([del_row,
                                      ])
        self.keys_menu.addActions([browse_file,
                                   del_row,
                                   ])
        # vertical header
        vheader = self.verticalHeader()
        vheader.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        vheader.addAction(del_row)

    def set_context_menu_for_resolution(self, resolution):
        """Adjust the context menu according to the selected time resolution
        (monthly or yearly).

        """
        if resolution == "monthly":
            label = "directory"
            toggle_show = True
        elif resolution == "yearly":
            label = "file"
            toggle_show = False

        for action in self.results_menu.actions():
            if action.text().startswith("Browse"):
                action.setText("Browse {0}".format(label))
            elif action.text().startswith("Show included"):
                action.setVisible(toggle_show)

    def show_months_popup(self):
        """Launch a widget to show the monthly files included in the selected
        directory.

        """
        row = self.currentIndex().row()
        index = self.model().index(row, 0)
        item = self.model().data(index)
        popup = QtGui.QListWidget(self)
        if item:
            network = item
            files = self.parent().find_results(network)
            ui.pylist_to_qlist(files, popup)
            popup.setWindowFlags(QtCore.Qt.Window)
            popup.setWindowTitle("Files with monthly results")
            popup.setMinimumWidth(popup.sizeHintForColumn(0) + 15)
            popup.show()


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

        # lines
        self.lineOrig.textChanged.connect(self.guess_inho)
        self.lineInho.textChanged.connect(self.enable_improvement)

        # table
        # model and view
        self.tableResultsModel = ct.TableModel(3, self)
        self.tableResultsView = TableView(3, self)
        # initialise the table with blank values
        columns = ['Results file', 'Network ID', 'Keys file', 'Use']
        table = pd.DataFrame(index=range(5), columns=columns)
        table.fillna('', inplace=True)
        table['Use'] = False
        self.tableResultsModel.update(table)
        # DEPRECATED:
        # close the previous used widget, being kept for reference only
        self.tableResults.close()
        self.tableResultsView.setModel(self.tableResultsModel)
        self.layout().insertWidget(3, self.tableResultsView)
        self.hheader = self.tableResultsView.horizontalHeader()
        self.hheader.setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.hheader.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        self.hheader.setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.hheader.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

        # hidden widgets by default
        ui.hide([self.labelSaveCost, self.lineSaveCost, self.buttonSaveCost,
                 self.progressBar
                 ])

        self.file_format()
        self.time_resolution()

    def browse_homog_dir(self, index):
        """Dialog to select the directory with the homogenisation results.

        """
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
            caption = "Select {0} file".format(target)
            filepath = QtGui.QFileDialog.getOpenFileName(self, caption,
                                                         dir=self.default_dir)

            if filepath[0]:
                self.tableResultsModel.setData(index, filepath[0])
                self.default_dir = os.path.dirname(filepath[0])

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

        caption = "Select the directory {0}".format(what)
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
        # simple validation of input data
        try:
            self.extract_results()
        except BaseException as e:
            print str(e)
            return False
        else:
            if not os.path.isdir(self.lineOrig.text()):
                raise ValueError("Original data path is not valid.")
            if self.format_is_gsimcli and not all([len(self.results_files),
                   len(self.network_ids), len(self.keys)]):
                raise ValueError("Incomplete or invalid gsimcli results.")

        self.show_status(True)
        self.set_progress_max()

        if self.format_is_gsimcli:
            results_arg = 'gsimcli_results'
        else:
            results_arg = 'network_path'

        # arguments for both formats
        kwargs = {
            results_arg: self.results_files,
            'no_data': self.spinNoData.value(),
            'orig_path': self.lineOrig.text(),
            'inho_path': self.lineInho.text(),
            'yearly': self.resolution == 'yearly',
            'over_network': self.groupNetwork.isChecked(),
            'over_station': self.groupStation.isChecked(),
            'skip_missing': self.checkSkipMissing.isChecked(),
            'skip_outlier': self.checkSkipOutlier.isChecked(),
        }
        # arguments for specific format
        if self.format_is_gsimcli:
            kwargs.update({
                'keys_path': self.keys,
                'costhome_path': self.lineSaveCost.text(),
                'yearly_sum': self.checkAverageYearly.isChecked(),
            })
        else:
            kwargs['networks_id'] = self.network_ids

        # set up the job
        if self.format_is_gsimcli:
            job = scores.gsimcli_improvement
        else:
            job = scores.cost_improvement

        updater = scores.update.progress
        self.office = ui.Office(self, job, updater=updater, **kwargs)
        # self.office.worker.time_elapsed.connect(self.set_time)
        self.office.progress.connect(self.set_progress)
        self.office.finished.connect(self.print_results)
        self.office.start()

    def count_stations(self):
        """Try to find the total number of stations in the submission from the
        keys files.

        """
        stations = 0

        if self.format_is_gsimcli:
            keys = self.tableResultsModel.get_key("Keys file", True)

            for key in keys:
                stations += sum(1 for line in open(key)) - 1  # @UnusedVariable

        else:
            paths = self.tableResultsModel.get_key("Results file", True)
            # simple guess based on the number of files and folders
            for path in paths:
                stations += len(os.listdir(path))

        return stations

    def enable_improvement(self, inho_path):
        """Enable/disable widgets related to the Improvement display.
        Connected to the Inho lineEdit.

        """
        if inho_path and os.path.isdir(inho_path):
            toggle = True
        else:
            toggle = False
        self.labelStationImprov.setEnabled(toggle)
        self.lineStationImprov.setEnabled(toggle)
        self.labelNetworkImprov.setEnabled(toggle)
        self.lineNetworkImprov.setEnabled(toggle)

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
        if toggle:
            inho_path = self.lineInho.text()
            self.enable_improvement(inho_path)

    def enable_scores_station(self, toggle):
        """Toggle widgets related to the station scores group: crmse and
        improvement labels and lines.
        Connected to the groupStation checkbox.

        """
        self.labelStationCRMSE.setEnabled(toggle)
        self.lineStationCRMSE.setEnabled(toggle)
        self.labelStationImprov.setEnabled(toggle)
        self.lineStationImprov.setEnabled(toggle)
        if toggle:
            inho_path = self.lineInho.text()
            self.enable_improvement(inho_path)

    def extract_results(self):
        """Extract the results files, network IDs and keys files from the
        tableResults Model.

        """
        results = self.tableResultsModel.get_key('Results file', True)
        network_ids = self.tableResultsModel.get_key('Network ID', True)

        if self.format_is_gsimcli:
            keys = self.tableResultsModel.get_key('Keys file', True)

        if self.format_is_gsimcli:
            if self.resolution == "yearly":
                results_files = results
            elif self.resolution == "monthly":
                networks = list()
                for i, network in enumerate(results):
                    networks.append(self.find_results(network, network_ids[i]))
                results_files = networks
            self.results_files = dict(zip(network_ids, results_files))
            self.keys = keys
            self.network_ids = network_ids

        else:  # format is cost-home
            self.results_files = results.tolist()[0]
            # FIXME: [0] will give a wrong number of networks to set_progress
            self.keys = None
            ids_list = network_ids.tolist()
            if ids_list:
                self.network_ids = ids_list[0].split()
            else:
                self.network_ids = None

    def file_format(self):
        """Handle the different file formats accepted.

        WIP

        """
        fformat = self.comboFormat.currentText()
        if fformat == "gsimcli":
            toggle_save = True
        elif fformat == "COST-HOME":
            toggle_save = False

        self.format_is_gsimcli = toggle_save
        self.enable_save_cost(toggle_save and self.checkSaveCost.isChecked())
        self.checkSaveCost.setEnabled(toggle_save)
        keys_index = self.tableResultsModel.header.index('Keys file')
        self.tableResultsView.setColumnHidden(keys_index, not toggle_save)

    def find_results(self, path, network_id=''):
        """Find gsimcli results files.

        """
        return glob2.glob(os.path.join(path, '**/*' + network_id + '*.xls'))

    def guess_inho(self):
        """Try to guess the inho path.

        """
        inho = self.lineOrig.text().replace(os.sep + 'orig' + os.sep,
                                            os.sep + 'inho' + os.sep)
        if os.path.isdir(inho):
            self.lineInho.setText(inho)

    def print_results(self):
        """Display the results in the lineEdits widgets.

        """
        show_improvement = self.labelStationImprov.isEnabled()
        over_network = self.groupNetwork.isChecked()
        over_station = self.groupStation.isChecked()
        self.results = self.office.results

        if over_network:
            self.network_crmse = str(self.results[0][0])
            self.lineNetworkCRMSE.setText(self.network_crmse)
            if show_improvement:
                self.network_improvement = str(self.results[2][0])
                self.lineNetworkImprov.setText(self.network_improvement)
        if over_station:
            self.station_crmse = str(self.results[0][int(over_network)])
            self.lineStationCRMSE.setText(self.station_crmse)
            if show_improvement:
                self.station_improvement = str(
                    self.results[2][int(over_network)])
                self.lineStationImprov.setText(self.station_improvement)

        self.show_status(False)
        self.buttonSaveResults.setEnabled(True)

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
                    "Improvement:\t{0}\t{1}".format(self.station_improvement,
                                                  self.network_improvement))
            with open(filepath[0], 'w') as afile:
                afile.write(text)

    def set_gui_params(self):
        """Set the GUI parameters.

        """
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
        """Set the progress of the calculation process.

        """
        progress = 100 * current / self.total
        self.progressBar.setValue(progress)

    def set_progress_max(self):
        """Determine the maximum value for the progress bar.

        """
        over_network = self.groupNetwork.isChecked()
        over_station = self.groupStation.isChecked()

        networks = len(self.results_files)
        stations = self.count_stations()
        total = networks + 1
        if over_network:
            total += networks * 2
        if over_station:
            total += stations * 2

        self.total = total

    def set_use_all(self, toggle):
        """Select all or none of the rows to be used.
        Connected to the Use all checkbox.

        """
        for row in range(self.tableResultsModel.rowCount()):
            index = self.tableResultsModel.index(row, 3)
            self.tableResultsModel.setData(index, toggle)

    def show_status(self, toggle):
        """Enable/disable the progress bar and the Calculate pushbutton.

        """
        self.progressBar.setValue(0)
        self.progressBar.setVisible(toggle)
        self.buttonCalculate.setEnabled(not toggle)

    def time_resolution(self):
        """Handle the time resolution.
        Connected to the resolution combo box.

        """
        resolution = self.comboResolution.currentText().lower()

        if resolution == "monthly":
            label = "Results directory"
            toggle_sum = False
            self.resolution = "monthly"
        elif resolution == "yearly":
            label = "Results file"
            toggle_sum = True
            self.resolution = "yearly"

        self.tableResultsModel.setHeaderData(0, label)
        self.tableResultsView.set_context_menu_for_resolution(resolution)
        self.checkAverageYearly.setEnabled(toggle_sum)

    def update_bench(self):
        """Update the Orig and Inho paths according to a previsouly saved
        benchmark directory.

        """
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
