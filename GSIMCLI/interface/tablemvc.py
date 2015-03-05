# -*- coding: utf-8 -*-
'''
Created on 25/02/2015

@author: julio
'''
from PySide import QtGui, QtCore
import pandas as pd
import sys


class TableModel(QtCore.QAbstractTableModel):
#     dataChanged = QtCore.Signal(QtCore.QModelIndex, QtCore.QModelIndex)

    def __init__(self, parent=None):
        super(TableModel, self).__init__(parent)
        self.table = pd.DataFrame(index=range(3), columns=["A", "B"])
        self.table.fillna('', inplace=True)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            i = index.row()
            j = index.column()
            return self.table.iloc[i, j]

    def flags(self, index):
        return (QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsEnabled)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 3

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            i = index.row()
            j = index.column()
            self.table.iloc[i, j] = value
            self.dataChanged.emit(index, index)
            return True
        return False


class TableView(QtGui.QTableView):
    def __init__(self, parent=None):
        super(TableView, self).__init__(parent)
        self.doubleClicked.connect(self.browse_dir)
        # set edit triggers that avoid overlap of slots when double clicking
#         self.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed |
#                              QtGui.QAbstractItemView.EditKeyPressed)

    def browse_dir(self):
        index = self.currentIndex()
        filepath = QtGui.QFileDialog.getExistingDirectory(self, "Select dir")

        if filepath:
            self.model().setData(index, filepath)
            # self.setText(filepath)
            # self.dataChanged(index, index)
            # self.edit(index)
            


class MWEWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MWEWindow, self).__init__(parent)
        self.table_model = TableModel(self)
        self.table_view = TableView(self)
        self.table_view.setModel(self.table_model)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.table_view)
        self.setLayout(vbox)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    w = MWEWindow()
    w.show()
    app.exec_()
    sys.exit()
