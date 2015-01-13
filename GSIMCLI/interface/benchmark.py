# -*- coding: utf-8 -*-
"""
Created on 13/01/2015

@author: julio
"""
from PySide import QtGui
import os
import sys

import tools.scores as scores
from external_libs.pyside_dynamic import loadUi
from interface.ui_utils import hide

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

        # hidden widgets by default
        hide([self.labelSaveCost, self.lineSaveCost,
              self.buttonSaveCost,
              ])

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

    def calculate_scores(self):
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


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Scores()
    # on exit
    window.show()
    sys.exit(app.exec_())
