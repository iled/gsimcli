#!/usr/bin/env python
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
import warnings

base = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base)

import external_libs.disk as fs
from external_libs.pyside_dynamic import loadUi
from launchers import method_classic
import pandas as pd
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
        self.settings.setIniCodec("UTF-8")
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
        self.set_gui_params()

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
        self.HD_checkTolerance.toggled.connect(self.enable_tolerance)
        self.HR_checkPurgeSims.toggled.connect(self.enable_purge_sims)

        # combo boxes
        self.SA_comboStrategy.currentIndexChanged.connect(
                                                      self.enable_maxsamples)
        self.HD_comboStationOrder.currentIndexChanged.connect(
                                                  self.change_station_order)
        self.HC_comboCorrectionMethod.currentIndexChanged.connect(
                                                         self.enable_skewness)
        self.HC_comboCorrectionMethod.currentIndexChanged.connect(
                                                     self.enable_percentile)

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
        self.SO_spinMaxSearchNodes.valueChanged.connect(self.set_max_nodes)
        self.SA_spinMaxNodes.valueChanged.connect(self.set_max_nodes)

        # hidden widgets by default
        self.set_hidden([self.groupProgress, self.groupStatusInfo,
                         self.groupTime,
                         self.SI_labelNetwork, self.SI_labelStatusNetwork,
                         self.SI_labelDecade, self.SI_labelStatusDecade,
                         self.SV_labelBatchDecades,
                         self.SA_labelMaxSamples, self.SA_spinMaxSamples,
                         self.HD_groupUserOrder, self.HD_groupTolerance,
                         self.HC_groupSkewness, self.HC_groupPercentile])

        # default
        self.default_varnames()

        # install the custom output stream
        sys.stdout = EmittingStream()
        sys.stdout.text_written.connect(self.output_status)

        # initialise status counters
        self.set_counters()

    def __del__(self):
        """ Restore sys.stdout. """
        sys.stdout = sys.__stdout__

    def set_gui_params(self):
        """Set the GUI parameters.

        To add new parameters, follow the model:

        >>> new_par = GuiParam("par name", self.Qt_widget, group, dependencies,
                           "name in the gsimcli par file")
        >>> add(new_par)

        """
        # set the GUI parameters
        self.guiparams = list()
        add = self.guiparams.extend
        #    Main Window
        #         gp = "main_window"
        #         size = GuiParam("size", widget=self, group=gp)
        #         pos = GuiParam("position", widget=self, group=gp)
        #         state = GuiParam("state", widget=self, group=gp)
        #                          get_value=self.saveState)
        #         defaultdir = GuiParam("default_dir", widget=self, group=gp,
        #                               get_value=self.default_dir)
        #         printstatus = GuiParam("print_status", widget=self, group=gp,
        #                                get_value=self.print_status)
        #         recent_settings = GuiParam("recent_settings", widget=self,
        #                                    group=gp, otype=list,
        #                                    get_value=self.recent_settings)
        #    Data / Load
        gp = "data_load"
        data_path = GuiParam("data_path", self.DL_lineDataPath, group=gp,
                             depends=lambda: not self.batch_decades,
                             gsimcli_name="data")
        no_data = GuiParam("no_data", self.DL_spinNoData, group=gp,
                           gsimcli_name="no_data")
        header = GuiParam("header", self.DL_checkHeader, group=gp,
                          gsimcli_name="data_header")
        data_name = GuiParam("data_name", self.DL_lineDataName, group=gp,
                             gsimcli_name="name")
        varnames = GuiParam("variables", self.DL_listVarNames, group=gp,
                            gsimcli_name="variables")
        add([data_path, no_data, header, data_name, varnames])
        #    Data / Batch
        gp = "data_batch"
        batch_networks = GuiParam("batch_networks", self.DB_checkBatchNetworks,
                                  group=gp)
        network_paths = GuiParam("networks_paths", self.DB_listNetworksPaths,
                                 group=gp, depends=batch_networks)
        batch_decades = GuiParam("batch_decades", self.DB_checkBatchDecades,
                                 group=gp)
        dec_path = GuiParam("decades_path", self.DB_lineDecadesPath, group=gp,
                            depends=[batch_decades, lambda: not
                                     self.batch_networks])
        network_id = GuiParam("network_id", self.DB_lineNetworkID, group=gp,
                              depends=[batch_decades, lambda: not
                                       self.batch_networks])
        var_path = GuiParam("variography_path", self.DB_lineVariogPath,
                            group=gp, depends=[batch_decades, lambda: not
                                               self.batch_networks])
        add([batch_networks, network_paths, batch_decades, dec_path,
             network_id, var_path])
        #    Simulation / Options
        gp = "simulation_options"
        par_path = GuiParam("par_path", self.SO_lineParPath, group=gp,
                            gsimcli_name="dss_par")
        exe_path = GuiParam("exe_path", self.SO_lineExePath, group=gp,
                            gsimcli_name="dss_exe")
        n_sims = GuiParam("number_simulations", self.SO_spinNumberSims,
                          group=gp, gsimcli_name="number_simulations")
        krig_type = GuiParam("krigging_type", self.SO_comboKrigType, group=gp,
                             gsimcli_name="krig_type")
        max_nodes = GuiParam("max_search_nodes", self.SO_spinMaxSearchNodes,
                             group=gp, gsimcli_name="max_search_nodes")
        cpu_cores = GuiParam("cpu_cores", self.SO_spinCores, group=gp)
        skip_sim = GuiParam("skip_sim", self.SO_checkSkipSim, group=gp)
        add([par_path, exe_path, n_sims, krig_type, max_nodes, cpu_cores,
             skip_sim])
        #    Simulation / Grid
        gp = "simulation_grid"
        xx_nodes_n = GuiParam("XX_nodes_number", self.SG_spinXXNodes,
                              group=gp, gsimcli_name="XX_nodes_number",
                              depends=lambda: not self.batch_networks)
        yy_nodes_n = GuiParam("YY_nodes_number", self.SG_spinYYNodes,
                              group=gp, gsimcli_name="YY_nodes_number",
                              depends=lambda: not self.batch_networks,)
        zz_nodes_n = GuiParam("ZZ_nodes_number", self.SG_spinZZNodes,
                              group=gp, gsimcli_name="ZZ_nodes_number",
                              depends=lambda: not self.batch_networks,)
        xx_min = GuiParam("XX_minimum", self.SG_spinXXOrig, group=gp,
                          depends=lambda: not self.batch_networks,
                          gsimcli_name="XX_minimum")
        yy_min = GuiParam("YY_minimum", self.SG_spinYYOrig, group=gp,
                          depends=lambda: not self.batch_networks,
                          gsimcli_name="YY_minimum")
        zz_min = GuiParam("ZZ_minimum", self.SG_spinZZOrig, group=gp,
                          depends=lambda: not self.batch_networks,
                          gsimcli_name="ZZ_minimum")
        xx_spacing = GuiParam("XX_spacing", self.SG_spinXXSize, group=gp,
                              depends=lambda: not self.batch_networks,
                              gsimcli_name="XX_spacing")
        yy_spacing = GuiParam("YY_spacing", self.SG_spinYYSize, group=gp,
                              depends=lambda: not self.batch_networks,
                              gsimcli_name="YY_spacing")
        zz_spacing = GuiParam("ZZ_spacing", self.SG_spinZZSize, group=gp,
                              depends=lambda: not self.batch_networks,
                              gsimcli_name="ZZ_spacing")
        add([xx_nodes_n, yy_nodes_n, zz_nodes_n, xx_min, yy_min, zz_min,
             xx_spacing, yy_spacing, zz_spacing])
        #    Simulation / Variogram
        gp = "simulation_variogram"
        varmodel = GuiParam("model", self.SV_comboVarModel, group=gp,
                            depends=lambda: not self.batch_decades,
                            gsimcli_name="model")
        nugget = GuiParam("nugget", self.SV_spinNugget, group=gp,
                          depends=lambda: not self.batch_decades,
                          gsimcli_name="nugget")
        sill = GuiParam("sill", self.SV_spinSill, group=gp,
                        depends=lambda: not self.batch_decades,
                        gsimcli_name="sill")
        ranges = GuiParam("ranges", self.SV_lineRanges, group=gp,
                          depends=lambda: not self.batch_decades,
                          gsimcli_name="ranges")
        varangles = GuiParam("angles", self.SV_lineAngles, group=gp,
                             depends=lambda: not self.batch_decades,
                             gsimcli_name="angles")
        add([varmodel, nugget, sill, ranges, varangles])
        #    Simulation / Advanced
        gp = "simulation_advanced"
        strategy = GuiParam("search_strategy", self.SA_comboStrategy, group=gp,
                            gsimcli_name="search_strategy")
        min_data = GuiParam("min_data", self.SA_spinMinData, group=gp,
                            gsimcli_name="min_data")
        max_samples = GuiParam("max_search_samples", self.SA_spinMaxSamples,
                               group=gp, gsimcli_name="max_search_samples",
                               depends=lambda: strategy.widget.
                               currentText().lower() == "two-part search")
        search_radius = GuiParam("search_radius", self.SA_lineRadius, group=gp,
                                 gsimcli_name="search_radius")
        search_angles = GuiParam("search_angles", self.SA_lineAngles, group=gp,
                                 gsimcli_name="search_angles")
        add([strategy, min_data, max_samples, search_radius, search_angles])
        #    Homogenisation / Detection
        gp = "homogenisation_detection"
        station_order = GuiParam("station_order", self.HD_comboStationOrder,
                                 group=gp, gsimcli_name="st_order")
        user_order = GuiParam("user_order", self.HD_listUserOrder, group=gp,
                              gsimcli_name="st_user",
                              depends=lambda: station_order.widget.
                              currentText().lower() == "user")
        ascending = GuiParam("ascending", self.HD_checkAscending, group=gp,
                             gsimcli_name="ascending",
                             depends=lambda: not station_order.widget.
                             currentText().lower() == "user")
        md_last = GuiParam("md_last", self.HD_checkMDLast, group=gp,
                           gsimcli_name="md_last",
                           depends=lambda: not station_order.widget.
                           currentText().lower() == "user")
        detect_prob = GuiParam("detect_prob", self.HD_spinProb, group=gp,
                               gsimcli_name="detect_prob")
        tolerance = GuiParam("tolerance", self.HD_checkTolerance, group=gp,
                             gsimcli_name="tolerance")
        radius = GuiParam("radius", self.HD_spinTolerance, group=gp,
                          depends=tolerance, gsimcli_name="radius")
        dist_units = GuiParam("distance_units", self.HD_radioDistance,
                              group=gp, depends=tolerance,
                              gsimcli_name="distance_units")
        add([station_order, user_order, ascending, md_last, detect_prob,
             tolerance, radius, dist_units])
        #    Homogenisation / Correction
        gp = "homogenisation_correction"
        correct = GuiParam("correct_method", self.HC_comboCorrectionMethod,
                           group=gp, gsimcli_name="correct_method")
        skew = GuiParam("skewness", self.HC_spinSkewness, group=gp,
                        depends=lambda: correct.widget.
                        currentText().lower() == "skewness",
                        gsimcli_name="skewness")
        perc = GuiParam("percentile", self.HC_spinPercentile, group=gp,
                        depends=lambda: correct.widget.
                        currentText().lower() == "percentile",
                        gsimcli_name="percentile")
        add([correct, skew, perc])
        #    Homogenisation / Results
        gp = "homogenisation_results"
        detect_save = GuiParam("detect_save", self.HR_checkSaveInter, group=gp,
                               gsimcli_name="detect_save")
        sim_purge = GuiParam("sim_purge", self.HR_checkPurgeSims, group=gp,
                             gsimcli_name="sim_purge")
        r_path = GuiParam("results_path", self.HR_lineResultsPath, group=gp,
                          gsimcli_name="results")
        r_name = GuiParam("results_name", self.HR_lineResultsName, group=gp,
                          gsimcli_name="results_file")
        add([detect_save, sim_purge, r_path, r_name])

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
            info_object = self.SI_labelStatusNetwork
            self.count_status[0] += 1
        elif "STATUS: decade" in text:
            info_object = self.SI_labelStatusDecade
            self.count_status[1] += 1
        elif "STATUS: candidate" in text:
            info_object = self.SI_labelStatusStation
            self.count_status[2] += 1
            self.current_sim = (self.SO_spinNumberSims.value() *
                                self.count_status[2])
        elif "STATUS: realization" in text:
            info_object = self.SI_labelStatusSim
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
        """Connect the right menu (QTreeWidget) with the panels on the right
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
        elif tree_item == "Correction":
            self.stackedWidget.setCurrentWidget(self.HomogenisationCorrection)
        elif tree_item == "Results":
            self.stackedWidget.setCurrentWidget(self.HomogenisationResults)

    def set_max_nodes(self, i):
        """Sync both spin boxes that handle the maximum number of nodes to be
        found.
        Connected to SO_spinMaxSearchNodes and SA_spinMaxNodes.

        """
        self.SO_spinMaxSearchNodes.setValue(i)
        self.SA_spinMaxNodes.setValue(i)

    def set_recent_settings(self):
        """Create the recent settings files menu. Filter non
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

    def set_hidden(self, widgets):
        """Hide a list of widgets.

        """
        for widget in widgets:
            widget.setVisible(False)

    def set_counters(self):
        """Initialise or reset the counters that keep track current status:
        network, decade, candidate, simulation.

        """
        self.count_status = [0, 0, 0, 0]
        self.total_sims = 0
        self.current_sim = 0

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
        option for Simulation\Grid.
        Connected to the batch networks checkbox.

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

        # toggle status info
        self.SI_labelNetwork.setVisible(toggle)
        self.SI_labelStatusNetwork.setVisible(toggle)

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

        # toggle status info
        self.SI_labelDecade.setVisible(toggle)
        self.SI_labelStatusDecade.setVisible(toggle)

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
            if self.batch_networks and self.DB_listNetworksPaths.count() > 1:
                enable_user = False
                disable_checks = False
                order_warning = ("Not possible to define candidate stations "
                                 "order manually while processing multiple "
                                 "networks.")
            elif ((not self.DL_lineDataPath.text() and not self.batch_networks)
                  or (self.batch_networks and
                      self.DB_listNetworksPaths.count() < 1)):
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

    def enable_tolerance(self, toggle):
        """Toggle the widgets related to the tolerance feature on the local
        PDF calculation.

        """
        self.HD_groupTolerance.setVisible(toggle)

    def enable_skewness(self, index):
        """Toggle the widgets related to the skewness correction method.
        Connected to the correction method combobox.

        """
        if self.HC_comboCorrectionMethod.currentText() == "Skewness":
            enable = True
        else:
            enable = False
        self.HC_groupSkewness.setVisible(enable)

    def enable_percentile(self, index):
        """Toggle the widgets related to the percentile correction method.
        Connected to the correction method combobox.

        """
        if self.HC_comboCorrectionMethod.currentText() == "Percentile":
            enable = True
        else:
            enable = False
        self.HC_groupPercentile.setVisible(enable)

    def enable_maxsamples(self, index):
        """Toggle the widgets related to the two-part search strategy.
        Connected to the search strategy combobox.

        """
        if self.SA_comboStrategy.currentText() == "Two-part search":
            enable = True
        else:
            enable = False
        self.SA_labelMaxSamples.setVisible(enable)
        self.SA_spinMaxSamples.setVisible(enable)

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

    def save_settings(self, settings=None):
        """Store all the user options to QSettings.

        """
        if settings:
            save = settings.setValue
        else:
            settings = self.settings
            save = self.settings.setValue

        def _save_lists(key, values):
            if self.linux:
                for i, value in enumerate(values):
                    save(key + "_" + str(i), value)
            else:
                save(key, values)

        # Main Window
        settings.beginGroup("main_window")
        save("size", self.size())
        save("position", self.pos())
        save("state", self.saveState())
        save("default_dir", self.default_dir)
        save("print_status", self.print_status)
        _save_lists("recent_settings", self.recent_settings)
        settings.endGroup()
        # Other groups
        group = str()
        for param in self.guiparams:
            if param.group != group:
                if group:
                    settings.endGroup()
                group = param.group
                settings.beginGroup(group)

            if param.has_data() and param.check_dependencies():
                save(*param.save())
        settings.endGroup()

    def load_settings(self, settings):
        """Load and apply all user options from QSettings.

        """
        value = settings.value

        # Main Window
        settings.beginGroup("main_window")
        self.actionPrintStatus.setChecked(bool(value("print_status")))
        settings.endGroup()
        # Other groups
        group = str()
        for param in self.guiparams:
            if param.group != group:
                if group:
                    settings.endGroup()
                group = param.group
                settings.beginGroup(group)

            if value(param.name) is not None and param.check_dependencies():
                param.load(value(param.name))

        settings.endGroup()

    def load_gsimcli_settings(self):
        """Load and apply all user options from already loaded GsimcliParams.

        DEPRECATED
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

        # Simulation / Advanced
        self.SA_lineRadius.setText(self.params.search_radius)

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
        self.HD_spinProb.setValue(self.params.detect_prob)
        self.HD_checkTolerance.setChecked(self.params.tolerance)
        if self.HD_checkTolerance.isChecked():
            self.HD_spinTolerance.setValue(self.params.radius)
            self.HD_radioDistance(self.params.distance_units)

        # Homogenisation / Correction
        self.HC_comboCorrectionMethod.setCurrentIndex(
             self.HC_comboCorrectionMethod.findText(self.params.correct_method,
                                                   QtCore.Qt.MatchContains))
        if self.params.correct_method == "skewness":
            self.HC_spinSkewness.setValue(self.params.skewness)
        elif self.params.correct_method == "percentile":
            self.HC_spinPercentile.setValue(self.params.percentile)

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
        gspar = self.params
        for param in self.guiparams:
            name = param.gsimcli_name
            if name is not None:
                if param.check_dependencies() and param.has_data():
                    # krigging type
                    if name == "krig_type":
                        krigtype = self.SO_comboKrigType.currentText()
                        if krigtype == "Simple":
                            krigtype = "SK"
                        elif krigtype == "Ordinary":
                            krigtype = "OK"
                        gspar.krig_type = krigtype
                    # variogram model
                    elif name == "model":
                        model = self.SV_comboVarModel.currentText()[0]
                        gspar.model = model
                    # station order
                    elif name == "st_order":
                        st_order = (self.HD_comboStationOrder.
                                    currentText().lower())
                        if st_order == "id order":
                            st_order = "sorted"
                        gspar.st_order = st_order
                    elif name == "correct_method":
                        gspar.correct_method = (self.HC_comboCorrectionMethod.
                                                currentText().lower())
                    # other params
                    elif name in ["results", "results_file"]:
                        setattr(gspar, name, param.value.encode('utf-8'))
                    else:
                        pname, value = param.save_gsimcli()
                        setattr(gspar, pname, value)

        self.params.save(par_path)
        self.actionGSIMCLI.setEnabled(True)
        self.estimate_necessary_space()

        self.statusBar().showMessage("gsimcli parameters saved at: {}".
                                     format(self.params.path), 5000)
        if self.print_status:
            print "gsimcli parameters saved at: ", self.params.path

    def apply_settings(self):
        """Create or update GsimcliParams file. Connected to dialogbuttonbox.

        """
        self.save_gsimcli_settings(self.temp_params.name)

    def reset_settings(self):
        """Reset all the ui settings. Connected to dialogbuttonbox.

        """
        self.settings.clear()
        raise NotImplementedError

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
            exported = QtCore.QSettings(filepath,
                                        QtCore.QSettings.NativeFormat)
            exported.setIniCodec("UTF-8")
            # clear existing settings on the file
            exported.clear()
            self.save_settings(exported)
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
        self.load_settings(loaded)
        self.save_settings()
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
        """Find, show and assess available disk space.

        """
        self.free_space = fs.disk_usage(self.HR_lineResultsPath.text().
                                        encode('utf-8')).free
        self.HR_labelAvailableDiskValue.setText(
                                            fs.bytes2human(self.free_space))
        self.compare_space()

    def count_decades(self, network):
        """Find the variography file for a given network and count the number
        of decades in that network.

        """
        variogram_file = os.path.join(network, glob.glob(
                             os.path.join(network, self.wildcard_variog))[0])
        variograms = pd.read_csv(variogram_file)
        return variograms.shape[0]

    def estimate_necessary_space(self):
        """Estimate the necessary disk space according to the existing ui
        settings.

        It is only considering the files generated by the simulation process.

        """
        # initialise the number of decades
        if self.batch_decades:
            decades = 10
        else:
            decades = 1
        # save total number of simulations
        self.total_sims = 0
        # TODO: estimate for other files
        if self.skip_sim:
            sims_size = 0
        else:
            purge = self.HR_checkPurgeSims.isChecked()
            each_max = 0

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
                    # number of decades
                    decades = self.count_decades(network)
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
                decades_factor = 1
            else:
                decades_factor = decades

            sims_size = count * self.SO_spinNumberSims.value() * decades_factor
            self.total_sims *= self.SO_spinNumberSims.value() * decades

        self.needed_space = sims_size
        self.HR_labelEstimatedDiskValue.setText(
                                        fs.bytes2human((self.needed_space)))
        self.compare_space()

    def compare_space(self):
        """Compare necessary and available disk spaces. Show warning on ui if
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
        varnames = qlist_to_pylist(self.DL_listVarNames)
        if self.batch_networks:
            stations_list, total = hmg.list_networks_stations(
                           networks=qlist_to_pylist(self.DB_listNetworksPaths),
                           variables=varnames,
                           secdir=secdir, header=self.header, nvars=5)
        else:
            data_path = self.DL_lineDataPath.text()
            stations_list = dict()
            if data_path:
                if self.batch_decades:
                    pset_file = hmg.find_pset_file(directory=data_path,
                                                  header=self.header, nvars=5)
                else:
                    pset_file = data_path
                stations = hmg.list_stations(pset_file, self.header,
                                                  variables=varnames)
                total = len(stations)
                stations_list[os.path.dirname(data_path)] = stations
            else:
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
        self.enable_header(self.header)

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
        self.set_counters()
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


class GuiParam(object):
    """Hold the necessary settings to manage each GUI parameter.

    """
    def __init__(self, name, widget, group, depends=None, gsimcli_name=None):
        """Constructor to initialise a GUI parameter.

        Parameters
        ----------
        name : string
            Name of the parameter that will be used to store its value in the
            GUI settings file.
        widget : QObject
            Qt widget instance related to the parameter.
        group : string
            Settings group that the parameter belongs to.
        depends : list of function or list of GuiParam instance, optional
            Functions to retrieve values from other widgets, or GuiParam
            instances, that the parameter depends on.
        gsimcli_name : string, optional
            Name of the parameter in the GsimcliParam class. If given, it will
            check if it exists in the class definition and it will warn if it
            does not exist.

        """
        self.name = name
        self.widget = widget
        self.group = group
        if isinstance(depends, list) or depends is None:
            self.depends = depends
        else:
            self.depends = [depends]
        self.gsimcli_name = gsimcli_name

        if gsimcli_name:
            self.check_gsimcli_params()

        self.update()

    def check_dependencies(self):
        """A widget may depend on the value of another widget. This method
        checks if all the parameter dependencies are met. Returns True if all
        dependencies are satisfied or if it has no dependencies.

        Only boolean values are supported for the dependencies.

        """
        if self.depends:
            for dependency in self.depends:
                if isinstance(dependency, GuiParam):
                    dep = dependency.value
                elif callable(dependency):
                    dep = dependency()
                else:
                    raise TypeError("dependencies must be callables or "
                                    "instances of GuiParam, got {} instead."
                                    .format(type(dependency)))
                if not dep:
                    return False
        return True

    def check_gsimcli_params(self):
        """Check if the parameter is included in the GsimcliParam class
        docstring. A warn message will be thrown if it is not included, as a
        reminder.

        """
        if self.gsimcli_name in GsimcliParam.__doc__:
            return True
        else:
            warnings.warn("The parameter {} is not properly configured in "
                          "GsimcliParam class. Please check if it is included "
                          "in the docstring and in the fields or optional "
                          "lists.".format(self.name))
            return False

    def update(self):
        if isinstance(self.widget, GsimcliMainWindow):
            pass
        if isinstance(self.widget, QtGui.QLineEdit):
            self.value = self.widget.text()
        if isinstance(self.widget, QtGui.QSpinBox):
            self.value = self.widget.value()
        if isinstance(self.widget, QtGui.QDoubleSpinBox):
            self.value = self.widget.value()
        if isinstance(self.widget, QtGui.QListWidget):
            self.value = qlist_to_pylist(self.widget)
        if isinstance(self.widget, QtGui.QComboBox):
            self.value = self.widget.currentIndex()
        if (isinstance(self.widget, QtGui.QCheckBox) or
                isinstance(self.widget, QtGui.QRadioButton)):
            self.value = self.widget.isChecked()

    def load(self, value):
        def to_bool(u):
            return u in ["true", "True", True]

        if isinstance(self.widget, GsimcliMainWindow):
            pass
        elif isinstance(self.widget, QtGui.QLineEdit):
            self.widget.setText(str(value))
        elif isinstance(self.widget, QtGui.QSpinBox):
            self.widget.setValue(int(value))
        elif isinstance(self.widget, QtGui.QDoubleSpinBox):
            self.widget.setValue(float(value))
        elif isinstance(self.widget, QtGui.QListWidget):
            pylist_to_qlist(value, self.widget)
        elif isinstance(self.widget, QtGui.QComboBox):
            self.widget.setCurrentIndex(int(value))
        elif (isinstance(self.widget, QtGui.QCheckBox) or
                isinstance(self.widget, QtGui.QRadioButton)):
            self.widget.setChecked(to_bool(value))

        self.update()

    def save(self):
        """Provide an interface to save the parameter value in QSettings.

        """
        self.update()
        return (self.name, self.value)

    def save_gsimcli(self):
        """Provide an interface to save the parameter value in the gsimcli
        parameters file.

        """
        self.update()
        return (self.gsimcli_name, self.value)

    def has_data(self):
        """Return True if the widget's value is has some data (it's not empty).

        """
        self.update()
        try:
            it_has = bool(len(self.value))
        except TypeError:
            it_has = True
        return it_has


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
    if not isinstance(pylist, list):
        pylist = [pylist]

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
    app.setApplicationName("gsimcli")
    # MainWindow = loadUiWidget("/home/julio/qt/gsimcli.ui")
    MainWindow = GsimcliMainWindow()
    # on exit
    app.aboutToQuit.connect(MainWindow.on_exit)
    MainWindow.show()
    sys.exit(app.exec_())
