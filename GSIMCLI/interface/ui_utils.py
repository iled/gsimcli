# encoding: utf-8
"""
Created on 13/01/2015

@author: julio
"""
from PySide import QtGui
import warnings

from parsers.gsimcli import GsimcliParam


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
        # if isinstance(self.widget, GsimcliMainWindow):
        #    pass
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
        if (
            isinstance(self.widget, QtGui.QCheckBox) or
            isinstance(self.widget, QtGui.QRadioButton) or
            (isinstance(self.widget, QtGui.QGroupBox) and
             self.widget.isCheckable())
             ):
            self.value = self.widget.isChecked()

    def load(self, value):
        def to_bool(u):
            return u in ["true", "True", True]

        # if isinstance(self.widget, GsimcliMainWindow):
        #    pass
        if isinstance(self.widget, QtGui.QLineEdit):
            self.widget.setText(str(value))
        elif isinstance(self.widget, QtGui.QSpinBox):
            self.widget.setValue(int(value))
        elif isinstance(self.widget, QtGui.QDoubleSpinBox):
            self.widget.setValue(float(value))
        elif isinstance(self.widget, QtGui.QListWidget):
            pylist_to_qlist(value, self.widget)
        elif isinstance(self.widget, QtGui.QComboBox):
            self.widget.setCurrentIndex(int(value))
        elif (
            isinstance(self.widget, QtGui.QCheckBox) or
            isinstance(self.widget, QtGui.QRadioButton) or
            (isinstance(self.widget, QtGui.QGroupBox) and
             self.widget.isCheckable())
              ):
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


def hide(widgets):
    """Hide a list of widgets.

    """
    for widget in widgets:
        widget.setVisible(False)


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
