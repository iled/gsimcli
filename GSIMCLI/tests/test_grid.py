'''
Created on 02/03/2014

@author: julio
'''
import os
import unittest

import numpy as np
import tools.grid as gr


class TestHeader(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.pset_path_header = 'data/000005_19001999.prn'
        cls.pset_path_noheader = 'data/000005_19001999_nh.prn'

    @classmethod
    def teardown_class(cls):
        os.remove('data/test_rm_h.prn')
        os.remove('data/test_add_h.prn')

    def test_detect_headed(self):
        self.assertTrue(gr.has_header(self.pset_path_header),
                        'File has header.')

    def test_detect_not_headed(self):
        self.assertFalse(gr.has_header(self.pset_path_noheader),
                         'File does not have header.')

    def test_remove_header(self):
        out = 'data/test_rm_h.prn'
        gr.remove_header(self.pset_path_header, out)
        try:
            np.loadtxt(out)
        finally:
            self.assertTrue(True)

    def test_remove_header_fail(self):
        out = 'data/test_rm_h.prn'
        gr.remove_header(self.pset_path_noheader, out)
        try:
            np.loadtxt(out)
        finally:
            self.assertTrue(True)

    def test_add_header(self):
        out = 'data/test_add_h.prn'
        gr.add_header(self.pset_path_noheader, out=out)
        try:
            np.loadtxt(out, skiprows=7)
        finally:
            self.assertTrue(True)

    def test_add_header_fail(self):
        out = 'data/test_add_h.prn'
        gr.add_header(self.pset_path_noheader, out=out)
        self.assertRaises(ValueError, np.loadtxt, out)
        self.assertRaises(ValueError, np.loadtxt, out, skiprows=6)


if __name__ == "__main__":
    import nose
    nose.runmodule(argv=[__file__, '-vvs'], exit=False)
