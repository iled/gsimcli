# -*- coding: utf-8 -*-
'''
Created on 27/01/2015

@author: julio
'''
from PySide import QtGui, QtCore


class CheckBoxDelegate(QtGui.QStyledItemDelegate):
    """A delegate that places a fully functioning QCheckBox in every cell of
    the column to which it's applied.

    Adapted from:
    https://gist.github.com/MarshallChris/6029919

    """
    def __init__(self, parent=None):
        super(CheckBoxDelegate, self).__init__(parent)

    def createEditor(self, *args, **kwargs):
        """Important, otherwise an editor is created if the user clicks in this
        cell.
        ** Need to hook up a signal to the model

        """
        return None

    def paint(self, painter, option, index):
        """Paint a checkbox without the label.

        """
        checked = bool(index.model().data(index, QtCore.Qt.DisplayRole))
        check_box_style_option = QtGui.QStyleOptionButton()

        if (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
            check_box_style_option.state |= QtGui.QStyle.State_Enabled
        else:
            check_box_style_option.state |= QtGui.QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QtGui.QStyle.State_On
        else:
            check_box_style_option.state |= QtGui.QStyle.State_Off

        check_box_style_option.rect = self.getCheckBoxRect(option)

        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox,
                                               check_box_style_option, painter)
        self.checked = checked

    def editorEvent(self, event, model, option, index):
        """Change the data in the model and the state of the checkbox if the
        user presses the left mousebutton or presses Key_Space or Key_Select
        and this cell is editable. Otherwise do nothing.

        """
        if not (index.flags() and QtCore.Qt.ItemIsEditable) > 0:
            return False

        # Do not change the checkbox-state
        if (event.type() == QtCore.QEvent.MouseButtonRelease or
                event.type() == QtCore.QEvent.MouseButtonDblClick):
            if (event.button() != QtCore.Qt.LeftButton or
                    not self.getCheckBoxRect(option).contains(event.pos())):
                return False
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                return True
        elif event.type() == QtCore.QEvent.KeyPress:
            if (event.key() != QtCore.Qt.Key_Space and
                    event.key() != QtCore.Qt.Key_Select):
                return False
        else:
            return False

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData(self, editor, model, index):
        """The user wanted to change the old state in the opposite.

        """
        newValue = not bool(index.model().data(index, QtCore.Qt.DisplayRole))
        model.setData(index, newValue, QtCore.Qt.EditRole)
        self.checked = newValue

    def getCheckBoxRect(self, option):
        check_box_style_option = QtGui.QStyleOptionButton()
        check_box_rect = QtGui.QApplication.style().subElementRect(
                                       QtGui.QStyle.SE_CheckBoxIndicator,
                                       check_box_style_option, None)
        check_box_point = QtCore.QPoint(option.rect.x() +
                                        option.rect.width() / 2 -
                                        check_box_rect.width() / 2,
                                        option.rect.y() +
                                        option.rect.height() / 2 -
                                        check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())

    def isChecked(self):
        return self.checked

    def setChecked(self, toggle):
        self.checked = toggle
