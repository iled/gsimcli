# -*- coding: utf-8 -*-
"""
Created on 20/05/2015

@author: julio
"""
from PySide import QtGui, QtCore

from external_libs.ui import CheckBoxDelegate
import pandas as pd


class TableModel(QtCore.QAbstractTableModel):

    """Table model with a column filled with one check box per line. Each check
    box is centered in the cell and has no text.

    The data structured is a pandas.DataFrame.

    """
    dataChanged = QtCore.Signal(QtCore.QModelIndex, QtCore.QModelIndex)

    def __init__(self, checkbox_col, parent=None, auto_row=True):
        """Constructor.

        Parameters
        ----------
        checkbox_col : int
            Number of the column with the check boxes.
        parent : QObject, optional
            Parent of the model.
        auto_row : bool, optional
            Automatically add a row after the last one is edited. Default is
        True.

        """
        super(TableModel, self).__init__(parent)
        self.table = None
        self.header = None
        self.vheader = None
        self.checkbox_col = checkbox_col
        # signals
        if auto_row:
            self.dataChanged.connect(self.add_rows_auto)

    def addItem(self, item):
        """Append a row to the table.

        Parameters
        ----------
        item : array_like
            Row to be inserted after the last row in the table.

        """
        count = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), count, count)
        self.table.loc[count] = item
        self.endInsertRows()

    def add_rows_auto(self, index):
        """Automatically add a new row after entering data in the last row.
        Connected to the dataChanged signal.
        This new row is empty and the check box is not checked.

        Parameters
        ----------
        index : QModelIndex
            Index passed by the dataChanged signal.

        """
        row = index.row()
        row_content = self.table.values[row, :-1]
        if row == (self.rowCount() - 1) and all(row_content):
            self.addItem(['', '', '', False])

    def clear(self):
        """Empty the table.

        """
        self.beginResetModel()
        self.update(pd.DataFrame(columns=self.table.columns))
        self.endResetModel()

    def columnCount(self, parent=QtCore.QModelIndex()):
        """Return the number of columns in the table.

        """
        if self.table is not None:
            return self.table.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Return the value in the given index of the table.

        """
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            i = index.row()
            j = index.column()
            if j == self.checkbox_col:
                return self.table.iloc[i, j]
            else:
                return unicode(self.table.iloc[i, j])

    def flags(self, index):
        """Return the item flags for the given index.

        """
        if index.column() == self.checkbox_col:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled  # @IgnorePep8

    def headerData(self, idx, orientation, role):
        """Return the data for the given `role` and `section` in the header
        with the specified `orientation`.

        """
        if (orientation == QtCore.Qt.Horizontal and
                role == QtCore.Qt.DisplayRole):
            return self.table.columns.tolist()[idx]
        if (orientation == QtCore.Qt.Vertical and
                role == QtCore.Qt.DisplayRole):
            return self.table.index.tolist()[idx]

    def isChecked(self, index):
        """Return the check box state in the given `index`.

        """
        return self.table.iloc[index.row(), self.checkbox_col]

    def get_key(self, key, filter_selected=False):
        """Return the column named `key` in the table.

        Parameters
        ----------
        key : string
            Column name.
        filter_selected : boolean, default False
            Return only the rows with a checked check box.

        """
        if filter_selected:
            values = self.table.query(self.checkbox_key + ' == True')[key]
        else:
            values = self.table[key]

        return values

    def get_row(self, row):
        """Return the data in the given `row` number.

        Parameters
        ----------
        row : int
            Row number

        """
        return self.table.loc[row]

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        """Remove the row in the given position.

        """
        if not(0 <= row <= self.rowCount()):
            return False

        self.beginRemoveRows(parent, row, row)
        self.table.drop(row, axis=0, inplace=True)
        self.table.reset_index(drop=True, inplace=True)
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        """Return the number of rows in the table.

        """
        if self.table is not None:
            return self.table.shape[0]

    def setChecked(self, index, value, role=QtCore.Qt.EditRole):
        """Set the check box in the given `index` with the given `value`.

        """
        if role == QtCore.Qt.EditRole:
            self.table.iloc[index.row(), self.checkbox_col] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """Set the `role` data for the item at `index` to `value`.

        """
        if role == QtCore.Qt.EditRole:
            i = index.row()
            j = index.column()
            self.table.iloc[i, j] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setHeaderData(self, section, value, orientation=QtCore.Qt.Horizontal,
                      role=QtCore.Qt.EditRole):
        """
        Set the data for the given `role` and `section` in the header with the
        specified `orientation` to the `value` supplied.

        """
        if role == QtCore.Qt.EditRole and orientation == QtCore.Qt.Horizontal:
            self.header[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        elif role == QtCore.Qt.EditRole and orientation == QtCore.Qt.Vertical:
            self.vheader = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        else:
            return False

    def update(self, data_in):
        """Change the whole existing table with `data_in`. Headers will be
        changed accordingly to the names existing in `data_in` table.

        Existing data will be lost.

        Parameters
        ----------
        data_in : pandas.DataFrame
            Table with the new data and headers.

        """
        self.table = data_in
        headers = data_in.columns
        self.header = [unicode(field) for field in headers]
        indexes = data_in.index
        self.vheader = [unicode(index + 1) for index in indexes]
        self.checkbox_key = self.table.columns[self.checkbox_col]


class TableView(QtGui.QTableView):

    """A table view to show and manage the data in the table model with check
    boxes in one column.

    The table has alternating row colours.

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
        super(TableView, self).__init__(parent)
        self.setAlternatingRowColors(True)
        # set delegate
        self.setItemDelegateForColumn(checkbox_col, CheckBoxDelegate(self))

    def remove_rows(self):
        """Remove the selected rows from the table. If the last row is removed,
        a new one will be added.

        """
        indexes = self.selectedIndexes()
        rows = sorted({index.row() for index in indexes})
        for n, row in enumerate(rows):
            self.model().removeRow(row - n)

        # keep one row
        if self.model().rowCount() < 1:
            row = [''] * (self.model().columnCount() - 1) + [True]
            self.model().addItem(row)
