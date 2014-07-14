# -*- coding: utf-8 -*-
"""
Created on 16/06/2014

@author: julio
"""

import glob
from PySide import QtCore, QtGui  # , QtUiTools
import os
import sys
from tempfile import NamedTemporaryFile

base = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base)

import external_libs.disk as fs
from external_libs.pyside_dynamic import loadUi
from launchers import method_classic
from parsers.gsimcli import GsimcliParam
import tools.homog as hmg


class MyMainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        # load ui file
        QtGui.QMainWindow.__init__(self, parent)
        loadUi(os.path.join(base, "interface", "gsimcli.ui"), self)
        # QtUiTools.QUiLoader  # try this

        # set params
        self.params = GsimcliParam()
        self.temp_params = NamedTemporaryFile(delete=False)
        self.loaded_params = None
        self.skip_dss = self.SO_checkSkipSim.isChecked()
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
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).clicked.connect(
                                                        self.apply_settings)
        self.DL_buttonDataPath.clicked.connect(self.browse_data_file)
        self.DB_buttonAddNetworks.clicked.connect(self.browse_networks)
        self.DB_buttonRemoveNetworks.clicked.connect(self.remove_networks)
        self.DB_buttonDecadesPath.clicked.connect(self.browse_decades)
        self.DB_buttonVariogPath.clicked.connect(self.browse_variog_file)
        self.SO_buttonExePath.clicked.connect(self.browse_exe_file)
        self.HR_buttonResultsPath.clicked.connect(self.browse_results)

        # change pages
        self.treeWidget.expandAll()
        self.treeWidget.currentItemChanged.connect(self.set_stacked_item)

        # check boxes
        self.DL_checkHeader.toggled.connect(self.enable_header)
        self.DB_checkBatchDecades.toggled.connect(self.enable_batch_decades)
        self.DB_checkBatchNetworks.toggled.connect(self.enable_batch_networks)
        self.SO_checkSkipSim.toggled.connect(self.enable_skip_dss)
        self.actionPrintStatus.toggled.connect(self.disable_print_status)
        self.HR_checkPurgeSims.toggled.connect(self.enable_purge_sims)

        # combo boxes
        self.HD_comboStationOrder.currentIndexChanged.connect(
                                                  self.change_station_order)
        self.HD_comboDetectionMethod.currentIndexChanged.connect(
                                                         self.enable_skewness)

        # hidden
        self.SV_labelBatchDecades.setVisible(False)
        self.HD_groupUserOrder.setVisible(False)

        # line edits
        self.DL_lineDataPath.textChanged.connect(self.preview_data_file)
        self.DB_lineDecadesPath.textChanged.connect(self.changed_decades_path)
        self.HR_lineResultsPath.textChanged.connect(self.available_space)

        # lists
        self.DB_listNetworksPaths.currentItemChanged.connect(
                                                     self.current_network)

        # menu
        self.actionOpen.triggered.connect(self.open_params)
        self.actionSave.triggered.connect(self.save_params)
        self.actionSaveAs.triggered.connect(self.save_as_params)
        self.actionGSIMCLI.triggered.connect(self.run_gsimcli)
        self.actionClose.triggered.connect(
                                   QtCore.QCoreApplication.instance().quit)

        # default
        self.default_varnames()

    def set_stacked_item(self, current, previous):
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

    def enable_header(self, toggle):
        self.header = toggle
        if toggle and self.DL_plainDataPreview.blockCount() > 1:
            self.DL_lineDataName.setText(self.DL_plainDataPreview.toPlainText()
                                         .split(os.linesep)[0])
        else:
            self.DL_lineDataName.clear()

    def enable_decades_group(self, enable):
        self.DB_labelVariogPath.setEnabled(enable)
        self.DB_lineVariogPath.setEnabled(enable)
        self.DB_buttonVariogPath.setEnabled(enable)
        self.DB_labelDecadesPath.setEnabled(enable)
        self.DB_lineDecadesPath.setEnabled(enable)
        self.DB_buttonDecadesPath.setEnabled(enable)
        self.DB_labelNetworkID.setEnabled(enable)
        self.DB_lineNetworkID.setEnabled(enable)

    def disable_datapath_group(self, disable):
        self.DL_labelDataPath.setDisabled(disable)
        self.DL_lineDataPath.setDisabled(disable)
        self.DL_buttonDataPath.setDisabled(disable)

    def enable_batch_networks(self, toggle):
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

        self.estimate_necessary_space()

    def enable_batch_decades(self, toggle):
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

    def enable_skip_dss(self, toggle):
        self.skip_dss = toggle
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
        self.estimate_necessary_space()

    def disable_print_status(self, toggle):
        self.print_status = toggle

    def change_station_order(self, index=None):
        st_order = self.HD_comboStationOrder.currentText()
        order_warning = None
        if st_order == "User":
            if self.DB_listNetworksPaths.count() > 1:
                enable_user = False
                disable_checks = False
                order_warning = ("Not possible to define candidate stations "
                                 "order manually while processing multiple "
                                 "networks.")
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
        if self.HD_comboDetectionMethod.currentText() == "Skewness":
            enable = True
        else:
            enable = False
        self.HD_labelSkewness.setEnabled(enable)
        self.HD_spinSkewness.setEnabled(enable)

    def browse_data_file(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select data file",
                                     dir=os.path.expanduser('~/'))
        if filepath[0]:
            self.DL_lineDataPath.setText(filepath[0])
            self.preview_data_file()
        self.enable_header(self.header)

    def browse_networks(self):
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setDirectory(os.path.expanduser('~/'))
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, True)
        dialog.findChild(QtGui.QListView, "listView").setSelectionMode(
                               QtGui.QAbstractItemView.ExtendedSelection)
        dialog.findChild(QtGui.QTreeView).setSelectionMode(
                               QtGui.QAbstractItemView.ExtendedSelection)
        if dialog.exec_():
            self.DB_listNetworksPaths.addItems(dialog.selectedFiles())
        # update stations order
        self.change_station_order()

    def remove_networks(self):
        for path in self.DB_listNetworksPaths.selectedItems():
            self.DB_listNetworksPaths.takeItem(
                                           self.DB_listNetworksPaths.row(path))
        # update stations order
        self.change_station_order()

    def browse_decades(self):
        dirpath = QtGui.QFileDialog.getExistingDirectory(self,
                                    caption="Select decades directory",
                                    dir=os.path.expanduser('~/'))
        if dirpath:
            self.DB_lineDecadesPath.setText(dirpath)

    def browse_variog_file(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select variography file",
                                     dir=os.path.expanduser('~/'),
                                     filter="Text CSV (*.csv)")
        if filepath[0]:
            self.DB_lineVariogPath.setText(filepath[0])

    def browse_exe_file(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select executable file",
                                     dir=os.path.expanduser('~/'),
                                     filter="Executable (*.exe)")
        if filepath[0]:
            self.SO_lineExePath.setText(filepath[0])

    def browse_results(self):
        filepath = QtGui.QFileDialog.getExistingDirectory(self,
                                     caption="Select results directory",
                                     dir=os.path.expanduser('~/'))
        if filepath:
            self.HR_lineResultsPath.setText(filepath)

    def preview_data_file(self, filepath=None):
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
        # guess network_id
        self.DB_lineNetworkID.setText(os.path.basename(os.path.dirname(
                                           self.DB_lineDecadesPath.text())))
        # try to find a data file
        self.preview_data_file(self.find_data_file())

    def load_settings(self):
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
             self.HD_comboDetectionMethod.findText(self.params.detect_method,
                                                   QtCore.Qt.MatchContains))
        if self.params.detect_method == "skewness":
            self.HD_spinSkewness.setValue(self.params.skewness)
        self.HD_spinProb.setValue(self.params.detect_prob)

        # Homogenisation / Results
        self.HR_checkSaveInter.setChecked(self.params.detect_save)
        self.HR_checkPurgeSims.setChecked(self.params.sim_purge)
        self.HR_lineResultsPath.setText(self.params.results.decode('utf-8'))

        self.actionGSIMCLI.setEnabled(True)

        self.statusBar().showMessage("Parameters loaded from: {}".
                                     format(self.params.path), 5000)
        if self.print_status:
            print "loaded from: ", self.params.path

    def save_settings(self, par_path=None):
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
        self.params.detect_method = (self.HD_comboDetectionMethod.
                                     currentText().lower())
        if self.params.detect_method == "skewness":
            self.params.skewness = self.HD_spinSkewness.value()
        self.params.detect_prob = self.HD_spinProb.value()

        # Homogenisation / Results
        self.params.detect_save = self.HR_checkSaveInter.isChecked()
        self.params.sim_purge = self.HR_checkPurgeSims.isChecked()
        self.params.results = str(self.HR_lineResultsPath.text())

        self.params.save(par_path)
        self.actionGSIMCLI.setEnabled(True)
        self.estimate_necessary_space()

        self.statusBar().showMessage("Parameters saved at: {}".
                                     format(self.params.path), 5000)
        if self.print_status:
            print "saved at: ", self.params.path

    def run_gsimcli(self):
        self.apply_settings()
        self.params.path = str(self.params.path)
        self.params.results = str(self.params.results)

        if self.batch_networks:
            networks_list = qlist_to_pylist(self.DB_listNetworksPaths)
            # workaround for unicode/bytes issues
            networks_list = map(str, networks_list)
            method_classic.batch_networks(par_path=self.params.path,
                                          networks=networks_list,
                                          decades=self.batch_decades,
                                          skip_dss=self.skip_dss,
                                          print_status=self.print_status)
        elif self.batch_decades:
            method_classic.batch_decade(par_path=self.params.path,
                            variograms_file=str(self.DB_lineVariogPath.text()),
                            print_status=self.print_status,
                            skip_dss=self.skip_dss,
                            network_id=self.DB_lineNetworkID.text())
        else:
            method_classic.run_par(par_path=self.params.path,
                                   skip_dss=self.skip_dss,
                                   print_status=self.print_status)

        self.statusBar().showMessage("Homogenisation process completed.", 5000)
        if self.print_status:
            print "Done."

    def apply_settings(self):
        self.save_settings(self.temp_params.name)

    def save_params(self):
        self.save_settings(self.loaded_params)

    def save_as_params(self):
        filepath = QtGui.QFileDialog.getSaveFileName(self,
                                 caption="Save parameters file",
                                 dir=os.path.expanduser('~/'),
                                 filter="Parameters (*.par);;All files (*.*)")
        if filepath[0]:
            self.save_settings(filepath[0])
            self.actionSave.setEnabled(True)

    def open_params(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                 caption="Open parameters file",
                                 dir=os.path.expanduser('~/'),
                                 filter="Parameters (*.par);;All files (*.*)")
        if filepath[0]:
            self.loaded_params = filepath[0]
            self.params.load(filepath[0])
            self.load_settings()
            self.actionSave.setEnabled(True)

    def default_varnames(self):
        pylist_to_qlist(["x", "y", "time", "station", "clim"],
                        self.DL_listVarNames)

    def on_exit(self):
        os.remove(self.temp_params.name)

    def available_space(self):
        self.free_space = fs.disk_usage(self.HR_lineResultsPath.text()).free
        self.HR_labelAvailableDiskValue.setText(
                                            fs.bytes2human(self.free_space))
        self.compare_space()

    def estimate_necessary_space(self):
        # TODO: estimate for other files
        if self.skip_dss:
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
            if self.HD_comboStationOrder.currentText() == "User":
                stations_list = self.HD_line
            stations_list = self.find_stations_ids()
            # per nerwork
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
                    n_stations = len(stations_list.stations[network_id])
                    # sum up
                    count += each_map * n_stations
            # only one network
            else:
                # simulation grid
                each_map = 14 * (self.SG_spinXXNodes.value() *
                                 self.SG_spinYYNodes.value() *
                                 self.SG_spinZZNodes.value())
                # number of stations
                n_stations = stations_list.total
                count = each_map * n_stations

            if purge:
                count = each_max
                decades = 1

            sims_size = count * self.SO_spinNumberSims.value() * decades

        self.needed_space = sims_size
        self.HR_labelEstimatedDiskValue.setText(
                                        fs.bytes2human((self.needed_space)))
        self.compare_space()

    def compare_space(self):
        size_warning = None
        if self.needed_space and self.needed_space < self.free_space:
            style = "QLabel { color : green }"
        elif self.needed_space:
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
        self.preview_data_file(self.find_data_file())

    def check_decades_dir(self):
        for network in qlist_to_pylist(self.DB_listNetworksPaths):
            if not glob.glob(os.path.join(network, self.wildcard_decade)):
                return False
        return True


def qlist_to_pylist(qlist):
    items = list()
    for item_row in xrange(qlist.count()):
        items.append(qlist.item(item_row).text())

    return items


def pylist_to_qlist(pylist, qlist):
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
    # MainWindow = loadUiWidget("/home/julio/qt/gsimcli.ui")
    MainWindow = MyMainWindow()
    # on exit
    app.aboutToQuit.connect(MainWindow.on_exit)
    MainWindow.show()
    sys.exit(app.exec_())
