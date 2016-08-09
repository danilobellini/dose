Dose
====

.. summary

An automated traffic light/signal/semaphore GUI showing the state
during test driven development (TDD), mainly written for coding dojos.

.. summary end


What does it do?
----------------

Runs a test command when some file is modified, showing its result in
a GUI.


Example
-------

Try ``dose tox`` instead of ``tox`` and have fun. Or anything else
instead of ``tox``.


What happens when something changes?
------------------------------------

A custom test command spawn a subprocess, and its output/error data
appear in the shell used to call Dose. If the process returned value
is zero, dose turns green, else it it turns red. It stays yellow while
waiting for the subprocess to finish.


What does it watch?
-------------------

Dose watches recursively the a working directory (by default, the
current directory) for file modifications, using the watchdog package
for that. You can configure a ignore pattern to avoid undesired
detections.


Requirements
------------

- wxPython 2.8 or 3.0 (classic)
- watchdog

You should install the ``wxpython`` or ``wxgtk`` packages from your
Linux distribution, or get the Windows binary packages directly from
https://www.wxpython.org


Installation
------------

``pip install dose``


GUI Controls
------------

- *Dragging*\ : Move
- *Dragging holding Ctrl*\ : Resize
- *Dragging holding Shift*\ : Controls th transparency
- *Double click*\ : start or stop the watcher (can kill the test job)

A right click would show more options.

Please see the CHANGES.rst file for more information.


----

Copyright (C) 2012-2016 Danilo de Jesus da Silva Bellini
