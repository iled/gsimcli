# encoding: utf-8
"""
Created on 13/01/2015

@author: julio
"""


def hide(widgets):
    """Hide a list of widgets.

    """
    for widget in widgets:
        widget.setVisible(False)
