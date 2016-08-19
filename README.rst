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

The test command output is shown in the console standard output
whereby Dose was called. The same applies to the standard error, but
it's red-colored. Dose uses ANSI escaping codes for coloring text in
a terminal.


Syntax / Example
----------------

Just call ``dose TEST_COMMAND``, where ``TEST_COMMAND`` is what you
would call to run some test suite. Dose is written in Python 2 but the
test command can be anything.

*Hint (color)*: The ANSI coloring from the test command is to the
underlying console. For example, a tox + py.test Python project whose
``tox.ini`` has ``commands = py.test {posargs}``, you can force the
py.test coloring with ``dose tox -- --color=yes``.

*Hint (shell)*: You can use shell pipes in your test command by
quoting the whole command, e.g. ``dose "cat tests.txt | verify.sh"``.


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

.. _watchdog:
  https://pypi.python.org/pypi/watchdog


Requirements
------------

- wxPython 2.8 or 3.0 (classic)
- watchdog

You should install the ``wxpython`` or ``wxgtk`` packages from your
Linux distribution, or get the Windows / Mac OS X binary packages
directly from the `wxPython official site`_\ . On Mac OS X 10.11
(El Capitan), `this blog post might help`_\ .

.. _`wxPython official site`:
  https://www.wxpython.org

.. _`this blog post might help`:
  http://davixx.fr/blog/2016/01/25/wxpython-on-os-x-el-capitan/


Installation
------------

``pip install dose``


GUI Controls
------------

- *Dragging*\ : Move
- *Dragging holding Ctrl/⌘*\ : Resize
- *Dragging holding Shift*\ : Controls th transparency
- *Double click*\ : start or stop the watcher (can kill the test job)

A right click (or Ctrl + click on OSX) show more options.

Please see the CHANGES.rst file for more information.


----

.. copyright

Copyright (C) 2012-2016 Danilo de Jesus da Silva Bellini

.. copyright end
