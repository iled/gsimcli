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

There are three groups of settings for you to set up: data, simulation and
homogenisation.

Data
~~~~

In this group you must prepare the data to be homogenised.

Load
''''

Data file location
    Browse a single file containing. This option is automatically disabled if
    `Batch`_ is enabled.

Header
    Enable if every data file have the standard GSLIB_ header lines.

 .. _GSLIB: http://www.gslib.com/gslib_help/format.html

File preview
    Show the first 10 lines of the loaded file. It is useful to double check
    the header existence and the variables order.

    When processing multiple networks, it will try to locate one of the data
    files of the selected network and display its first 10 lines.

Name
    The data set name. If header is enabled, it will automatically extract the
    first line of the data file into this field.

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

Batch
'''''

Depending on the size of the data set and on the selected settings, the
homogenisation process may take a few hours or even several days. These batch
options allow you to prepare different networks and leave them to run on a
queue list.

Batch networks
    This option allow you to select multiple networks to homogenise. Each
    network should be in a single