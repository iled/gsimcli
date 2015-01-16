# encoding: utf-8
"""
Created on 13/01/2015

@author: julio
"""
from PySide import QtGui, QtCore
import time
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
        if isinstance(self.widget, QtGui.QTableWidget):
            self.value = qtable_to_pylist(self.widget)
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
        elif isinstance(self.widget, QtGui.QTableWidget):
            pylist_to_qtable(value, self.widget)
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


class Office(QtCore.QObject):
    """Connect the boss (parent) with the worker doing the job.

    """
    finished = QtCore.Signal()

    def __init__(self, parent, job, updater=None, **kwargs):
        super(Office, self).__init__(parent)
        self.job = job
        self.jobargs = kwargs
        # new thread
        self.thread = QtCore.QThread()
        # new worker
        self.worker = Worker(self, self.job, **self.jobargs)
        # move worker to thread
        self.worker.moveToThread(self.thread)
        # connect the thread's started signal to the worker's processing slot
        self.thread.started.connect(self.worker.run)
        # fetch results
        self.worker.results.connect(self.delivery)
        # clean-up, quit thread, mark worker and thread for deletion
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.timer.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.worker.timer.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        if updater is not None:
            updater.connect(self.worker.update_progress.emit)

    def start(self):
        self.thread.start()
        # self.result = self.worker.result

    def delivery(self):
        self.results = self.worker.result
        self.finished.emit()


class Worker(QtCore.QObject):
    """Handle threads.

    """
    # signals emmited during the job
    update_progress = QtCore.Signal(int)
    time_elapsed = QtCore.Signal(int)
    results = QtCore.Signal(object)
    finished = QtCore.Signal()

    def __init__(self, parent, job, **kwargs):
        # super(Worker, self).__init__(parent)
        QtCore.QObject.__init__(self)
        self.job = job
        self.kwargs = kwargs
        self.timer = Timer(self)
        self.timer.time_elapsed.connect(self.time_elapsed.emit)
        self.is_running = False

    def run(self):
        self.timer.start(time.time())
        self.is_running = True
        self.result = self.job(**self.kwargs)
        self.done()

    def done(self):
        self.is_running = False
        # workaround for the timer QThread removal
        time.sleep(1)
        self.results.emit(self.result)
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


class Updater(QtCore.QObject):
    progress = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)
        self.current = 0

    def reset(self):
        self.current = 0

    def send(self):
        self.progress.emit(self.current)


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


def qtable_to_pylist(qtable):
    """Convert QTableWidget to Python list.

    Parameters
    ----------
    qtable : QtGui.QTableWidget object
        Target QTableWidget.

    Returns
    -------
    items : list
        List with the items contained in qtable.

    See Also
    --------
    pylist_to_qtable : Convert Python list into an existing QTableWidget.

    """
    table = list()
    for col in xrange(qtable.columnCount()):
        column = list()
        for row in xrange(qtable.rowCount()):
            item = qtable.item(row, col)
            if item is not None:
                column.append(item.text())
            else:
                column.append("")
        table.append(column)

    return table


def pylist_to_qtable(pylist, qtable):
    """Convert Python list into an existing QTableWidget.

    Parameters
    ----------
    pylist : list
        List to be converted.
    qtable : QtGui.QTableWidget object
        Existing QTableWidget.

    See Also
    --------
    qtable_to_pylist : Convert QTWidget to Python list.

    """
    for col, column in enumerate(pylist):
        for row, content in enumerate(column):
            item = QtGui.QTableWidgetItem(content)
            qtable.setItem(row, col, item)

    return qtable
