# -*- coding: utf-8 -*-
"""
Created on 16/06/2014

@author: julio
"""

from PySide import QtCore, QtGui  # , QtUiTools
import os
import sys
from tempfile import NamedTemporaryFile

base = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base)

from interface.pyside_dynamic import loadUi
from launchers import method_classic
from parsers.gsimcli import GsimcliParam


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
        self.skip_dss = self.SO_checkSkipDSS.isChecked()
        self.print_status = self.actionPrintStatus.isChecked()

        # change pages
        self.treeWidget.expandAll()
        self.treeWidget.currentItemChanged.connect(self.set_stacked_item)

        # check boxes
        self.DB_checkBatchDecades.toggled.connect(self.enable_batch_decades)
        self.DB_checkBatchNetworks.toggled.connect(self.enable_batch_networks)
        self.SO_checkSkipDSS.toggled.connect(self.enable_skip_dss)
        self.actionPrintStatus.toggled.connect(self.disable_print_status)

        # combo boxes
        self.HD_comboStationOrder.currentIndexChanged.connect(
                                                  self.change_station_order)
        self.HD_comboDetectionMethod.currentIndexChanged.connect(
                                                         self.enable_skewness)

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

        # line edits
        self.DL_plainDataPreview.setPlainText("Data file preview")
        self.DL_lineDataPath.editingFinished.connect(self.preview_data_file)
        self.DB_lineDecadesPath.textChanged.connect(self.guess_network_id)

        # hidden
        self.SV_labelBatchDecades.setVisible(False)

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
        self.enable_decades_group(self.DB_checkBatchDecades.isChecked() and not
                                  self.DB_checkBatchNetworks.isChecked())
        if not self.DB_checkBatchDecades.isChecked():
            self.disable_datapath_group(toggle)

    def enable_batch_decades(self, toggle):
        # self.SimulationVariogram.setDisabled(toggle)
        # self.SV_labelBatchDecades.setVisible(toggle)
        tree_item = self.treeWidget.findItems("Variogram",
                         QtCore.Qt.MatchRecursive, QtCore.Qt.MatchExactly)[0]
        tree_item.setDisabled(toggle)
        if toggle:
            tool_tip = ("Batch mode for decades is enabled, variograms "
                                 "are specified in variography files.")
        else:
            tool_tip = None
        tree_item.setToolTip(0, tool_tip)
        self.enable_decades_group(toggle and not
                                  self.DB_checkBatchNetworks.isChecked())
        if not self.DB_checkBatchNetworks.isChecked():
            self.disable_datapath_group(toggle)

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
        
    def disable_print_status(self, toggle):
        self.print_status = toggle

    def change_station_order(self, index):
        st_order = self.HD_comboStationOrder.currentText()
        if st_order == "User":
            enable_user = True
            disable_checks = True
        elif st_order == "Random":
            enable_user = False
            disable_checks = True
        else:
            enable_user = False
            disable_checks = False
        self.HD_labelUserOrder.setEnabled(enable_user)
        self.HD_lineUserOrder.setEnabled(enable_user)
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

    def remove_networks(self):
        for path in self.DB_listNetworksPaths.selectedItems():
            self.DB_listNetworksPaths.takeItem(
                                           self.DB_listNetworksPaths.row(path))

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

    def preview_data_file(self):
        try:
            with open(self.DL_lineDataPath.text(), 'r+') as datafile:
                lines = str()
                for i in xrange(10):  # @UnusedVariable
                    lines += datafile.readline()
        except IOError:
            lines = "Error loading file"
        self.DL_plainDataPreview.setPlainText(lines)
        
    def guess_network_id(self):
        self.DB_lineNetworkID.setText(os.path.basename(os.path.dirname(
                                           self.DB_lineDecadesPath.text())))

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
            self.HD_lineUserOrder.setText(self.params.st_user)
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

        # TODO: set status or something to show it was loaded
        if self.print_status:
            print "loaded from: ", self.params.path

    def save_settings(self, par_path=None):
        # Data / Load
        if self.DB_checkBatchDecades.isChecked():
            self.params.data = self.DB_lineDecadesPath.text()
        else:
            self.params.data = self.DL_lineDataPath.text()
        self.params.no_data = self.DL_spinNoData.value()
        self.params.data_header = self.DL_checkHeader.isChecked()
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
        if not self.DB_checkBatchNetworks.isChecked():
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
        if not self.DB_checkBatchDecades.isChecked():
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
            self.params.st_user = self.HD_lineUserOrder.text()
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

        # TODO: set status or something to show it was saved
        if self.print_status:
            print "saved at: ", self.params.path

    def run_gsimcli(self):
        self.apply_settings()
        batch_networks = self.DB_checkBatchNetworks.isChecked()
        batch_decades = self.DB_checkBatchDecades.isChecked()
        self.params.path = str(self.params.path)
        self.params.results = str(self.params.results)

        if batch_networks:
            networks_list = qlist_to_pylist(self.DB_listNetworksPaths)
            # workaround for unicode/bytes issues
            networks_list = map(str, networks_list)
            method_classic.batch_networks(par_path=self.params.path,
                                          networks=networks_list,
                                          decades=batch_decades,
                                          skip_dss=self.skip_dss,
                                          print_status=self.print_status)
        elif batch_decades:
            method_classic.batch_decade(par_path=self.params.path,
                            variograms_file=str(self.DB_lineVariogPath.text()),
                            print_status=self.print_status,
                            skip_dss=self.skip_dss,
                            network_id=self.DB_lineNetworkID.text())
        else:
            method_classic.run_par(par_path=self.params.path,
                                   skip_dss=self.skip_dss,
                                   print_status=self.print_status)

    def apply_settings(self):
        self.save_settings(self.temp_params.name)

    def save_params(self):
        self.save_settings(self.loaded_params)

    def save_as_params(self):
        filepath = QtGui.QFileDialog.getSaveFileName(self,
                                     caption="Save parameters file",
                                     dir=os.path.expanduser('~/'))
        if filepath[0]:
            self.save_settings(filepath[0])
            self.actionSave.setEnabled(True)

    def open_params(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Open parameters file",
                                     dir=os.path.expanduser('~/'))
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
