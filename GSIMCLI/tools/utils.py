'''
Created on 6 de Nov de 2013

@author: julio
'''


def dms2dec(d, m, s):
    """Converts Degrees, Minutes, Seconds formatted coordinates to decimal.

    Formula:
    DEC = (DEG + (MIN * 1/60) + (SEC * 1/60))

    Assumes that data is signalled.
    """
    return int(d) + float(m) / 60 + float(s) / 3600


def is_number(s):
    """Check if s is a number"""
    try:
        float(s)
        return True
    except ValueError:
        return False
    # except TypeError:
    #    return False


def skip_lines(file_id, nlines):
    """Skip the next nlines from the file handled with file_id."""
    for i in xrange(nlines):  # @UnusedVariable
        file_id.readline()


if __name__ == '__main__':
    pass
