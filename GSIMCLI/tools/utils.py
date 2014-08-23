# -*- coding: utf-8 -*-
"""
Collection of some useful general purpose functions.

Created on 6 de Nov de 2013

@author: julio
"""
import datetime
import os


def dms2dec(d, m, s):
    """Convert coordinates in the format (Degrees, Minutes, Seconds) to
    decimal.

    Parameters
    ----------
    d : number
        Degrees.
    m : number
        Minutes.
    s : number
        Seconds.

    Returns
    -------
    float
        Coordinates in decimal format.

    Notes
    -----
    Assumes that data is signalled.
    The conversion is done by the formula

    .. math:: \operatorname{DEC} = \operatorname{DEG} + \operatorname{MIN}/60
        + \operatorname{SEC}/3600.

    """
    return int(d) + float(m) / 60 + float(s) / 3600


def is_number(s):
    """Check if s is a number.

    Parameters
    ----------
    s : string or number
        Input to check if is a number.

    Returns
    -------
    boolean
        True if `s` is a number.

    """
    try:
        float(s)
        return True
    except ValueError:
        return False
    # except TypeError:
    #    return False


def skip_lines(file_id, nlines):
    """Skip the next  n lines from a file.

    Parameters
    ----------
    file_id : file handle
        Input file.
    nlines : int
        Number of lines to skip.

    """
    for i in xrange(nlines):  # @UnusedVariable
        file_id.readline()


def filename_seq(file_id, n):
    """Generator to create a sequence of numbered filenames.

    Parameters
    ----------
    file_id : string
        Initial file name.
    n : int
        Number of names to generate.

    Returns
    -------
    fname : string
        File name.

    """
    base, ext = os.path.splitext(file_id)
    for i in xrange(n):
        fname = base + '_' + str(i) + ext
        i += 1
        yield fname


def filename_indexing(file_id, n):
    """Insert an index in a filename.

    Parameters
    ----------
    file_id : string
        File name.
    n : number
        Index to insert.

    Returns
    -------
    fname : string
        File name.

    """
    base, ext = os.path.splitext(file_id)
    fname = base + '_' + str(n) + ext
    return fname


def path_up(path, nlevels):
    """Go up n levels in the path tree.

    Parameters
    ----------
    path : string
        Folder or file path.
    nlevels : int
        Number of levels to go up.

    Returns
    -------
    head : string
        Target directory.
    tail : string
        The remaining part of the path tree.

    """
    if os.path.isdir(path):
        head = path
        filename = None
    else:
        head, filename = os.path.split(path)

    tail = list()
    if filename:
        tail.append(filename)

    for i in xrange(nlevels):  # @UnusedVariable
        head, base = os.path.split(head)
        tail.append(base)

    tail = os.path.join(*tail[::-1])

    return head, tail


def yes_no(yn):
    """Parse a string containing 'Y'(es) or 'N'(o).

    Parameters
    ----------
    yn : string
        Input string.

    Returns
    -------
    boolean
        Returns True if `yn` is equal to 'y' or to 'yes', otherwise returns
        False.

    """
    if yn.strip().lower() in ['y', 'yes']:
        return True
    else:
        return False


def seconds_convert(seconds):
    """Convert seconds to months, days and HH:MM:ss.

    Parameters
    ----------
    seconds : int
        Number of seconds.

    Returns
    -------
    string
        A formatted string with the result of the conversion.

    """
    months, seconds = divmod(seconds, 2592000)
    days, seconds = divmod(seconds, 86400)
    # months
    if months > 1:
        m_str = "{} months ".format(months)
    elif months > 0:
        m_str = "{} month ".format(months)
    else:
        m_str = ""
    # days
    if days > 1:
        d_str = "{} days ".format(days)
    elif days > 0:
        d_str = "{} day ".format(days)
    else:
        d_str = ""
    # HH:MM:ss
    h_str = str(datetime.timedelta(seconds=seconds))

    return m_str + d_str + h_str
