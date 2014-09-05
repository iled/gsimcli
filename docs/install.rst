.. _install:

************
Installation
************

Currently there is no stand-alone installer. You have to run gsimcli as a
Python script, launching the file **interface/gui.py**.

Python version support
~~~~~~~~~~~~~~~~~~~~~~

Only Python 2.7 was tested. It should be easy to port to Python 3.2+ if all
dependencies are already available to that same version.

Dependencies
~~~~~~~~~~~~

  * `NumPy <http://www.numpy.org>`__: 1.8 or higher
  * `pandas <http://pandas.pydata.org>`__: 0.13.0 or higher
  * `DSS <https://sites.google.com/site/cmrpsoftware/geoms>`__: only the binary
  * `Wine <https://www.winehq.org>`__: only for \*nix systems

.. note::

   pandas has a list of dependencies, some mandatory, other recommended and
   some other just optional. Although, you are highly encouraged to install all
   of them as they may be necessary in GSIMCLI.
   
   Although, if you installed Python through a packaged distribution,
   chances are that you already have those libraries.