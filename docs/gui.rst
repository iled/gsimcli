===========
User manual
===========

:Date: |today|
:Version: |version|

This document aims to get you used to the gsimcli's graphical user interface
(GUI).
It is divided into sections that more or less match the interface sections.

The interface was designed to be easy and intuitive to use, having a lot of
common structures seen in other programs.

Overview
--------

The main window is divided into four sections, as shown in picture below:

    * on top there is the **main menu**
    * all the homogenisation process **settings** are accessed on the left menu
    * below that, on the bottom left corner, there is the **status box**
    * the remaining area on the right is where the settings are shown.

.. image: _static/gui_overview.png

Main menu
---------

The main menu include a few other subsections. When available, the actions
listed in the main menu may be followed by a keyboard shortcut.

File
~~~~

From here you can read and write files.

Restore last session
    Reload all the settings used in the last session (if any).

Open settings file
    Load all the settings saved into a configuration file. The file extension
    depends on your operating system and should be automatically detected.

Recent settings files
    List the last 10 configuration files which were opened or saved and will
    load all the settings saved into the selected file.

Save settings
    Save the current settings into the configuration file previously loaded.

Export settings
    Save the current settings into a new configuration file.

Quit
    Exit from the application.

View
~~~~

Print status (console)
    Enable or disable the program output into the console (terminal emulator).
    If any error occur while running the application, it will be printed in
    the console regardless of this option.

Tools
~~~~~

Not implemented yet.

Run
~~~

GSIMCLI
    Start the homogenisation process with the current settings. The process
    progress will be stated in the status box.

Help
~~~~

About
    Some information about the application.

Settings
--------

This GUI basically serves the purpose to prepare and launch the GSIMCLI
homogenisation process. This process depends on several settings which are
user adjustable.

There are three groups of settings for you to set up: :ref:`data`,
:ref:`simulation` and :ref:`homogenisation`.

.. _data:

Data
~~~~

In this group you must prepare the data to be homogenised.

Load
''''

Data file location
    Browse a single file containing. This option is automatically disabled if
    :ref:`batch` is enabled.

.. _header:

Header
    Enable if every data file have the standard GSLIB_ header lines.

.. _GSLIB: http://www.gslib.com/gslib_help/format.html

File preview
    Show the first 10 lines of the loaded file. It is useful to double check
    the header existence and the variables order.

    When processing multiple networks, it will try to locate one of the data
    files of the selected network and display its first 10 lines.

Name
    The data set name. If :ref:`header` is enabled, it will automatically
    extract the first line of the data file into this field.

Variables
    Select the correct variables order, which should match the structure on the
    given data files. You can adjust their order through drag and drop. There
    are five default variables that your data file should include:

    * x: value for the X-coordinate
    * y: value for the Y-coordinate
    * time: value for the unit of time (e.g., year)
    * station: the station ID number
    * clim: value for the climate variable

    The example below shows the preview of a loaded data file and the matching
    (drag and drop) of the variable corresponding to the station ID.

.. image: _static/gui_variables.png

No data
    The numeric placeholder for missing data. The default value is ``-999.9``.

.. _batch:

Batch
'''''

Depending on the size of the data set and on the selected settings, the
homogenisation process may take a few hours or even several days. These batch
options allow you to prepare different networks and leave them to run as on a
queue list.

.. _batch_networks:

Batch networks
    This option allow you to select multiple networks to homogenise. Each
    network data set must follow a specific format and have a main folder with
    a (meaningful) identifiation name/number, which contains:
      
   * a file with the grid properties, this file name must be of the type
   ``**grid*.csv``
   * as of :version: ``0.0.1``, it is mandatory that :ref:`batch_decades` is
   enabled and thus its requirements must also be followed
   * a folder which name starts with ``*dec*`` (e.g., decades or dec_files)
   * a variogram file within it, and this file name must be of the type
   ``*variog*.csv``
   
   The file with the grid properties must follow these specifications:
   
   - comma separated values (CSV)
   - seven labelled columns (not case sensitive):
      - xmin: initial value in X-axis
      - ymin: initial value in Y-axis
      - xnodes: number of nodes in X-axis
      - ynodes: number of nodes in Y-axis
      - znodes: number of nodes in Z-axis
      - xsize: node size in X-axis
      - ysize: node size in Y-axis
      - other columns will be ignored
      
   After enabling this option, the buttons to add and remove networks become
   available.
   
   Press the button **Add networks** to select the main directories of the
   networks to be homogenised. You can select multiple folders (networks) at
   the same time by pressing CTRL (PC) or CMD (Mac) while selecting them.
   
   After adding networks to the queue list, you can remove one or multiple
   networks from the list: just select them and press the button
   **Remove selected**.
   
   It is also possible to change the order in which the networks will be
   processed by drag and dropping from the list.
   
   :Note: when :ref:`batch_networks` is enabled, the settings' menu to set up
   the simulation :ref:`grid` automatically becomes unavailable, hence the need
   to specify the grid through a spreadsheet file.  
      
.. _batch_decades:    

Batch decades
   It might be useful to process a time series in chunks of time, for instance,
   if your data set spans a full century, splitting the data in decades may
   help to analyse local (temporal) trends or irregularities, or it just can
   ease the computacional weigth.
   
   Ir order to enable this option, the following requirements must be followed:
   
   * your data set files must be placed inside the folder
   * the decadal data files must have, at least, the first year of each decade
   in their file names
   * you should provide a spreadsheet file with the theoretical variogram model
   
   The variograms file must follow these specifications:
      
   - comma separated values (CSV)
   - nine labelled columns (not case sensitive):
      - variance
      - decade: decade in the format aaXX-aaYY (*aa* is optional)
      - model: {'S', 'E', 'G'}, (S = spherical, E = exponential,
      G = gaussian)
      - nugget: nugget effect
      - range
      - partial sill
      - nugget_norm: variance-normalised nugget effect
      - psill_norm: variance-normalised partial sill
      - sill_norm: variance-normalised total sill
      - other columns will be ignored
      
   After enabling this option, the related areas become available, except if
   :ref:`batch_networks` is also enabled, in which case it is not necessary to
   specify anything else.
   
   If not processing multiple networks, the following fields must be filled:
   
   * Decades directory: the folder containing your decadal files
   * Network ID: the network ID name/number. The program will try to guess the
   ID from the decades directory, but you can change it after that.
   * Variography file: the spreadsheet file containg the variogram model.
   
   :Note: when :ref:`batch_decades` is enabled, the settings' menu to set up
   the :ref:`variogram` automatically becomes unavailable, hence the need to
   specify the variogram through a spreadsheet file.
   
Simulation
~~~~~~~~~~

The gsimcli homogenisation process is based on a geostatistical stochastic
simulation method. It is necessary to specify several options related to that
part of the process, however, we provide you with a set of default values.
Also, the less relevant [to the homogenisation process] simulation parameters
are conveniently hidden and placed in a section for :ref:`advanced` users.

Options
'''''''

Parameters file
   The simulation parameters file, in its original format. As of
   :version: ``0.0.1``, that file will be automatically generated, and this
   this field is disabled.
   
Executable file
   The simulation (Direct Sequential Simulation -- DSS) binary file. As of
   :version: ``0.0.1``, only the 2001 version is supported. You can get the
   binary from the `CMRP Software cmrp` site. Download the file *GeoMS.zip*
   and extract the binary *dss.exe*.
   
.. _cmrp: https://sites.google.com/site/cmrpsoftware/geoms

Number of simulations
   The number of simulations per candidate station. A brief study demonstrated
   that a higher number leads to better results, as it will produce a smoother
   local distribution. A low number (below 100) will produce a distribution
   with *artifacts*, while a too high number will require too much CPU time. We
   advise you to run the process with a few hundreds (e.g., 500) realisations
   per candidate station.
   
Krigging type
   The krigging estimator used while simulating each node:
   
   * Ordinary (OK)
   * Simple (SK)
   
Maximum number of nodes to be found
   Related to the search method.
   
   We advise the value 16, in the range 1 -- 64. A higher number will produce a
   better spatial correlation in the simulated maps but it will demand an
   unnecessary higher computational effort. We found that a value above 16
   would not bring enough benefits to justify the increasing CPU time.
   
Number of CPU cores
   Recent computers often have multiple central processing units (CPU's) or one
   CPU with multiple cores, where each of them can be assigned to run a
   different process at the same time.
   
   In this program, such technology can be used to speed up the overall
   process. Specifically, you can opt to run multiple simulations at the same
   time if your computer have that capability, instead of running one at a
   time.
   
   The program will detect the number of cores installed and select that value
   by default.
   
   :Note: The supported DSS version is not parallelised. The multi-threading is
   attained through a script that will prepare and launch a number of copies
   of the DSS binary equal to the given number of CPU cores.
   
Skip simulation and use simulated maps already in place
   Enable this option if you have already run all the simulations and have kept
   the resulting maps in the results folder.
   
   This option is useful for debugging purposes or if you need to rebuild the
   results file.
   
Grid
''''

Here you specify the simulation grid:

* Grid dimension: the number of nodes/cells in each direction
* Cell size: the length (in units of distance) of one side of each cell
(which are squared)
* Origin coordinates: the position (in units of distance) of the first cell
   
This section will be automatically disabled when :ref:`batch_networks` is
enabled. 
   
Variogram
'''''''''

In this screen there are the necessary fields to set up the theoretical
variogram model:

* Model
* Nugget effect
* Sill
* Ranges (three comma separated values)
* Angles (three comma separated values)

This section will be automatically disabled when :ref:`batch_decades` is
enabled.

Advanced
''''''''

Options to change the remaining DSS parameters. Not implemented yet.

Homogenisation
~~~~~~~~~~~~~~

