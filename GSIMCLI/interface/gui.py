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
        print os.path.join(base, "interface", "gsimcli.ui")
        loadUi(os.path.join(base, "interface", "gsimcli.ui"), self)
        # QtUiTools.QUiLoader  # try this

        # set params
        self.params = GsimcliParam()
        params = NamedTemporaryFile()
        self.params_path = params.name
        self.skip_dss = self.SO_checkSkipDSS.isChecked()

        # change pages
        self.treeWidget.expandAll()
        self.treeWidget.currentItemChanged.connect(self.set_stacked_item)

        # check boxes
        self.DB_batchDecades.toggled.connect(self.enable_batch_decades)
        self.DB_batchNetworks.toggled.connect(self.enable_batch_networks)
        self.SO_checkSkipDSS.toggled.connect(self.enable_skip_dss)

        # combo boxes
        self.HD_stOrder.currentIndexChanged.connect(self.change_station_order)
        self.HD_method.currentIndexChanged.connect(self.enable_skewness)

        # buttons
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).clicked.connect(
                                                            self.save_settings)
        self.DL_dataButton.clicked.connect(self.browse_data_file)
        self.DB_buttonAddNetworks.clicked.connect(self.browse_networks)
        self.DB_buttonRemoveNetworks.clicked.connect(self.remove_networks)
        self.DB_variogButton.clicked.connect(self.browse_variog_file)
        self.SO_dssexeButton.clicked.connect(self.browse_exe_file)
        self.HR_resultsButton.clicked.connect(self.browse_results)

        # hidden
        self.SV_labelBatchDecades.setVisible(False)

        # menu
        self.actionOpen.triggered.connect(self.open_params)
        self.actionSave.triggered.connect(self.save_params)
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
        self.DB_variogLabel.setEnabled(enable)
        self.DB_variogPath.setEnabled(enable)
        self.DB_variogButton.setEnabled(enable)

    def disable_datapath_group(self, disable):
        self.DL_labelDataPath.setDisabled(disable)
        self.DL_dataPath.setDisabled(disable)
        self.DL_dataButton.setDisabled(disable)

    def enable_batch_networks(self, toggle):
        self.DB_labelBatchNetworks.setEnabled(toggle)
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
        self.enable_decades_group(self.DB_batchDecades.isChecked() and not
                                  self.DB_batchNetworks.isChecked())
        if not self.DB_batchDecades.isChecked():
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
                                  self.DB_batchNetworks.isChecked())
        if not self.DB_batchNetworks.isChecked():
            self.disable_datapath_group(toggle)

    def enable_skip_dss(self, toggle):
        self.skip_dss = toggle

    def change_station_order(self, index):
        st_order = self.HD_stOrder.currentText()
        if st_order == "User":
            enable_user = True
            disable_checks = True
        elif st_order == "Random":
            enable_user = False
            disable_checks = True
        else:
            enable_user = False
            disable_checks = False
        self.HD_label_userOrder.setEnabled(enable_user)
        self.HD_userOrder.setEnabled(enable_user)
        self.HD_checkAscending.setDisabled(disable_checks)
        self.HD_checkMDLast.setDisabled(disable_checks)

    def enable_skewness(self, index):
        if self.HD_method.currentText() == "Skewness":
            enable = True
        else:
            enable = False
        self.HD_labelSkewness.setEnabled(enable)
        self.HD_skewness.setEnabled(enable)

    def browse_data_file(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select data file",
                                     dir=os.path.expanduser('~/'))
        if filepath[0]:
            self.DL_dataPath.setText(filepath[0])

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
        for path in self.DB_networksPaths.selectedItems():
            self.DB_networksPaths.takeItem(self.DB_networksPaths.row(path))

    def browse_variog_file(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select variography file",
                                     dir=os.path.expanduser('~/'),
                                     filter="Text CSV (*.csv)")
        if filepath[0]:
            self.DB_variogPath.setText(filepath[0])

    def browse_exe_file(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Select executable file",
                                     dir=os.path.expanduser('~/'),
                                     filter="Executable (*.exe)")
        if filepath[0]:
            self.SO_dssexePath.setText(filepath[0])

    def browse_results(self):
        filepath = QtGui.QFileDialog.getExistingDirectory(self,
                                     caption="Select results directory",
                                     dir=os.path.expanduser('~/'))
        if filepath:
            self.HR_resultsPath.setText(filepath)

    def load_settings(self):
        # Data / Load
        self.DL_dataPath.setText(self.params.data)
        self.DL_noData.setValue(self.params.no_data)
        self.DL_checkHeader.setChecked(self.params.data_header)
        try:
            self.DL_dataName.setText(self.params.name)
            pylist_to_qlist(self.params.variables, self.DL_listVarNames)
        except(AttributeError):
            # ignore if attributes are not present
            pass

        # Simulation / Options
        # self.SO_dssparPath.setText(self.params.dss_par)
        self.SO_dssexePath.setText(self.params.dss_exe)
        self.SO_numberSims.setValue(self.params.number_simulations)
        self.SO_krigType.setCurrentIndex(self.SO_krigType.findText(
                       self.params.krig_type[0], QtCore.Qt.MatchStartsWith))
        self.SO_maxSearchNodes.setValue(self.params.max_search_nodes)

        # Simulation / Grid
        try:
            self.SG_xxNodes.setValue(self.params.XX_nodes_number)
            self.SG_yyNodes.setValue(self.params.YY_nodes_number)
            self.SG_zzNodes.setValue(self.params.ZZ_nodes_number)
            self.SG_xxMin.setValue(self.params.XX_minimum)
            self.SG_yyMin.setValue(self.params.YY_minimum)
            self.SG_zzMin.setValue(self.params.ZZ_minimum)
            self.SG_xxSpacing.setValue(self.params.XX_spacing)
            self.SG_yySpacing.setValue(self.params.YY_spacing)
            self.SG_zzSpacing.setValue(self.params.ZZ_spacing)
        except(AttributeError):
            self.DB_batchNetworks.setChecked(True)

        # Simulation / Variogram
        try:
            self.SV_varModel.setCurrentIndex(self.SV_varModel.findText(
                               self.params.model, QtCore.Qt.MatchStartsWith))
            self.SV_nugget.setValue(self.params.nugget)
            self.SV_sill.setValue(self.params.sill)
            self.SV_ranges.setText(self.params.ranges)
            self.SV_angles.setText(self.params.angles)
        except(AttributeError):
            self.DB_batchDecades.setChecked(True)

        # Homogenisation / Detection
        st_order = self.params.st_order
        if st_order == "sorted":
            st_order = "id order"
        self.HD_stOrder.setCurrentIndex(self.HD_stOrder.findText(st_order,
                                                     QtCore.Qt.MatchContains))
        if st_order == "user":
            self.HD_userOrder.setText(self.params.st_user)
        else:
            self.HD_checkAscending.setChecked(self.params.ascending)
            self.HD_checkMDLast.setChecked(self.params.md_last)
        self.HD_method.setCurrentIndex(self.HD_method.findText(
                           self.params.detect_method, QtCore.Qt.MatchContains))
        if self.params.detect_method == "skewness":
            self.HD_skewness.setValue(self.params.skewness)
        self.HD_prob.setValue(self.params.detect_prob)

        # Homogenisation / Results
        self.HR_checkSaveInter.setChecked(self.params.detect_save)
        self.HR_checkPurgeSims.setChecked(self.params.sim_purge)
        self.HR_resultsPath.setText(self.params.results.decode('utf-8'))

        self.actionGSIMCLI.setEnabled(True)

        # TODO: set status or something to show it was loaded
        print "loaded from: ", self.params.path

    def save_settings(self):
        # Data / Load
        self.params.data = self.DL_dataPath.text()
        self.params.no_data = self.DL_noData.value()
        self.params.data_header = self.DL_checkHeader.isChecked()
        self.params.name = self.DL_dataName.text()
        self.params.variables = qlist_to_pylist(self.DL_listVarNames)

        # Simulation / Options
        if self.SO_dssparPath.text():
            self.params.dss_par = self.SO_dssparPath.text()
        self.params.dss_exe = self.SO_dssexePath.text()
        self.params.number_simulations = self.SO_numberSims.value()
        krigtype = self.SO_krigType.currentText()
        if krigtype == "Simple":
            krigtype = "SK"
        elif krigtype == "Ordinary":
            krigtype = "OK"
        self.params.krig_type = krigtype
        self.params.max_search_nodes = self.SO_maxSearchNodes.value()

        # Simulation / Grid
        if not self.DB_batchNetworks.isChecked():
            self.params.XX_nodes_number = self.SG_xxNodes.value()
            self.params.YY_nodes_number = self.SG_yyNodes.value()
            self.params.ZZ_nodes_number = self.SG_zzNodes.value()
            self.params.XX_minimum = self.SG_xxMin.value()
            self.params.YY_minimum = self.SG_yyMin.value()
            self.params.ZZ_minimum = self.SG_zzMin.value()
            self.params.XX_spacing = self.SG_xxSpacing.value()
            self.params.YY_spacing = self.SG_yySpacing.value()
            self.params.ZZ_spacing = self.SG_zzSpacing.value()

        # Simulation / Variogram
        if not self.DB_batchDecades.isChecked():
            self.params.model = self.SV_varModel.currentText()[0]
            self.params.nugget = self.SV_nugget.value()
            self.params.sill = self.SV_sill.value()
            self.params.ranges = self.SV_ranges.text()
            self.params.angles = self.SV_angles.text()

        # Homogenisation / Detection
        st_order = self.HD_stOrder.currentText().lower()
        if st_order == "id order":
            st_order = "sorted"
        self.params.st_order = st_order
        if st_order == "user":
            self.params.st_user = self.HD_userOrder.text()
        else:
            self.params.ascending = self.HD_checkAscending.isChecked()
            self.params.md_last = self.HD_checkMDLast.isChecked()
        self.params.detect_method = self.HD_method.currentText().lower()
        if self.params.detect_method == "skewness":
            self.params.skewness = self.HD_skewness.value()
        self.params.detect_prob = self.HD_prob.value()

        # Homogenisation / Results
        self.params.detect_save = self.HR_checkSaveInter.isChecked()
        self.params.sim_purge = self.HR_checkPurgeSims.isChecked()
        self.params.results = str(self.HR_resultsPath.text())

        self.params.save(self.params_path)
        self.actionGSIMCLI.setEnabled(True)

        # TODO: set status or something to show it was saved
        print "saved at: ", self.params.path

    def run_gsimcli(self):
        batch_networks = self.DB_batchNetworks.isChecked()
        batch_decades = self.DB_batchDecades.isChecked()
        self.params.path = str(self.params.path)
        self.params.results = str(self.params.results)

        if batch_networks:
#             networks = list()
#             for item_row in xrange(self.DB_networksPaths.count()):
#                 networks.append(self.DB_networksPaths.item(item_row).text())
            networks = qlist_to_pylist(self.DB_listNetworksPaths)
            # workaround for unicode/bytes issues
            networks = map(str, networks)
            method_classic.batch_networks(self.params.path, networks,
                                          batch_decades, self.skip_dss)
        elif batch_decades:
            method_classic.batch_decade(self.params.path,
                                    self.DB_variogPath.text(), self.skip_dss)
        else:
            method_classic.run_par(self.params.path, self.skip_dss)

    def save_params(self):
        filepath = QtGui.QFileDialog.getSaveFileName(self,
                                     caption="Save parameters file",
                                     dir=os.path.expanduser('~/'))
        if filepath[0]:
            self.params_path = filepath[0]
            self.save_settings()

    def open_params(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self,
                                     caption="Open parameters file",
                                     dir=os.path.expanduser('~/'))
        if filepath[0]:
            self.params.load(filepath[0])
            self.params_path = filepath[0]
            self.load_settings()

    def default_varnames(self):
        pylist_to_qlist(["x", "y", "time", "station", "clim"],
                        self.DL_listVarNames)


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
    import sys
    app = QtGui.QApplication(sys.argv)
    # MainWindow = loadUiWidget("/home/julio/qt/gsimcli.ui")
    MainWindow = MyMainWindow()
    MainWindow.show()
    sys.exit(app.exec_())
