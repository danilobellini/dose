Dose
====

.. summary

An automated traffic light/signal/semaphore GUI showing the state
during test driven development (TDD), mainly written for coding dojos.

.. summary end


What does it do?
----------------

Runs a test command when some file is created/modified/deleted,
showing the return value in a GUI.

There are 3 states:

- *Red*: Last test job failed/errored (it didn't return zero)
- *Yellow*: Running a test job
- *Green*: Last test job passed (it returned zero)

The test job output is written on the standard output, so it should
appear in the console/terminal whereby Dose was called. The same
applies to the standard error, whose text should appear in red.


Syntax / Example
----------------

Just call ``dose TEST_COMMAND``, where ``TEST_COMMAND`` is what you
would call to run your test suite in a terminal/console/shell. Dose is
written in Python but the test command can be any shell command.

*Hint (color)*: Any ANSI escaping code from the test command (e.g.
colors) is also sent to the standard streams in the underlying
console (Linux, Mac OS X and Cygwin) or converted by colorama_ to
Windows Console Handles API calls (Windows). In other words, colors
are enabled. For example, in a tox + py.test Python project whose
``tox.ini`` has ``commands = py.test {posargs}``, you can force the
py.test coloring with ``dose tox -- --color=yes``.

*Hint (shell)*: You can use shell pipes in your test command by
quoting the whole command, e.g. ``dose "cat tests.txt | verify.sh"``.


.. not-in-help
.. _colorama: https://pypi.python.org/pypi/colorama
.. not-in-help end

What does it watch?
-------------------

Using the watchdog_ package, Dose recursively watches a working
directory for file creation/modification/deletion events.

The watched directory is the current working directory, the one
whereby Dose was called. You can change it with the GUI, but remember
that the test command is always called in that directory too.

You can also configure an ignore pattern to avoid undesired
detections on temporary/compiled files.

Valid events during a test would kill (SIGTERM) a test job to
restart it. There's a 10ms delay before starting a test job and a 50ms
delay before killing it. Multiple events are joined to avoid
spawning/killing more than required.

There's a cycle/repeat detection in the watcher: repeating an event
won't kill the test job. Modifying the same file twice will have the
second modification ignored, unless it happens after finishing a test
job.

*Hint (change directory)*: You can watch a directory and call a
command in another directory by using ``cd PATH && TEST_COMMAND`` as
your test command, e.g. ``dose "cd toxinidir && tox"``.


.. not-in-help

.. _watchdog:
  https://pypi.python.org/pypi/watchdog


Requirements
------------

- Python (2 or 3) with pip/wheel/setuptools
- wxPython 2.8 or 3.0 (either Classic or Phoenix)
- watchdog
- colorama
- docutils

The only dependency package you have to worry about is wxPython, the
other ones should be installed together with Dose when they're not
available. The wxPyWiki have a detailed page on
`how to install wxPython`_\ , including how to install wxPython
Phoenix via pip, but for the wxPython Classic
you should install the ``wxpython`` or ``wxgtk`` packages from your
Linux distribution, or get the Windows / Mac OS X binary packages
directly from the `wxPython official site`_\ . On Mac OS X 10.11
(El Capitan), `this blog post might help`_\ .

.. _`how to install wxPython`:
  https://wiki.wxpython.org/How%20to%20install%20wxPython

.. _`wxPython official site`:
  https://www.wxpython.org

.. _`this blog post might help`:
  http://davixx.fr/blog/2016/01/25/wxpython-on-os-x-el-capitan/


Installation
------------

From PyPI_\ , with pip (recommended)::

  pip install dose

From the source distribution (e.g. after cloning this repository), you
can either use pip::

  pip install .

Wheel::

  python setup.py bdist_wheel
  wheel install dist/*.whl

Or setuptools directly (not recommended)::

  python setup.py install

.. _PyPI:
  http://pypi.python.org/pypi/dose


.. not-in-help end

GUI Controls
------------

.. linux-windows

**On Linux / Windows**

- *Dragging*\ : Move
- *Dragging holding Ctrl*\ : Resize
- *Dragging holding Shift*\ : Controls the transparency
- *Double click*\ : start or stop the watcher (can kill the test job)

A right click shows more options.

.. linux-windows end
.. osx

**On Mac OS X**

- *Dragging*\ : Move
- *Dragging holding ⌘*\ : Resize
- *Dragging holding ⇧*\ : Controls the transparency
- *Double click*\ : start or stop the watcher (can kill the test job)

A right click (or Ctrl + mouse click) shows more options.

.. osx end
.. not-in-help

Please see the CHANGES.rst file for more information.


----

.. copyright

Copyright (C) 2012-2016 Danilo de Jesus da Silva Bellini
