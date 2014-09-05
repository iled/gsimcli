# -*- coding: utf-8 -*-
"""
Created on 16/06/2014

@author: julio
"""

from PySide import QtCore, QtGui  # , QtUiTools
from functools import partial
import glob
from multiprocessing import cpu_count
import os
import sys
from tempfile import NamedTemporaryFile
import time

base = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base)

import external_libs.disk as fs
from external_libs.pyside_dynamic import loadUi
from launchers import method_classic
from parsers.gsimcli import GsimcliParam
import tools.homog as hmg
from tools.utils import seconds_convert


class GsimcliMainWindow(QtGui.QMainWindow):
    """Main window for GSIMCLI application. Handle all the necessary logic.

    """
    def __init__(self, parent=None):
        """Constructor. Initialise some variables, setup settings and handle
        all signals.

        """
        # linus?
        self.linux = sys.platform.startswith('linux')
        # load ui file
        QtGui.QMainWindow.__init__(self, parent)
        loadUi(os.path.join(base, "interface", "gsimcli.ui"), self)
        # QtUiTools.QUiLoader  # try this

        # settings
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.NativeFormat)
        self.settings = QtCore.QSettings()
        self.settings_ext = os.path.splitext(self.settings.fileName())[1]
        # self.settings.clear()
        self.settings.beginGroup("main_window")
        self.resize(self.settings.value("size", QtCore.QSize(742, 660)))
        self.move(self.settings.value("position", QtCore.QPoint(50, 50)))
        if self.settings.contains("state"):
            self.restoreState(self.settings.value("state"))
            self.actionRestoreLastSession.setEnabled(True)
        default_dir = self.settings.value("default_dir")
        if default_dir and os.path.exists(default_dir):
            self.default_dir = default_dir
        else:
            self.default_dir = os.path.expanduser('~/')
        self.load_recent_settings()
        self.settings.endGroup()

        # set params
        self.params = GsimcliParam()
        self.temp_params = NamedTemporaryFile(delete=False)
        self.loaded_params = None
        self.skip_sim = self.SO_checkSkipSim.isChecked()
        self.print_status = self.actionPrintStatus.isChecked()
        self.batch_decades = self.DB_checkBatchDecades.isChecked()
        self.batch_networks = self.DB_checkBatchNetworks.isChecked()
        self.header = self.DL_checkHeader.isChecked()
        self.needed_space = None
        self.free_space = None
        self.stations_list = list()
        self.wildcard_decade = 'dec*'
        self.wildcard_variog = '*variog*.csv'
        self.wildcard_grid = '*grid*.csv'

        # buttons
        self.buttonBox.button(QtGui.QDialogButtonBox.
                          Apply).clicked.connect(self.apply_settings)
        self.buttonBox.button(QtGui.QDialogButtonBox.
                          RestoreDefaults).clicked.connect(self.reset_settings)
        self.DL_buttonDataPath.clicked.connect(self.browse_data_file)
        self.DB_buttonAddNetworks.clicked.connect(self.browse_networks)
        self.DB_buttonRemoveNetworks.clicked.connect(self.remove_networks)
        self.DB_buttonDecadesPath.clicked.connect(self.browse_decades)
        self.DB_buttonVariogPath.clicked.connect(self.browse_variog_file)
        self.SO_buttonExePath.clicked.connect(self.browse_exe_file)
        self.HD_buttonRemoveStations.clicked.connect(self.remove_stations)
        self.HD_buttonResetStations.clicked.connect(self.reset_stations)
        self.HR_buttonResultsPath.clicked.connect(self.browse_results)
        self.buttonAbort.clicked.connect(self.abort_gsimcli)

        # change pages
        self.treeWidget.expandAll()
        self.treeWidget.currentItemChanged.connect(self.set_stacked_item)

        # check boxes
        self.DL_checkHeader.toggled.connect(self.enable_header)
        self.DB_checkBatchDecades.toggled.connect(self.enable_batch_decades)
        self.DB_checkBatchNetworks.toggled.connect(self.enable_batch_networks)
        self.SO_checkSkipSim.toggled.connect(self.enable_skip_sim)
        self.actionPrintStatus.toggled.connect(self.disable_print_status)
        self.HR_checkPurgeSims.toggled.connect(self.enable_purge_sims)

        # combo boxes
        self.HD_comboStationOrder.currentIndexChanged.connect(
                                                  self.change_station_order)
        self.HD_comboDetectionMethod.currentIndexChanged.connect(
                                                         self.enable_skewness)
        self.HD_comboDetectionMethod.currentIndexChanged.connect(
                                                     self.enable_percentile)

        # hidden
        self.SV_labelBatchDecades.setVisible(False)
        self.HD_groupUserOrder.setVisible(False)
        self.groupProgress.setVisible(False)
        self.groupStatusInfo.setVisible(False)
        self.groupTime.setVisible(False)
        self.HD_groupSkewness.setVisible(False)
        self.HD_groupPercentile.setVisible(False)

        # line edits
        self.DL_lineDataPath.textChanged.connect(self.preview_data_file)
        self.DB_lineDecadesPath.textChanged.connect(self.changed_decades_path)
        self.HR_lineResultsPath.textChanged.connect(self.available_space)
        self.HR_lineResultsName.textChanged.connect(self.check_results_ext)

        # lists
        self.DB_listNetworksPaths.currentItemChanged.connect(
                                                     self.current_network)

        # menu
        self.actionRestoreLastSession.triggered.connect(partial(
                            self.open_settings, self.settings.fileName()))
        # self.actionOpen.triggered.connect(self.open_gsimcli_params)
        self.actionOpenSettingsFile.triggered.connect(self.browse_settings)
        # self.actionSave.triggered.connect(self.save_gsimcli_params)
        self.actionSaveSettings.triggered.connect(self.save_settings)
        # self.actionSaveAs.triggered.connect(self.save_as_gsimcli_params)
        self.actionExportSettings.triggered.connect(self.export_settings)
        self.actionGSIMCLI.triggered.connect(self.start_gsimcli)
        # self.actionGSIMCLI.triggered.connect(self.run_gsimcli)
        self.actionClose.triggered.connect(self.close)
        self.actionOnlineDocs.triggered.connect(self.online_docs)
        self.actionAbout.triggered.connect(self.about)

        # spin
        self.set_cpu_cores()

        # default
        self.default_varnames()

        # install the custom output stream
        sys.stdout = EmittingStream()
        sys.stdout.text_written.connect(self.output_status)

        # keep track of current status: network, decade, candidate, simulation
        self.count_status = [0, 0, 0, 0]
        self.total_sims = 0
        self.current_sim = 0

    def __del__(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__

    def about(self):
        """The About box. """
        title = "About gsimcli"
        about = "".join(file('about.html').readlines())
        self.aboutbox = QtGui.QMessageBox.about(self, title, about)

    def online_docs(self):
        """Redirect to the online documentation at readthedocs.org"""
        QtGui.QDesktopServices.openUrl("http://gsimcli.readthedocs.org")

    def output_status(self, text):
        """Write text in the status block.

        """
        if "STATUS: network" in text:
            info_object = self.labelStatusNetwork
            self.count_status[0] += 1
        elif "STATUS: decade" in text:
            info_object = self.labelStatusDecade
            self.count_status[1] += 1
        elif "STATUS: candidate" in text:
            info_object = self.labelStatusStation
            self.count_status[2] += 1
            self.current_sim = (self.SO_spinNumberSims.value() *
                                self.count_status[2])
        elif "STATUS: realization" in text:
            info_object = self.labelStatusSim
            self.count_status[3] += 1
            self.current_sim += 1

        else:
            info_object = None

        if info_object:
            info_object.setText(text.split()[-1])
            self.set_progress()
        else:
            sys.__stdout__.write(text)

    def set_stacked_item(self, current, previous):
        """Connects the right menu (QTreeWidget) with the panels on the right
        (QStackedWidget).

        """
        if current.text(0) in ["Data", "Simulation", "Homogenisation"]:
            current.setExpanded(True)
            self.treeWidget.setCurrentItem(current.child(0))

        tree_item = self.treeWidget.currentItem().text(0)
        if tree_item == "Load":
            self.stackedWidget.setCurrentWidget(self.DataLoad)
        elif tree_item == "Batch":
            self.stackedWidget.setCurrentWidget(self.DataBatch)
        elif tree_item == "Save":
            self.stackedWidget.setCurrentWidget(self.DataSave)
        elif tree_item == "Options":
            self.stackedWidget.setCurrentWidget(self.SimulationOptions)
        elif tree_item == "Variogram":
            self.stackedWidget.setCurrentWidget(self.SimulationVariogram)
        elif tree_item == "Grid":
            self.stackedWidget.setCurrentWidget(self.SimulationGrid)
        elif tree_item == "Advanced":
            self.stackedWidget.setCurrentWidget(self.SimulationAdvanced)
        elif tree_item == "Detection":
            self.stackedWidget.setCurrentWidget(self.HomogenisationDetection)
        elif tree_item == "Results":
            self.stackedWidget.setCurrentWidget(self.HomogenisationResults)

    def set_recent_settings(self):
        """Create the recents settings files menu. Filter non
        existing files.

        """
        self.menuRecentSettingsFiles.clear()
        self.update_recent_settings()
        i = 1
        for recent in self.recent_settings:
            if os.path.exists(recent):
                item = QtGui.QAction(self.menuRecentSettingsFiles)
                item.setText("&" + str(i) + ": " + recent)
                item.setToolTip(recent)
                item.triggered.connect(partial(self.open_settings, recent))
                self.menuRecentSettingsFiles.addAction(item)
                i += 1

    def add_recent_settings(self, filepath):
        """Add an item to the recent settings files list. Won't add already
        listed files.

        """
        if filepath in self.recent_settings:
            self.recent_settings.remove(filepath)
        self.recent_settings.insert(0, filepath)
        self.set_recent_settings()

    def update_recent_settings(self):
        """Update the recent settings file list. Filter non existing files and
        keep the list under the limit of 10 items. Also, enable/disable the
        menu depending if the list is empty or not.

        """
        for recent in list(self.recent_settings):
            if not os.path.exists(recent):
                self.recent_settings.remove(recent)
        if len(self.recent_settings) > 10:
            self.recent_settings.pop()
        self.menuRecentSettingsFiles.setEnabled(bool(self.recent_settings))

    def load_recent_settings(self):
        """Extracts recent settings files list from the QSettings file. The
        loading method depends on the native file format.

        """
        if self.settings.contains("recent_settings"):
            self.recent_settings = self.settings.value("recent_settings")
        else:
            # for iniformat
            self.recent_settings = list()
            count = sum("recent_settings" in child for
                        child in self.settings.childKeys())
            for i in xrange(count):
                self.recent_settings.append(
                            self.settings.value("recent_settings_" + str(i)))
        self.set_recent_settings()

    def set_cpu_cores(self):
        """Set the spinbox related to the CPU cores, setting the default value
        to the maximum number available.

        """
        self.SO_spinCores.setValue(cpu_count())
        self.SO_spinCores.setMaximum(cpu_count())

    def enable_header(self, toggle):
        """Act when the header checkbox is toggled. Try to set the data name.

        """
        self.header = toggle
        if toggle and self.DL_plainDataPreview.blockCount() > 1:
            self.DL_lineDataName.setText(self.DL_plainDataPreview.toPlainText()
                                         .split(os.linesep)[0])
        else:
            self.DL_lineDataName.clear()

    def enable_decades_group(self, enable):
        """Toggle all the batch decade related widgets. Connected to the batch
        decades checkbox.

        """
        self.DB_labelVariogPath.setEnabled(enable)
        self.DB_lineVariogPath.setEnabled(enable)
        self.DB_buttonVariogPath.setEnabled(enable)
        self.DB_labelDecadesPath.setEnabled(enable)
        self.DB_lineDecadesPath.setEnabled(enable)
        self.DB_buttonDecadesPath.setEnabled(enable)
        self.DB_labelNetworkID.setEnabled(enable)
        self.DB_lineNetworkID.setEnabled(enable)

    def disable_datapath_group(self, disable):
        """Toggle all the data path related widgets. Connected to the batch
        decades and network checkboxes.

        """
        self.DL_labelDataPath.setDisabled(disable)
        self.DL_lineDataPath.setDisabled(disable)
        self.DL_buttonDataPath.setDisabled(disable)

    def enable_batch_networks(self, toggle):
        """Toggle all the batch network related widgets, including the menu
        option for Simulation\Grid. Connected to the batch
        networks checkbox.

        Update the estimated necessary space.

        """
        self.batch_networks = toggle
        self.DB_labelNetworksPaths.setEnabled(toggle)
        self.DB_buttonAddNetworks.setEnabled(toggle)
        self.DB_buttonRemoveNetworks.setEnabled(toggle)
        self.DB_listNetworksPaths.setEnabled(toggle)
        tree_item = self.treeWidget.findItems("Grid", QtCore.Qt.MatchRecursive,
                                              QtCore.Qt.MatchExactly)[0]
        tree_item.setDisabled(toggle)
        if toggle:
            tool_tip = ("Batch mode for networks is enabled, grids are "
                        "specified in each network grid file.")
        else:
            tool_tip = None
        tree_item.setToolTip(0, tool_tip)
        self.enable_decades_group(self.batch_decades and not
                                  self.batch_networks)
        if not self.batch_decades:
            self.disable_datapath_group(toggle)

        # toogle results file tooltip
        if toggle:
            results_tip = "A suffix will be appended per network."
        else:
            results_tip = None
        self.HR_lineResultsName.setToolTip(results_tip)

        # calc space
        self.estimate_necessary_space()

    def enable_batch_decades(self, toggle):
        """Toggle all the batch decades related widgets, including the menu
        option for Simulation\Variogram. Connected to the batch
        decades checkbox.

        Check if each network has a decades directory and try to find a data
        file. Update the estimated necessary space.

        """
        self.batch_decades = toggle
        # if batching networks, check if each network has a decades directory
        if self.batch_networks and not self.check_decades_dir():
            self.DB_checkBatchDecades.setChecked(False)
            self.DB_checkBatchDecades.setToolTip(("There are networks "
              "directories without the necessary decades directory inside."))
            return self
        else:
            self.DB_checkBatchDecades.setToolTip(None)

        # disable variogram
        # self.SimulationVariogram.setDisabled(toggle)
        # self.SV_labelBatchDecades.setVisible(toggle)
        tree_item = self.treeWidget.findItems("Variogram",
                         QtCore.Qt.MatchRecursive, QtCore.Qt.MatchExactly)[0]
        tree_item.setDisabled(toggle)
        if toggle:
            tool_tip = ("Batch mode for decades is enabled, variograms "
                        "are specified in variography files.")
            self.previous_znodes = self.SG_spinZZNodes.value()
            znodes = 10
        else:
            tool_tip = None
            znodes = self.previous_znodes
        tree_item.setToolTip(0, tool_tip)
        # enable group widgets
        self.enable_decades_group(toggle and not self.batch_networks)
        if not self.batch_networks:
            self.disable_datapath_group(toggle)
        # lock z-nodes
        self.SG_spinZZNodes.setValue(znodes)
        self.SG_spinZZNodes.setDisabled(toggle)
        self.SG_spinZZNodes.setToolTip("Batch decades is enabled.")
        # try to find a data file
        if self.batch_networks and self.DB_listNetworksPaths.currentItem():
            self.preview_data_file(self.find_data_file())
        # calc space
        self.estimate_necessary_space()

    def enable_skip_sim(self, toggle):
        """Toggle widgets related to the skip_sim checkbox: save
        intermediary files. Connected to the skip_sim checkbox.

        Update the estimated necessary space.

        """
        self.skip_sim = toggle
        self.HR_checkSaveInter.setChecked(toggle)
        self.HR_checkSaveInter.setDisabled(toggle)
        if toggle:
            tool_tip = ("Deleting intermediary files not possible when "
                        "skipping the simulation process.")
        else:
            tool_tip = None
        self.HR_checkSaveInter.setToolTip(tool_tip)
        self.estimate_necessary_space()

    def enable_purge_sims(self, toggle):
        """Connected to the purge_sim checkbox.

        Update the estimated necessary space.

        """
        self.estimate_necessary_space()

    def disable_print_status(self, toggle):
        """Connected to the print_status menu action.

        """
        self.print_status = toggle

    def remove_stations(self):
        """Remove selected stations from the users list. Connected to the
        remove_stations pushbutton.

        """
        for station in self.HD_listUserOrder.selectedItems():
            self.HD_listUserOrder.takeItem(self.HD_listUserOrder.row(station))
        # update stations order
        # self.change_station_order()

    def reset_stations(self):
        """Restore the complete list of stations. Connected to the
        reset_stations pushbutton.

        """
        pylist_to_qlist(qlist=self.HD_listUserOrder,
                        pylist=map(str, self.find_stations_ids().
                                   stations.items()[0][1]))

    def change_station_order(self, index=None):
        """Handle the different options to the candidate stations order.
        Connected to the station_order combobox.

        """
        st_order = self.HD_comboStationOrder.currentText()
        order_warning = None
        if st_order == "User":
            if self.DB_listNetworksPaths.count() > 1:
                enable_user = False
                disable_checks = False
                order_warning = ("Not possible to define candidate stations "
                                 "order manually while processing multiple "
                                 "networks.")
            elif self.DB_listNetworksPaths.count() < 1:
                enable_user = False
                disable_checks = False
                order_warning = ("No network data given yet.")
            else:
                enable_user = True
                disable_checks = True
                pylist_to_qlist(qlist=self.HD_listUserOrder,
                    pylist=map(str, self.find_stations_ids().
                               stations.items()[0][1]))
        elif st_order == "Random":
            enable_user = False
            disable_checks = True
        else:
            enable_user = False
            disable_checks = False
        self.HD_comboStationOrder.setToolTip(order_warning)
        self.HD_groupUserOrder.setVisible(enable_user)
        self.HD_checkAscending.setDisabled(disable_checks)
        self.HD_checkMDLast.setDisabled(disable_checks)

    def enable_skewness(self, index):
        """Toggle the widgets related to the skewness correction method.
        Connected to the correction method combobox.

        """
        if self.HD_comboDetectionMethod.currentText() == "Skewness":
            enable = True
        else:
            enable = False
        self.HD_groupSkewness.setVisible(enable)

    def enable_percentile(self, index):
        """Toggle the widgets related to the percentile correction method.
        Connected to the correction method combobox.

        """
        if self.HD_comboDetectionMethod.currentText() == "Percentile":
            enable = True
        else:
            enable = False
        self.HD_groupPercentile.setVisible(enable)

    def browse_data_file(self):
        """Open the dialog to select an existing data file. Connected to the
        browse data file pushbutton.

        Update data file preview and header related widgets.

        """
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select data file",
                                     dir=self.default_dir)
        if filepath[0]:
            self.DL_lineDataPath.setText(filepath[0])
            self.preview_data_file()
            self.enable_header(self.header)
            self.default_dir = os.path.dirname(filepath[0])

    def browse_networks(self):
        """Open the dialog to select existing network directories. Connected to
        the browse networks pushbutton.

        Use non native dialog in order to allow multiple selection.
        Update networks and stations lists.

        """
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setDirectory(self.default_dir)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, True)
        dialog.findChild(QtGui.QListView, "listView").setSelectionMode(
                               QtGui.QAbstractItemView.ExtendedSelection)
        dialog.findChild(QtGui.QTreeView).setSelectionMode(
                               QtGui.QAbstractItemView.ExtendedSelection)
        if dialog.exec_():
            self.DB_listNetworksPaths.addItems(dialog.selectedFiles())
            self.default_dir = dialog.selectedFiles()[-1]
        # update stations order
        self.change_station_order()

    def remove_networks(self):
        """Remove selected networks from the networks list. Connected to the
        remove_networks pushbutton.

        Update stations list.

        """
        for path in self.DB_listNetworksPaths.selectedItems():
            self.DB_listNetworksPaths.takeItem(
                                           self.DB_listNetworksPaths.row(path))
        # update stations order
        self.change_station_order()

    def browse_decades(self):
        """Open the dialog to select an existing decades directory. Connected
        to the browse decade pushbutton.

        """
        dirpath = QtGui.QFileDialog.getExistingDirectory(self,
                                    caption="Select decades directory",
                                    dir=self.default_dir)
        if dirpath:
            self.DB_lineDecadesPath.setText(dirpath)
            self.default_dir = dirpath

    def browse_variog_file(self):
        """Open the dialog to select an existing variography file, necessary
        to batch decades. Connected to the browse variography pushbutton.

        """
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select variography file",
                                     dir=self.default_dir,
                                     filter="Text CSV (*.csv)")
        if filepath[0]:
            self.DB_lineVariogPath.setText(filepath[0])
            self.default_dir = os.path.dirname(filepath[0])

    def browse_exe_file(self):
        """Open the dialog to select an existing simulation binary file.
        Connected to the browse executable file pushbutton.

        """
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select executable file",
                                     dir=self.default_dir,
                                     filter="Executable (*.exe)")
        if filepath[0]:
            self.SO_lineExePath.setText(filepath[0])
            self.default_dir = os.path.dirname(filepath[0])

    def browse_results(self):
        """Open the dialog to select the results directory or the results file,
        if batch decades is enabled.

        """
        if self.batch_networks:
            filepath = QtGui.QFileDialog.getExistingDirectory(self,
                                         caption="Select results directory",
                                         dir=self.default_dir)
        else:
            fullpath = QtGui.QFileDialog.getSaveFileName(self,
                                         caption="Select results file",
                                         dir=self.default_dir,
                                         filter="XLS Spreadsheet (*.xls")[0]

            filepath, filename = os.path.split(fullpath)
            if filename:
                filename = os.path.splitext(filename)[0] + ".xls"
                self.HR_lineResultsName.setText(filename)
        if filepath:
            self.HR_lineResultsPath.setText(filepath)
            self.default_dir = filepath

    def preview_data_file(self, filepath=None):
        """Set the QPlainTextEdit to preview the first 10 lines of a data file.

        """
        if not filepath:
            filepath = self.DL_lineDataPath.text()
        try:
            with open(filepath, 'r+') as datafile:
                lines = str()
                for i in xrange(10):  # @UnusedVariable
                    lines += datafile.readline()
            self.DL_labelDataPathPreview.setText(filepath)
        except IOError:
            lines = "Error loading file: " + filepath
            self.DL_labelDataPathPreview.setText(None)
        self.DL_plainDataPreview.setPlainText(lines)

    def changed_decades_path(self):
        """Try to extract the network id from a decade path, and try to find a
        data file in the same directory.

        """
        # guess network_id
        self.DB_lineNetworkID.setText(os.path.basename(os.path.dirname(
                                           self.DB_lineDecadesPath.text())))
        # try to find a data file
        self.preview_data_file(self.find_data_file())

    def save_settings(self):
        """Store all the user options to QSettings.

        Auxiliary function as a workaround to save on linux (iniformat).

        """
        save = self.settings.setValue

        def _save_lists(key, values):
            if self.linux:
                for i, value in enumerate(values):
                    save(key + "_" + str(i), value)
            else:
                save(key, values)

        # Main Window
        self.settings.beginGroup("main_window")
        save("size", self.size())
        save("position", self.pos())
        save("state", self.saveState())
        save("default_dir", self.default_dir)
        save("print_status", self.print_status)
        _save_lists("recent_settings", self.recent_settings)
        self.settings.endGroup()

        self.settings.beginGroup("Data")
        # Data / Load
        self.settings.beginGroup("Specifications")
        if self.batch_decades:
            save("data_path", self.DB_lineDecadesPath.text())
        else:
            save("data_path", self.DL_lineDataPath.text())
        save("no_data", self.DL_spinNoData.value())
        save("header", self.header)
        save("data_name", self.DL_lineDataName.text())
        varnames = qlist_to_pylist(self.DL_listVarNames)
        _save_lists("variables", varnames)
        self.settings.endGroup()

        # Data / Batch
        self.settings.beginGroup("Batch")
        save("batch_networks", self.batch_networks)
        networks = qlist_to_pylist(self.DB_listNetworksPaths)
        _save_lists("networks_paths", networks)
        save("batch_decades", self.batch_decades)
        if self.batch_decades:
            save("decades_path", self.DB_lineDecadesPath.text())
            save("network_id", self.DB_lineNetworkID.text())
            save("variography_path", self.DB_lineVariogPath.text())
        self.settings.endGroup()

        self.settings.endGroup()
        self.settings.beginGroup("Simulation")
        # Simulation / Options
        self.settings.beginGroup("Options")
        save("par_path", self.SO_lineParPath.text())
        save("exe_path", self.SO_lineExePath.text())
        save("number_simulations", self.SO_spinNumberSims.value())
        save("krigging_type", self.SO_comboKrigType.currentIndex())
        save("max_search_nodes", self.SO_spinMaxSearchNodes.value())
        save("cpu_cores", self.SO_spinCores.value())
        save("skip_sim", self.skip_sim)
        self.settings.endGroup()

        # Simulation / Grid
        self.settings.beginGroup("Grid")
        if not self.batch_networks:
            save("XX_nodes_number", self.SG_spinXXNodes.value())
            save("YY_nodes_number", self.SG_spinYYNodes.value())
            save("ZZ_nodes_number", self.SG_spinZZNodes.value())
            save("XX_minimum", self.SG_spinXXOrig.value())
            save("YY_minimum", self.SG_spinYYOrig.value())
            save("ZZ_minimum", self.SG_spinZZOrig.value())
            save("XX_spacing", self.SG_spinXXSize.value())
            save("YY_spacing", self.SG_spinYYSize.value())
            save("ZZ_spacing", self.SG_spinZZSize.value())
        self.settings.endGroup()

        # Simulation / Variogram
        self.settings.beginGroup("Variogram")
        if not self.batch_decades:
            save("model", self.SV_comboVarModel.currentIndex())
            save("nugget", self.SV_spinNugget.value())
            save("sill", self.SV_spinSill.value())
            save("ranges", self.SV_lineRanges.text())
            save("angles", self.SV_lineAngles.text())
        self.settings.endGroup()

        self.settings.endGroup()
        self.settings.beginGroup("Homogenisation")
        # Homogenisation / Detection
        self.settings.beginGroup("Detection")
        save("station_order", self.HD_comboStationOrder.currentIndex())
        st_order = self.HD_comboStationOrder.currentText().lower()
        if st_order == "user":
            user_order = qlist_to_pylist(self.HD_listUserOrder)
            _save_lists("user_order", user_order)
        else:
            save("ascending", self.HD_checkAscending.isChecked())
            save("md_last", self.HD_checkMDLast.isChecked())
        save("correct_method", self.HD_comboDetectionMethod.currentIndex())
        save("skewness", self.HD_spinSkewness.value())
        save("percentile", self.HD_spinPercentile.value())
        save("detect_prob", self.HD_spinProb.value())
        self.settings.endGroup()

        # Homogenisation / Results
        self.settings.beginGroup("Results")
        save("detect_save", self.HR_checkSaveInter.isChecked())
        save("sim_purge", self.HR_checkPurgeSims.isChecked())
        save("results_path", self.HR_lineResultsPath.text())
        save("results_name", self.HR_lineResultsName.text())
        self.settings.endGroup()

        self.settings.endGroup()

    def load_settings(self):
        """Load and apply all user options from QSettings.

        """
        load = self.settings.value
        # Main Window
        self.settings.beginGroup("main_window")
        self.actionPrintStatus.setChecked(load("print_status"))
        self.settings.endGroup()

        self.settings.beginGroup("Data")
        # Data / Load
        self.settings.beginGroup("Specifications")
        self.DB_lineDecadesPath.setText(load("data_path"))
        self.DL_spinNoData.setValue(load("no_data"))
        self.DL_checkHeader.setChecked(load("header"))
        self.DL_lineDataName.setText(load("data_name"))
        pylist_to_qlist(load("variables"), self.DL_listVarNames)
        self.settings.endGroup()

        # Data / Batch
        self.settings.beginGroup("Batch")
        self.DB_checkBatchNetworks.setChecked(load("batch_networks"))
        pylist_to_qlist(load("networks_paths"), self.DB_listNetworksPaths)
        self.DB_checkBatchDecades.setChecked(load("batch_decades"))
        if self.batch_decades:
            self.DB_lineDecadesPath.setText(load("decades_path"))
            self.DB_lineNetworkID.setText(load("network_id"))
            self.DB_lineVariogPath.setText(load("variography_path"))
        self.settings.endGroup()

        self.settings.endGroup()
        self.settings.beginGroup("Simulation")
        # Simulation / Options
        self.settings.beginGroup("Options")
        self.SO_lineParPath.setText(load("par_path"))
        self.SO_lineExePath.setText(load("exe_path"))
        self.SO_spinNumberSims.setValue(load("number_simulations"))
        self.SO_comboKrigType.setCurrentIndex(load("krigging_type"))
        self.SO_spinMaxSearchNodes.setValue(load("max_search_nodes"))
        self.SO_spinCores.setValue(load("cpu_cores"))
        self.SO_checkSkipSim.setChecked(load("skip_sim"))
        self.settings.endGroup()

        # Simulation / Grid
        self.settings.beginGroup("Grid")
        if not self.batch_networks:
            self.SG_spinXXNodes.setValue(load("XX_nodes_number"))
            self.SG_spinYYNodes.setValue(load("YY_nodes_number"))
            self.SG_spinZZNodes.setValue(load("ZZ_nodes_number"))
            self.SG_spinXXOrig.setValue(load("XX_minimum"))
            self.SG_spinYYOrig.setValue(load("YY_minimum"))
            self.SG_spinZZOrig.setValue(load("ZZ_minimum"))
            self.SG_spinXXSize.setValue(load("XX_spacing"))
            self.SG_spinYYSize.setValue(load("YY_spacing"))
            self.SG_spinZZSize.setValue(load("ZZ_spacing"))
        self.settings.endGroup()

        # Simulation / Variogram
        self.settings.beginGroup("Variogram")
        if not self.batch_decades:
            self.SV_comboVarModel.setCurrentIndex(load("model"))
            self.SV_spinNugget.setValue(load("nugget"))
            self.SV_spinSill.setValue(load("sill"))
            self.SV_lineRanges.setText(load("ranges"))
            self.SV_lineAngles.setText(load("angles"))
        self.settings.endGroup()

        self.settings.endGroup()
        self.settings.beginGroup("Homogenisation")
        # Homogenisation / Detection
        self.settings.beginGroup("Detection")
        self.HD_comboStationOrder.setCurrentIndex(load("station_order"))
        st_order = self.HD_comboStationOrder.currentText().lower()
        if st_order == "user":
            pylist_to_qlist(load("user_order"), self.HD_listUserOrder)
        else:
            self.HD_checkAscending.setChecked(load("ascending"))
            self.HD_checkMDLast.setChecked(load("md_last"))
        self.HD_comboDetectionMethod.setCurrentIndex(load("correct_method"))
        self.HD_spinSkewness.setValue(load("skewness"))
        self.HD_spinPercentile.setValue(load("percentile"))
        self.HD_spinProb.setValue(load("detect_prob"))
        self.settings.endGroup()

        # Homogenisation / Results
        self.settings.beginGroup("Results")
        self.HR_checkSaveInter.setChecked(load("detect_save"))
        self.HR_checkPurgeSims.setChecked(load("sim_purge"))
        self.HR_lineResultsPath.setText(load("results_path"))
        self.HR_lineResultsName.setText(load("results_name"))
        self.settings.endGroup()

        self.settings.endGroup()
        self.apply_settings()

    def load_settings_iniformat(self, qsettings):
        """Load and apply all user options from QSettings in iniformat.

        TODO: needs refactoring as an auxiliary function to load_settings.

        """
        load = qsettings.value

        def _load_lists(key, target):
            if qsettings.contains(key):
                pylist_to_qlist(load(key), target)
            else:
                values = list()
                count = sum(key in child for child in qsettings.childKeys())
                for i in xrange(count):
                    values.append(load(key + "_" + str(i)))
                pylist_to_qlist(values, target)

        def to_bool(u):
            return u in ["true", "True"]

        # Main Window
        qsettings.beginGroup("main_window")
        self.actionPrintStatus.setChecked(to_bool(load("print_status")))
        qsettings.endGroup()

        qsettings.beginGroup("Data")
        # Data / Load
        qsettings.beginGroup("Specifications")
        self.DB_lineDecadesPath.setText(load("data_path"))
        self.DL_spinNoData.setValue(float(load("no_data")))
        self.DL_checkHeader.setChecked(to_bool(load("header")))
        self.DL_lineDataName.setText(load("data_name"))
        _load_lists("variables", self.DL_listVarNames)
        qsettings.endGroup()

        # Data / Batch
        qsettings.beginGroup("Batch")
        self.DB_checkBatchNetworks.setChecked(to_bool(load("batch_networks")))
        _load_lists("networks_paths", self.DB_listNetworksPaths)
        self.DB_checkBatchDecades.setChecked(to_bool(load("batch_decades")))
        if self.batch_decades:
            self.DB_lineDecadesPath.setText(load("decades_path"))
            self.DB_lineNetworkID.setText(load("network_id"))
            self.DB_lineVariogPath.setText(load("variography_path"))
        qsettings.endGroup()

        qsettings.endGroup()
        qsettings.beginGroup("Simulation")
        # Simulation / Options
        qsettings.beginGroup("Options")
        self.SO_lineParPath.setText(load("par_path"))
        self.SO_lineExePath.setText(load("exe_path"))
        self.SO_spinNumberSims.setValue(int(load("number_simulations")))
        self.SO_comboKrigType.setCurrentIndex(int(load("krigging_type")))
        self.SO_spinMaxSearchNodes.setValue(int(load("max_search_nodes")))
        self.SO_spinCores.setValue(int(load("cpu_cores")))
        self.SO_checkSkipSim.setChecked(to_bool(load("skip_sim")))
        qsettings.endGroup()

        # Simulation / Grid
        qsettings.beginGroup("Grid")
        if not self.batch_networks:
            self.SG_spinXXNodes.setValue(int(load("XX_nodes_number")))
            self.SG_spinYYNodes.setValue(int(load("YY_nodes_number")))
            self.SG_spinZZNodes.setValue(int(load("ZZ_nodes_number")))
            self.SG_spinXXOrig.setValue(int(load("XX_minimum")))
            self.SG_spinYYOrig.setValue(int(load("YY_minimum")))
            self.SG_spinZZOrig.setValue(int(load("ZZ_minimum")))
            self.SG_spinXXSize.setValue(int(load("XX_spacing")))
            self.SG_spinYYSize.setValue(int(load("YY_spacing")))
            self.SG_spinZZSize.setValue(int(load("ZZ_spacing")))
        qsettings.endGroup()

        # Simulation / Variogram
        qsettings.beginGroup("Variogram")
        if not self.batch_decades:
            self.SV_comboVarModel.setCurrentIndex(int(load("model")))
            self.SV_spinNugget.setValue(float(load("nugget")))
            self.SV_spinSill.setValue(float(load("sill")))
            self.SV_lineRanges.setText(load("ranges"))
            self.SV_lineAngles.setText(load("angles"))
        qsettings.endGroup()

        qsettings.endGroup()
        qsettings.beginGroup("Homogenisation")
        # Homogenisation / Detection
        qsettings.beginGroup("Detection")
        self.HD_comboStationOrder.setCurrentIndex(int(load("station_order")))
        st_order = self.HD_comboStationOrder.currentText().lower()
        if st_order == "user":
            _load_lists("user_order", self.HD_listUserOrder)
        else:
            self.HD_checkAscending.setChecked(to_bool(load("ascending")))
            self.HD_checkMDLast.setChecked(to_bool(load("md_last")))
        self.HD_comboDetectionMethod.setCurrentIndex(
                                                 int(load("correct_method")))
        self.HD_spinSkewness.setValue(float(load("skewness")))
        self.HD_spinPercentile.setValue(float(load("percentile")))
        self.HD_spinProb.setValue(float(load("detect_prob")))
        qsettings.endGroup()

        # Homogenisation / Results
        qsettings.beginGroup("Results")
        self.HR_checkSaveInter.setChecked(to_bool(load("detect_save")))
        self.HR_checkPurgeSims.setChecked(to_bool(load("sim_purge")))
        self.HR_lineResultsPath.setText(load("results_path"))
        self.HR_lineResultsName.setText(load("results_name"))
        qsettings.endGroup()

        qsettings.endGroup()

    def load_gsimcli_settings(self):
        """Load and apply all user options from already loaded GsimcliParams.

        """
        # Data / Load
        self.DL_lineDataPath.setText(self.params.data)
        self.DL_spinNoData.setValue(self.params.no_data)
        self.DL_checkHeader.setChecked(self.params.data_header)
        try:
            self.DL_lineDataName.setText(self.params.name)
            pylist_to_qlist(self.params.variables, self.DL_listVarNames)
        except(AttributeError):
            # ignore if attributes are not present
            pass

        # Simulation / Options
        # self.SO_lineParPath.setText(self.params.dss_par)
        self.SO_lineExePath.setText(self.params.dss_exe)
        self.SO_spinNumberSims.setValue(self.params.number_simulations)
        self.SO_comboKrigType.setCurrentIndex(self.SO_comboKrigType.findText(
                       self.params.krig_type[0], QtCore.Qt.MatchStartsWith))
        self.SO_spinMaxSearchNodes.setValue(self.params.max_search_nodes)

        # Simulation / Grid
        try:
            self.SG_spinXXNodes.setValue(self.params.XX_nodes_number)
            self.SG_spinYYNodes.setValue(self.params.YY_nodes_number)
            self.SG_spinZZNodes.setValue(self.params.ZZ_nodes_number)
            self.SG_spinXXOrig.setValue(self.params.XX_minimum)
            self.SG_spinYYOrig.setValue(self.params.YY_minimum)
            self.SG_spinZZOrig.setValue(self.params.ZZ_minimum)
            self.SG_spinXXSize.setValue(self.params.XX_spacing)
            self.SG_spinYYSize.setValue(self.params.YY_spacing)
            self.SG_spinZZSize.setValue(self.params.ZZ_spacing)
        except(AttributeError):
            self.DB_checkBatchNetworks.setChecked(True)

        # Simulation / Variogram
        try:
            self.SV_comboVarModel.setCurrentIndex(
                          self.SV_comboVarModel.findText(self.params.model,
                                                 QtCore.Qt.MatchStartsWith))
            self.SV_spinNugget.setValue(self.params.nugget)
            self.SV_spinSill.setValue(self.params.sill)
            self.SV_lineRanges.setText(self.params.ranges)
            self.SV_lineAngles.setText(self.params.angles)
        except(AttributeError):
            self.DB_checkBatchDecades.setChecked(True)
            self.DB_lineDecadesPath.setText(self.params.data)
            self.DL_lineDataPath.clear()

        # Homogenisation / Detection
        st_order = self.params.st_order
        if st_order == "sorted":
            st_order = "id order"
        self.HD_comboStationOrder.setCurrentIndex(
                                  self.HD_comboStationOrder.findText(st_order,
                                                     QtCore.Qt.MatchContains))
        if st_order == "user":
            pylist_to_qlist(self.params.st_user, self.HD_listUserOrder)
        else:
            self.HD_checkAscending.setChecked(self.params.ascending)
            self.HD_checkMDLast.setChecked(self.params.md_last)
        self.HD_comboDetectionMethod.setCurrentIndex(
             self.HD_comboDetectionMethod.findText(self.params.correct_method,
                                                   QtCore.Qt.MatchContains))
        if self.params.correct_method == "skewness":
            self.HD_spinSkewness.setValue(self.params.skewness)
        elif self.params.correct_method == "percentile":
            self.HD_spinPercentile.setValue(self.params.percentile)
        self.HD_spinProb.setValue(self.params.detect_prob)

        # Homogenisation / Results
        self.HR_checkSaveInter.setChecked(self.params.detect_save)
        self.HR_checkPurgeSims.setChecked(self.params.sim_purge)
        if hasattr(self.params, "results_file"):
            self.HR_lineResultsName.setText(
                                    self.params.results_file.decode('utf-8'))
#             results = self.params.results_file
#         else:
#             results = self.params.results
#         self.HR_lineResultsPath.setText(results.decode('utf-8'))
        self.HR_lineResultsPath.setText(self.params.results.decode('utf-8'))

        self.actionGSIMCLI.setEnabled(True)

        self.statusBar().showMessage("Parameters loaded from: {}".
                                     format(self.params.path), 5000)
        if self.print_status:
            print "loaded from: ", self.params.path

    def save_gsimcli_settings(self, par_path=None):
        """Save GsimcliParams from ui options.

        """
        # Data / Load
        if self.batch_decades:
            self.params.data = self.DB_lineDecadesPath.text()
        else:
            self.params.data = self.DL_lineDataPath.text()
        self.params.no_data = self.DL_spinNoData.value()
        self.params.data_header = self.header
        self.params.name = self.DL_lineDataName.text()
        self.params.variables = qlist_to_pylist(self.DL_listVarNames)

        # Simulation / Options
        if self.SO_lineParPath.text():
            self.params.dss_par = self.SO_lineParPath.text()
        self.params.dss_exe = self.SO_lineExePath.text()
        self.params.number_simulations = self.SO_spinNumberSims.value()
        krigtype = self.SO_comboKrigType.currentText()
        if krigtype == "Simple":
            krigtype = "SK"
        elif krigtype == "Ordinary":
            krigtype = "OK"
        self.params.krig_type = krigtype
        self.params.max_search_nodes = self.SO_spinMaxSearchNodes.value()

        # Simulation / Grid
        if not self.batch_networks:
            self.params.XX_nodes_number = self.SG_spinXXNodes.value()
            self.params.YY_nodes_number = self.SG_spinYYNodes.value()
            self.params.ZZ_nodes_number = self.SG_spinZZNodes.value()
            self.params.XX_minimum = self.SG_spinXXOrig.value()
            self.params.YY_minimum = self.SG_spinYYOrig.value()
            self.params.ZZ_minimum = self.SG_spinZZOrig.value()
            self.params.XX_spacing = self.SG_spinXXSize.value()
            self.params.YY_spacing = self.SG_spinYYSize.value()
            self.params.ZZ_spacing = self.SG_spinZZSize.value()

        # Simulation / Variogram
        if not self.batch_decades:
            self.params.model = self.SV_comboVarModel.currentText()[0]
            self.params.nugget = self.SV_spinNugget.value()
            self.params.sill = self.SV_spinSill.value()
            self.params.ranges = self.SV_lineRanges.text()
            self.params.angles = self.SV_lineAngles.text()

        # Homogenisation / Detection
        st_order = self.HD_comboStationOrder.currentText().lower()
        if st_order == "id order":
            st_order = "sorted"
        self.params.st_order = st_order
        if st_order == "user":
            self.params.st_user = qlist_to_pylist(self.HD_listUserOrder)
        else:
            self.params.ascending = self.HD_checkAscending.isChecked()
            self.params.md_last = self.HD_checkMDLast.isChecked()
        self.params.correct_method = (self.HD_comboDetectionMethod.
                                     currentText().lower())
        if self.params.correct_method == "skewness":
            self.params.skewness = self.HD_spinSkewness.value()
        elif self.params.correct_method == "percentile":
            self.params.percentile = self.HD_spinPercentile.value()
        self.params.detect_prob = self.HD_spinProb.value()

        # Homogenisation / Results
        self.params.detect_save = self.HR_checkSaveInter.isChecked()
        self.params.sim_purge = self.HR_checkPurgeSims.isChecked()
        self.params.results = self.HR_lineResultsPath.text().encode('utf-8')
        self.params.results_file = self.HR_lineResultsName.text(
                                                            ).encode('utf-8')

        self.params.save(par_path)
        self.actionGSIMCLI.setEnabled(True)
        self.estimate_necessary_space()

        self.statusBar().showMessage("Parameters saved at: {}".
                                     format(self.params.path), 5000)
        if self.print_status:
            print "saved at: ", self.params.path

    def apply_settings(self):
        """Create or update GsimcliParams file. Connected to dialogbuttonbox.

        """
        self.save_gsimcli_settings(self.temp_params.name)

    def reset_settings(self):
        """Reset all the ui settings. Connected to dialogbuttonbox.

        """
        raise NotImplementedError

    def save_gsimcli_params(self):
        """Update the loaded GsimcliParams file.

        """
        # DEPRECATED
        self.save_gsimcli_settings(self.loaded_params)

    def save_as_gsimcli_params(self):
        """Open the dialog to select a new file to save current settings in
        GsimcliParams format.

        """
        # DEPRECATED
        filepath = QtGui.QFileDialog.getSaveFileName(self,
                                 caption="Save parameters file",
                                 dir=self.default_dir,
                                 filter="Parameters (*.par);;All files (*.*)")
        if filepath[0]:
            self.save_gsimcli_settings(filepath[0])
            self.default_dir = os.path.dirname(filepath[0])
            self.actionSave.setEnabled(True)

    def export_settings(self):
        """Open dialog to select a new file to save current settings in the
        native qsettings format.

        """
        filepath = QtGui.QFileDialog.getSaveFileName(self,
                         caption="Export GSIMCLI settings",
                         dir=self.default_dir,
                         filter="Settings files (*{0})".
                         format(self.settings_ext))
        if filepath[0]:
            filepath = os.path.splitext(filepath[0])[0] + self.settings_ext
            self.save_settings()
            exported = QtCore.QSettings(filepath,
                                        QtCore.QSettings.NativeFormat)
            # FIXME: code smell, allKeys may not work well on all platforms
            for key in self.settings.allKeys():
                exported.setValue(key, self.settings.value(key))
            exported.sync()
            self.add_recent_settings(filepath)
            self.default_dir = os.path.dirname(filepath[0])

    def open_gsimcli_params(self):
        """Open dialog to select an existing GsimcliParams file.

        """
        # DEPRECATED
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                 caption="Open parameters file",
                                 dir=self.default_dir,
                                 filter="Parameters (*.par);;All files (*.*)")
        if filepath[0]:
            self.loaded_params = filepath[0]
            self.params.load(filepath[0])
            self.load_gsimcli_settings()
            self.default_dir = os.path.dirname(filepath[0])
            self.actionSave.setEnabled(True)

    def browse_settings(self):
        """Open dialog to select an existing QSettings file. Connected to
        OpenSettingsFile menu action.

        """
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Open GSIMCLI settings file",
                                     dir=self.default_dir,
                                     filter="Settings files (*{0})".
                                     format(self.settings_ext))
        if filepath[0]:
            self.open_settings(filepath[0])
            self.add_recent_settings(filepath[0])
            self.actionRestoreLastSession.setEnabled(False)
            self.default_dir = os.path.dirname(filepath[0])

    def open_settings(self, filepath):
        """Load and apply ui settings from a QSettings file.

        """
        self.loaded_settings = filepath
        loaded = QtCore.QSettings(filepath, QtCore.QSettings.NativeFormat)
        if self.linux:
            self.load_settings_iniformat(loaded)
        else:
            # FIXME: code smell, allKeys may not work well on all platforms
            for key in loaded.allKeys():
                self.settings.setValue(key, loaded.value(key))
            self.load_settings()
        self.apply_settings()

    def default_varnames(self):
        """Set default variable names.

        TODO: feature not implemented yet.
        """
        pylist_to_qlist(["x", "y", "time", "station", "clim"],
                        self.DL_listVarNames)

    def on_exit(self):
        """Act on application exit. Connected to mainwindow.

        """
        os.remove(self.temp_params.name)

    def available_space(self):
        """Find, show and assess available disc space.

        """
        self.free_space = fs.disk_usage(self.HR_lineResultsPath.text().
                                        encode('utf-8')).free
        self.HR_labelAvailableDiskValue.setText(
                                            fs.bytes2human(self.free_space))
        self.compare_space()

    def estimate_necessary_space(self):
        """Estimate the necessary disc space according to the existing ui
        settings.

        It is only considering the files generated by the simulation process.

        """
        # save total number of simulations
        self.total_sims = 0
        # TODO: estimate for other files
        if self.skip_sim:
            sims_size = 0
        else:
            purge = self.HR_checkPurgeSims.isChecked()
            each_max = 0
            # number of decades
            if self.batch_decades:
                decades = 10
            else:
                decades = 1

            # use all stations or a user-given list
            user_order = (self.HD_comboStationOrder.currentText() == "User")
            if user_order:
                stations_list = qlist_to_pylist(self.HD_listUserOrder)
            else:
                stations_list = self.find_stations_ids()
            # per network
            if self.batch_networks:
                count = 0
                for network in qlist_to_pylist(self.DB_listNetworksPaths):
                    network_id = os.path.basename(network)
                    # simulation grid
                    specf = os.path.join(network, glob.glob(
                                os.path.join(network, self.wildcard_grid))[0])
                    spec = hmg.read_specfile(specf)
                    each_map = (14 * spec.xnodes * spec.ynodes *
                                self.SG_spinZZNodes.value()).values[0]
                    if purge and each_map > each_max:
                        each_max = each_map
                    # number of stations
                    if user_order:
                        n_stations = len(stations_list)
                    else:
                        n_stations = len(stations_list.stations[network_id])
                    # sum up
                    count += each_map * n_stations
                    self.total_sims += n_stations
            # only one network
            else:
                # simulation grid
                each_map = 14 * (self.SG_spinXXNodes.value() *
                                 self.SG_spinYYNodes.value() *
                                 self.SG_spinZZNodes.value())
                # number of stations
                if user_order:
                    n_stations = len(stations_list)
                else:
                    n_stations = stations_list.total
                count = each_map * n_stations
                self.total_sims = n_stations

            if purge:
                count = each_max
                decades = 1

            sims_size = count * self.SO_spinNumberSims.value() * decades
            self.total_sims *= self.SO_spinNumberSims.value() * decades

        self.needed_space = sims_size
        self.HR_labelEstimatedDiskValue.setText(
                                        fs.bytes2human((self.needed_space)))
        self.compare_space()

    def compare_space(self):
        """Compare necessary and available disc spaces. Show warning on ui if
        there is not enough available space.

        """
        size_warning = None
        if self.needed_space and self.needed_space < self.free_space:
            style = "QLabel { color : green }"
        elif self.needed_space and self.free_space:
            style = "QLabel { color : red }"
            size_warning = ("Not enough available space in the selected drive."
                            "\nChoose another drive or enable 'Purge simulated"
                            " maps' to remove them after each detection.")
            self.HR_groupDisk.setToolTip(size_warning)
        else:
            style = None
        self.HR_groupDisk.setToolTip(size_warning)
        self.HR_labelEstimatedDiskValue.setStyleSheet(style)

    def find_stations_ids(self):
        """Find the IDs from all stations contained in the data set being
        processed, whether batch decades or networks are enabled.

        """
        if self.batch_decades:
            secdir = self.wildcard_decade
        else:
            secdir = None
        if self.batch_networks:
            stations_list, total = hmg.list_networks_stations(
                           networks=qlist_to_pylist(self.DB_listNetworksPaths),
                           variables=qlist_to_pylist(self.DL_listVarNames),
                           secdir=secdir, header=self.header, nvars=5)
        else:
            data_path = self.DL_lineDataPath.text()
            if data_path:
                if self.batch_decades:
                    pset_file = hmg.find_pset_file(directory=data_path,
                                                  header=self.header, nvars=5)
                else:
                    pset_file = data_path
                stations_list = hmg.list_stations(pset_file, self.header)
                total = len(stations_list)
            else:
                stations_list = list()
                total = 0

        return hmg._ntuple_stations(stations_list, total)

    def find_data_file(self):
        """Find a data file in the decade or selected network.

        """
        selected_netw = self.DB_listNetworksPaths.currentItem()
        if self.batch_decades and not self.batch_networks:
            directory = self.DB_lineDecadesPath.text()
        elif self.batch_networks and not self.batch_decades and selected_netw:
            directory = selected_netw.text()
        elif self.batch_decades and self.batch_networks and selected_netw:
            network_dir = selected_netw.text()
            directory = os.path.join(network_dir,
                 glob.glob(os.path.join(network_dir, self.wildcard_decade))[0])

        if self.batch_decades or (self.batch_networks and selected_netw):
            return hmg.find_pset_file(directory, self.header, nvars=5)

    def current_network(self, current, previous):
        """Control the file preview, if any selected.

        """
        if current:
            self.preview_data_file(self.find_data_file())

    def check_decades_dir(self):
        """Check if there is a decades folder in every network.

        """
        for network in qlist_to_pylist(self.DB_listNetworksPaths):
            if not glob.glob(os.path.join(network, self.wildcard_decade)):
                return False
        return True

    def check_results_ext(self, text):
        """Make sure the results file has the necessary file extension (.xls).

        """
        if text:
            filename = self.HR_lineResultsName.text()
            if os.path.splitext(filename)[1].lower() != ".xls":
                filename = os.path.splitext(filename)[0] + ".xls"
            self.HR_lineResultsName.setText(filename)
            self.HR_lineResultsName.setCursorPosition(len(filename) - 4)

    def run_gsimcli(self):
        """Launch GSIMCLI process according to the existing ui settings.
        Connected to the GSIMCLI menu action.

        """
        self.apply_settings()
        self.params.path = str(self.params.path)
        self.params.results = str(self.params.results)
        cores = self.SO_spinCores.value()

        if self.batch_networks:
            networks_list = qlist_to_pylist(self.DB_listNetworksPaths)
            # workaround for unicode/bytes issues
            networks_list = map(str, networks_list)
            method_classic.batch_networks(par_path=self.params.path,
                                          networks=networks_list,
                                          decades=self.batch_decades,
                                          skip_dss=self.skip_sim,
                                          print_status=self.print_status,
                                          cores=cores)
        elif self.batch_decades:
            method_classic.batch_decade(par_path=self.params.path,
                            variograms_file=str(self.DB_lineVariogPath.text()),
                            print_status=self.print_status,
                            skip_dss=self.skip_sim,
                            network_id=self.DB_lineNetworkID.text(),
                            cores=cores)
        else:
            method_classic.run_par(par_path=self.params.path,
                                   skip_dss=self.skip_sim,
                                   print_status=self.print_status,
                                   cores=cores)

        self.statusBar().showMessage("Homogenisation process completed.", 5000)
        if self.print_status:
            print "Done."

    def closeEvent(self, event):
        """Event thrown when the MainWindow is closed.

        """
        self.save_settings()
        event.accept()

    def set_progress(self, progress=None):
        """Set the progress of the homogenisation process.

        """
        if not progress:
            progress = 100 * self.current_sim / self.total_sims

        self.progressBar.setValue(progress)

    def set_time(self, seconds):
        """Set the elapsed time of the homogenisation process.

        """
        self.labelTime.setText(seconds_convert(seconds))

    def start_gsimcli(self):
        """Start the homogenisation process, updating its status.
        Connected to the GSIMCLI menu action.

        """
        self.labelStatus.setText("Running...")
        self.groupStatusInfo.setVisible(True)
        self.groupProgress.setVisible(True)
        self.groupTime.setVisible(True)
        self.actionGSIMCLI.setEnabled(False)
        self.start_time = time.time()
        # self.gsimcli_worker.start()
        self.apply_settings()
        self.params.path = str(self.params.path)
        self.params.results = str(self.params.results)
        # new thread
        self.thread = QtCore.QThread()
        # new worker object
        self.worker = Homogenising(self)
        self.worker.time_elapsed.connect(self.set_time)
        self.worker.update_progress.connect(self.set_progress)
        self.worker.finished.connect(self.finish_gsimcli)
        # move object to thread
        self.worker.moveToThread(self.thread)
        # connect the thread's started signal to the worker's processing slot
        self.thread.started.connect(self.worker.run)
        # clean-up, quit thread, mark worker and thread for deletion
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.timer.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.worker.timer.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # go!
        self.thread.start()

    def finish_gsimcli(self):
        """Handle the end of the homogenisation process.
        Connected to the worker thread.

        """
        self.labelStatus.setText("Finished")
        self.groupStatusInfo.setVisible(False)
        self.groupProgress.setVisible(False)
        self.actionGSIMCLI.setEnabled(True)
        self.finish_time = time.time()

    def abort_gsimcli(self):
        """Abort the homogenisation process.
        Connected to the abort button.

        """
        method_classic.is_alive = False
        self.labelStatus.setText("Aborted")
        self.groupStatusInfo.setVisible(False)
        self.groupProgress.setVisible(False)
        self.actionGSIMCLI.setEnabled(True)
        self.worker.is_running = False
        self.finish_time = time.time()


class Homogenising(QtCore.QObject):
    """Homogenising class to handle the thread related to the homogenisation
    process.

    """
    # signals that will be emitted during the processing
    update_progress = QtCore.Signal(int)
    time_elapsed = QtCore.Signal(int)
    finished = QtCore.Signal()

    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.gui = parent
        self.timer = Timer(self)
        self.timer.time_elapsed.connect(self.time_elapsed.emit)
        self.is_running = False

    def run(self):
        self.is_running = True
        self.timer.start(time.time())
        cores = self.gui.SO_spinCores.value()

        if self.gui.batch_networks:
            networks_list = qlist_to_pylist(self.gui.DB_listNetworksPaths)
            # workaround for unicode/bytes issues
            networks_list = map(str, networks_list)
            method_classic.batch_networks(par_path=self.gui.params.path,
                                          networks=networks_list,
                                          decades=self.gui.batch_decades,
                                          skip_dss=self.gui.skip_sim,
                                          print_status=self.gui.print_status,
                                          cores=cores)
        elif self.gui.batch_decades:
            method_classic.batch_decade(par_path=self.gui.params.path,
                        variograms_file=str(self.gui.DB_lineVariogPath.text()),
                        print_status=self.gui.print_status,
                        skip_dss=self.gui.skip_sim,
                        network_id=self.gui.DB_lineNetworkID.text(),
                        cores=cores)
        else:
            method_classic.run_par(par_path=self.gui.params.path,
                                   skip_dss=self.gui.skip_sim,
                                   print_status=self.gui.print_status,
                                   cores=cores)

        self.is_running = False
        # this second is a workaround for the timer QThread removal
        time.sleep(1)
        self.finished.emit()


class Timer(QtCore.QThread):
    """Timer thread for elapsed time.

    """
    time_elapsed = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(Timer, self).__init__(parent)
        self.time_start = None
        self.parent = parent

    def start(self, time_start):
        self.time_start = time_start

        return super(Timer, self).start()

    def run(self):
        while self.parent.is_running:
            self.time_elapsed.emit(time.time() - self.time_start)
            time.sleep(1)


class EmittingStream(QtCore.QObject):
    """Report written data with a QT Signal.

    """
    text_written = QtCore.Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        sys.__stdout__.flush()


def qlist_to_pylist(qlist):
    """Convert QListWidget to Python list.

    Parameters
    ----------
    qlist : QtGui.QListWidget object
        Target QListWidget.

    Returns
    -------
    items : list
        List with the items contained in qlist.

    See Also
    --------
    pylist_to_qlist : Convert Python list into an existing QListWidget.

    """
    items = list()
    for item_row in xrange(qlist.count()):
        items.append(qlist.item(item_row).text())

    return items


def pylist_to_qlist(pylist, qlist):
    """Convert Python list into an existing QListWidget.

    Parameters
    ----------
    pylist : list
        List to be converted.
    qlist : QtGui.QListWidget object
        Existing QListWidget.

    See Also
    --------
    qlist_to_pylist : Convert QListWidget to Python list.

    """
    qlist.clear()
    qlist.addItems(pylist)

    return qlist

# def loadUiWidget(uifilename, parent=None):
#     loader = QtUiTools.QUiLoader()
#     uifile = QtCore.QFile(uifilename)
#     uifile.open(QtCore.QFile.ReadOnly)
#     ui = loader.load(uifile, parent)
#     uifile.close()
#     return ui

# class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
#     def __init__(self):
#         super(MainWindow, self).__init__()
#         self.setupUi(self)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setOrganizationName("ISEGI-NOVA")
    app.setOrganizationDomain("www.isegi.unl.pt")
    app.setApplicationName("GSIMCLI")
    # MainWindow = loadUiWidget("/home/julio/qt/gsimcli.ui")
    MainWindow = GsimcliMainWindow()
    # on exit
    app.aboutToQuit.connect(MainWindow.on_exit)
    MainWindow.show()
    sys.exit(app.exec_())
