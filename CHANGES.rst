Dose change log
===============

v1.1.0
------

* To avoid several simultaneous triggers for a single action being
  done (e.g. lots of events for each file while creating the source
  distribution to test with ``tox``), now only the file modifications
  events trigger a new test job.

* Brand new *killing* feature: the running test process now is killed
  when another event is triggered, and there's no delay to start the
  test job subprocess anymore. Cycles are detected to avoid an endless
  killing-spawning loop. To kill the current running process
  purposefully, one just need to double click dose with the left mouse
  button.

* New test job runner with realtime standard output/error streams.
  Each output/error byte is now printed as soon as possible, instead
  of waiting the process to finish.

* New colored output by printing the ANSI escape codes. The different
  colors used are:

  - Testing process standard error (sys.strerr): red.
  - Test job timestamp: yellow.
  - "Killed!" message: magenta/purple.
  - Event header/description: cyan/turquoise.
  - Exceptions: red.

  The messages themselves were modified to be centralized, and the
  timestamp now is just prefixed by ``[Dose]``.

* New external configuration file for loading/saving the aesthetic GUI
  state (window position, size, opacity and flip flag). The config is
  stored as a JSON file named ``.dose.conf``. Thanks Samuel Grigolato.

* Auto-save the configuration file 200ms after storing the new state in
  the config dictionary. The JSON config file is assumed to be the one
  at the current directory when it exists, otherwise it's loaded/saved
  at the home directory.

* Dose became a package including a prepared ``__main__.py`` module for
  running it with ``python -m``. For example::

    $ python2 -m dose py.test

  or the new console script without extension::

    $ dose py.test

  The legacy ``dose.py`` was completely removed, as the
  ``/usr/bin/dose.py`` (Linux path) was shadowing the installed
  ``dose`` package on importing, i.e., ``import dose`` used to import
  the ``dose.py`` script/module instead of the package.

* The setup script ``setup.py`` was completely rewritten.

* Bug fix: the given quoted/escaped arguments from the command line
  like::

    $ dose python -m doctest "Project Example [2]/main.rst"
    $ dose python -m doctest Project\ Example\ \[2\]/main.rst

  used to be internally re-joined losing the quoting/escaping
  information, behaving like this::

    $ dose python -m doctest Project Example [2]/main.rst

  Now the arguments are properly escaped when joining them as a single
  shell command to call ``subprocess.Popen``, unless there's only a
  single argument, which might include pipes and redirection.


v1.0.1
------

* Add compatibility with wxPython 3.0 (classic), now it's compatible with
  both wxPython 2.8 and 3.0.

* The event information header for each job is now processed to show just
  the file/directory name and whether it was created, modified or deleted,
  e.g.::

    *** File created: mypackage/mymodule.py ***

* The unicode characters in file/directory names now appears themselves in the
  event headers instead of an escaped representation, e.g.::

    *** Directory deleted: CAS Proofs/λ Calculus ***

  with ``λ`` instead of the raw event representation with ``\xce\xbb``::

    ***<DirDeletedEvent: src_path='./CAS Proofs/\xce\xbb Calculus'>***


v1.0.0
------

* First beta release, now with with semantic versioning. Environments with
  an alpha version installed should remove it and reinstall dose to upgrade
  it properly.

* The CLI arguments (``sys.argv``) are now used as the default test command,
  passing the remaining parameters to the call command itself, so one can
  call dose with something like ``dose.py py.test -k TestSomething`` directly.
  When the test command is provided like so, dose already starts watching and
  running the tests.

* The test command now can be any shell command with pipes/redirections, e.g.
  one can call ``dose.py "cat my_input.txt | my_test_script.sh"``.

* The default opacity/transparency is now slightly more opaque.

* The wxPython package isn't included as a requirement anymore as it requires
  an external installation procedure (e.g. the package manager of a
  Linux distribution or an installer for Windows).

* New logging header for each test job, showing the raw watchdog
  information about the event that triggered the test command, like::

    ***<FileCreatedEvent: src_path='./mypackage/mymodule.py'>***

  and this message for the only event that have nothing to do with watchdog::

    *** First call ***

* Bug fix: now the "skip"/ignore pattern can be customized. That was already
  an option in the GUI, but it was updating the test command instead,
  rendering it unusable.

* Bug fix: the test command can now include quoted arguments if it's passed
  as a single CLI argument or filled using the "call string" dialog box.

* Updated the default "skip"/ignore pattern to ignore ``__pycache__``
  directories.

  Intended to address the same issue regarding multiple test jobs for a
  single action, the test command runs one second after the watchdog event,
  instead of a half. This seems like a residual from experiments that
  happened before the event logging header was implemented.

* License fix: consistently using GPLv3 instead of GPLv3+.


alpha-2012.10.04
----------------

* Now using setuptools_ instead of distutils_ in the setup script,
  allowing it to look for and install the requirements: watchdog_ and its
  dependencies, recursively. It can be installed via ``pip`` and
  ``easy_install``, as long as the wxPython 2.8 package was previously
  installed.

* New customizable file/directory name "skip"/ignore pattern that defaults to
  ``*.pyc; *.pyo; .git/*``. This was done mainly to deal with the "bounce"
  issue (multiple events for a single action), as the ignore pattern
  "debounces" a new event that would otherwise happen after a compilation.

  Another approach used to attenuate that issue was a sleep of half a second
  to trigger the test command. Watchdog drops consecutive events that are
  duplicated, and used to drop non-consecutive duplicate events from its
  internal queue as well (watchdog commit 2d14857_).

* Force UTF-8 encoding on the watched directory name, this might have been
  an issue when handling non-ascii paths (watchdog issues 104_ and 157_\ , now
  fixed there). Taking the opportunity, this alpha release switched the string
  literals to unicode.


alpha-2012.10.02
----------------

* First version!

  It's a language-agnostic borderless "traffic light/signal/semaphore" GUI
  for TDD (Test Driven Development), mainly intended for use in Coding Dojos,
  hence its name: it's a *Dojo Semaphore*\ , a name that has the same leading
  syllables in both English and Portuguese.

* Written in Python 2 using the wxPython 2.8 GUI library.

* Compatibility with both Linux and Windows.

* It recursively watches a working directory (defaults to the current
  directory) for every file/subdirectory creation, modification and deletion
  that happens inside it, triggering a test job.

* Avoids file/directory polling whenever possible, using the watchdog_ package
  for that.

* The test command can be any customizable shell command, like
  ``python -m doctest``, ``py.test -k test_my_new_feature``,
  ``tox -e py34,pypy``, ``./run_tests.sh``, etc..

* It's always on top and doesn't show in the taskbar.

* The window is transparent and has a customizable transparency when dragging
  it with the "Shift" key pressed. That requires a compositing window manager.

* Fully resizable when dragging it with the "Ctrl" key pressed.

* The window can be flipped and adjusts itself to vertical/horizontal when
  resized.

* Works fine with file/directory names that includes whitespace or unicode.


.. _setuptools: https://pypi.python.org/pypi/setuptools
.. _distutils: https://docs.python.org/2/library/distutils.html
.. _2d14857: https://github.com/gorakhargosh/watchdog/commit/2d14857c
.. _104: https://github.com/gorakhargosh/watchdog/issues/104
.. _157: https://github.com/gorakhargosh/watchdog/issues/157
.. _watchdog: https://pypi.python.org/pypi/watchdog
