# -*- coding: utf-8 -*-
"""
Created on 31/01/2015

@author: julio
"""
from PySide import QtGui
import hashlib
import os
import sys
import tempfile
import urllib2
from zipfile import ZipFile

from external_libs.pyside_dynamic import loadUi
from interface.ui_utils import Office, Updater, hide


base = os.path.dirname(os.path.dirname(__file__))


class InstallDialog(QtGui.QDialog):
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
        self.temp_file = os.path.join(tempfile.gettempdir(), 'benchmark.zip')
        self.benchmark_path = None
        self.downloading = False
        self.installing = False

        if hasattr(self.parent, "default_dir"):
            self.default_dir = self.parent.default_dir
        else:
            self.default_dir = os.path.expanduser('~/')

        # action
        button_ok = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        button_ok.clicked.connect(self.accept)
        button_cancel = self.buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        button_cancel.clicked.connect(self.close)

        # buttons
        self.buttonDatasetPath.clicked.connect(self.browse_path)
        self.buttonDownload.clicked.connect(self.start_download)

        # hide
        hide([self.progressBar, self.labelStatus])

    def accept(self):
        user_path = self.lineDatasetPath.text()
        if hasattr(self, "path"):
            self.benchmark_path = self.path
        elif user_path and os.path.isdir(user_path):
            self.benchmark_path = user_path
        self.done(QtGui.QDialog.Accepted)

    def browse_path(self):
        caption = "Select the directory with the benchmark data set"
        path = QtGui.QFileDialog.getExistingDirectory(self, caption,
                                                      dir=self.default_dir)
        if path:
            self.path = path
            self.default_dir = os.path.abspath(path)
            self.lineDatasetPath.setText(path)

    def check_zip_exists(self):
        if hasattr(self, "temp_file") and os.path.isfile(self.temp_file):
            return True
        else:
            return False

    def check_zip_hash(self, set_status=False):
        hashfile = hashlib.sha256(open(self.temp_file, 'rb').read())
        if hashfile.hexdigest() != self.sha256:
            status = ("Invalid or corrupted file. Please try to download it "
                      "again.")
            ok = False
        else:
            status = "File checksum verified."
            ok = True
        if set_status:
            self.set_status(status)
        return ok

    def check_zip_test(self, set_status=False):
        test = ZipFile(self.temp_file).testzip()
        if test is None:
            status = "File integrity verified."
            ok = True
        else:
            status = "Test failed in the file {}.".format(test)
            ok = False
        if set_status:
            self.set_status(status)
        return ok

    def completed_install(self):
        self.set_status("Completed")
        self.show_progress(False)
        self.lineDatasetPath.setText(self.path)
        self.downloading = False
        self.installing = False

    def download(self, file_url=None):
        if file_url is None:
            file_url = ("ftp://ftp.meteo.uni-bonn.de/pub/victor/costhome/"
                        "homogenized_monthly_benchmark/benchmark.zip")
        open_url = urllib2.urlopen(file_url)
        meta = open_url.info()
        self.file_size = int(meta.getheaders('Content-Length')[0])
        self.update.reset()
        block_size = 1024 * 8

        with open(self.temp_file, 'w+b') as f:
            while True:
                buffering = open_url.read(block_size)
                if not buffering:
                    break

                f.write(buffering)
                self.update.current += block_size
                self.update.send()

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
        self.update.reset()
        self.get_install_path()
        with ZipFile(self.temp_file) as zipfile:
            members = zipfile.infolist()
            self.zip_items = len(members)
            for i, member in enumerate(members):
                zipfile.extract(member, self.path)
                self.update.current = i
                self.update.send()

    def set_progress(self, value):
        if self.downloading and not self.installing:
            total = self.file_size
        elif self.installing and not self.downloading:
            total = self.zip_items
        else:
            raise Exception("unexpected error")
        progress = 100 * value / total
        self.progressBar.setValue(progress)

    def set_status(self, status=None):
        if status is not None:
            self.labelStatus.setText(status)
            self.labelStatus.setVisible(True)
        else:
            self.labelStatus.setVisible(False)

    def show_progress(self, show):
        self.progressBar.setValue(0)
        self.progressBar.setVisible(show)

    def start_download(self, **kwargs):
        self.downloading = True
        self.installing = False
        download = True
        if self.check_zip_exists():
            # FIXME: label not showing up
            self.set_status("Existing file detected. Checking file...")
            if self.check_zip_hash() and self.check_zip_test():
                download = False

        if download:
            self.set_status("Downloading...")
            self.show_progress(True)
            self.office = Office(self, self.download, self.update.progress,
                                 **kwargs)
            self.office.progress.connect(self.set_progress)
            self.office.finished.connect(self.start_install)
            self.office.start()
        else:
            self.start_install()

    def start_install(self):
        self.downloading = False
        self.installing = True
        self.set_status("Installing...")
        self.show_progress(True)
        self.office = Office(self, self.install, self.update.progress)
        self.office.progress.connect(self.set_progress)
        self.office.finished.connect(self.completed_install)
        self.office.start()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    dialog = InstallDialog()
    dialog.show()
    sys.exit(app.exec_())
