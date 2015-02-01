# -*- coding: utf-8 -*-
"""
Created on 31/01/2015

@author: julio
"""
from PySide import QtCore, QtGui
import hashlib
import os
import sys
import tempfile
import time
import urllib2
from zipfile import ZipFile

base = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base)

from external_libs.pyside_dynamic import loadUi
from interface.ui_utils import Office, Updater, hide


class InstallDialog(QtGui.QWidget):
    """Dialog to the user download and/or install the benchmark data set.

    """
    sha256 = '28ec16be039b2c539a378e6d15f3b187b8d3d7557944d52d05f5a80c69ed412b'
    update = Updater()

    def __init__(self, parent=None):
        """Constructor

        """
        super(InstallDialog, self).__init__(parent)
        # load ui file
        loadUi(os.path.join(base, "interface", "install_dataset.ui"), self)
        self.downloading = False
        self.installing = False

        # buttons
        self.buttonDownload.clicked.connect(self.start_download)

        # hide
        hide([self.progressBar, self.labelStatus])

    @QtCore.Slot()
    def accept(self):
        print "yep"

    def check_file(self):
        if os.path.isfile(self.temp_file):
            hash = hashlib.sha256(open(self.temp_file, 'rb').open())
            if hash.hexdigest() != self.sha256:
                pass
            else:
                test = ZipFile(self.temp_file).testzip()

        if test is None:
            status = "No errors detected in the downloaded file."
            time.sleep(2)
        else:
            status = "Test failed in the file {}.".format(test)
        self.labelStatus.setText(status)

    def download_(self, file_url=None):
        self.downloading = True
        if file_url is None:
            file_url = ("ftp://ftp.meteo.uni-bonn.de/pub/victor/costhome/"
                        "homogenized_monthly_benchmark/benchmark.zip")
        open_url = urllib2.urlopen(file_url)
        meta = open_url.info()
        self.file_size = int(meta.getheaders('Content-Length')[0])
        self.temp_file = os.path.join(tempfile.gettempdir(), 'benchmark.zip')
 
        downloaded_bytes = 0
        self.update.reset()
        block_size = 1024 * 8
 
        with open(self.temp_file, 'w+b') as f:
            while True:
                buffering = open_url.read(block_size)
                if not buffering:
                    break
 
                f.write(buffering)
                downloaded_bytes += block_size
                self.update.current += block_size
                self.update.send()
                print downloaded_bytes

    def download(self):
        self.downloading = True
        self.update.reset()
        self.file_size = 3
        self.temp_file = '/tmp/benchmark.zip'
        for i in xrange(3):
            time.sleep(1)
            self.update.current = i+1
            self.update.send()
            print i
        print "out download"
        
    def download_and_install(self):
        self.check_file()

    def get_install_path(self):
        user_path = self.lineDatasetPath.text()
        if user_path and os.path.isdir(os.path.dirname(user_path)):
            self.path = user_path
        else:
            self.path = os.path.join(base, "benchmark")
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        return self.path

    def install(self):
        print "installing"
        self.installing = True
        self.progressBar.setValue(0)
        self.labelStatus.setText('Installing...')
        self.update.reset()
        self.get_install_path()
        with ZipFile(self.temp_file) as zipfile:
            members = zipfile.infolist()
            self.zip_items = len(members)
            for i, member in enumerate(members):
                zipfile.extract(member, self.path)
                self.update.current = i
                self.update.send()
 
        self.show_status(False)
        self.lineDatasetPath.setText(self.path)

    @QtCore.Slot()
    def reject(self):
        print "noooo"

    def set_progress(self, value):
        who = "download"#self.sender().job.__name__
        print who
        if who == "download":
            total = self.file_size
        elif who == "install":
            total = self.zip_items
        else:
            print "ops"
            return
        progress = 100 * value / total
        self.progressBar.setValue(progress)
        print value, "out set progress"
        #time.sleep(2)
        print "pi"

    def show_status(self, toggle):
        self.progressBar.setValue(0)
        self.progressBar.setVisible(toggle)
        self.labelStatus.setVisible(toggle)
        
    def start_download(self, **kwargs):
        if self.downloading:
            self.labelStatus.setText("File already downloaded. "
                                     "Checking file integrity.")
            self.labelStatus.setVisible(True)
            self.check_file()
            self.install()
        else:
            self.show_status(True)
            self.office = Office(self, self.download, self.update.progress,
                                 **kwargs)
            self.office.worker.update_progress.connect(self.set_progress)
            self.office.finished.connect(self.start_install)
            self.office.start()

    def start_install(self):
        print "start install"
        self.office = Office(self, self.install, self.update.progress)
        self.office.worker.update_progress.connect(self.set_progress)
        self.office.start()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    dialog = InstallDialog()
    dialog.show()
    sys.exit(app.exec_())
