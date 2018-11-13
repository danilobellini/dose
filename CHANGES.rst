Dose change log
===============

The section titles in this change log are the tag names in the git
repository.


Development
-----------

* Add wxPython as a dependency, so a ``pip install dose`` should be
  the whole installation procedure in a virtualenv.
  The documentation was updated to the new installation procedure
  and it now includes a link to its AUR package (Arch Linux).

* Update the McCabe complexity limit to 9 in flake8_ to let it pass
  in all tests (7 was too small).

* Use ``collections.abc`` for testing when available, to avoid
  misleading warnings regarding the still unreleased Python 3.8.

* Create ``dose.compat.allow_implicit_stop`` decorator to let Dose work
  in Python 3.7, removing the warnings in older Python versions.

* Require a newer watchdog_ version (``>=0.9.0``), deprecating the
  patch regarding out-of-order inotify events.

* Rewrite the overall border drawing to minimize a light gray visual
  glitch in the rounded borders.

* Fix the egg long description to have a distinct path for GitHub
  links and GitHub images, based on the relative URLs of the project
  files. That's a reStructuredText generated from the Dose
  documentation by the setup script, and uploaded to PyPI on each
  release. The previous release required a manual to fix these links.


v1.2.0
------

* Add wxPython Phoenix compatibility. Dose works with either wxPython
  Classic (2.8/3.0) or Phoenix. The new ``dose.compat.wx`` lazily
  loads wxPython using the Phoenix naming conventions.

* First version running on Python 3 (using wxPython Phoenix)! It won't
  run on CPython 3.2 due to some "u"-prefixed unicode literals. Dose
  requires either CPython 2.7 or CPython 3.3+ as long as that complies
  with the wxPython requirements.

* Compatibility with Microsoft Windows is back! This release runs on
  Windows (and Cygwin) platforms/environments.

  For coloring on Windows, Dose has a new dependency, colorama_\ ,
  which allows the ANSI codes to be properly mapped to the
  ``SetConsoleTextAttribute`` function from the Windows Console
  Handles API.

* New "Help..." popup menu item that displays a new window containing
  most of the ``README.rst`` and ``CHANGES.rst`` contents. It also
  includes a table of contents with links to the text sections.
  Clicking on an external link opens it in the default web browser.

  This feature requires docutils_ for converting the reStructuredText
  data to HTML, therefore it's a new Dose dependency. There's no extra
  dependency for rendering the resulting HTML, wxPython provides
  the ``HtmlWindow`` widget that renders an HTML subset, and it's
  enough for this task.

* Collects the console/terminal width to show the Dose messages
  properly centered, and for "horizontal rulers" ("====" lines) to
  fill the whole line. If the SIGWINCH (window changed) signal is
  available in the system, it's used to get the new width when the
  console window gets resized. Anyway, the width is always retrieved
  before calling a test job.

  On Windows, Dose doesn't print a character in the last column. That
  avoids skipping a line due to an implicit line feed when that
  visible column is also the last buffer column.

* Bug fix: previously, Dose couldn't run on terminals without a
  detected encoding. With that fixed, Dose can be piped, allowing
  commands like::

    dose | tee tests.log

  For running Dose writing its output to ``tests.log``, and::

    dose | xargs -d'\n' -n1

  For refreshing whole lines at once.

* Bug fix: paths (directories/files names) are always decoded using
  the filesystem encoding instead of UTF-8.

* Use the default accelerator for closing a window in the operating
  system (e.g. Alt+F4). Also, the accelerators were removed from the
  menu, avoiding a warning for the invalid "Double Click" accelerator.

* More abstract setup.py that installs from anywhere and gets the
  shared files from the ``MANIFEST.in``.

* New shared resources loader that gets the Dose resources from the
  ``sys.prefix`` directory, leaving the setuptools ``pkg_resources``
  package resource loader as a fallback. Therefore, Dose no longer
  require setuptools_\ , but for installation.

  A wheel_\ /\ pip_ installation actually stores the shared resources
  in a path relative to ``sys.prefix``, so ``pip install .`` is the
  recommended way to install dose from a source distribution.

* Cache the terminal printer functions (e.g. the ones used for
  coloring) as a slight optimization.

* Include a minimal test suite for Dose with a code coverage report.
  The test suite includes a flake8_ environment for code
  linting, McCabe complexity verification and style checking.
  The shoemaker's son always goes barefoot, or at least it did until
  now. Better late than never.

* Include detailed instructions on how to install Dose and its
  requirements in a Python virtualenv or in the system on all
  platforms it supports (Linux, Mac OS X, Windows, Cygwin).

* Add a screenshot for each platform Dose supports.


v1.1.1
------

* Faster! Dose waits just 10ms before spawning a test job, and
  spawns only a single test job subprocess when multiple files are
  modified at once.

  Towards an event that triggers a new test job while another job
  is running, the test job subprocess is killed immediately,
  unless it happens during the first 50ms after spawning, where
  the kill happens after that delay.

  That avoids new test job runners as much as possible and it's faster
  than spawning a runner for each event just to kill it afterwards, as
  Dose used to do. The kill delay wasn't explicit, but it used
  to have a 50ms polling loop querying for a spawned subprocess.

  The 10ms pre-spawn delay is evaluated in a 1ms polling loop, and
  simultaneous file modification events are joined together before
  that. In other words, Dose can abort a test job as early as
  possible.

* More compact logging, without information about the repeated/cyclic
  file modification detection, and printing timestamps only for a
  spawned test job.

* Revert file creation/deletion to trigger a test job. Any event on
  a file (i.e., any file creation/modification/deletion) trigger a
  test job. On the other hand, events on directories are ignored.

  Actually, it's a bug fix. At least the file creation is required on
  Mac OS X as some applications (e.g. vim) delete and create a file
  instead of modifying it, w.r.t. the watchdog events.

* Bug fix: some calls were replaced by event messages to let the main
  window be refreshed by the main thread (thread-safe) instead of a
  test job runner thread or a watcher thread.

  That refresh happens when dose toggles its green/yellow/red color
  and when the watching stops due to some internal exception.
  Updating the GUI from outside the wxPython event loop (main thread)
  can cause a segmentation fault.

* Bug fix: multi-byte unicode characters have been being written to
  the standard error with an ANSI escape code in between. For example,
  it was printing ``Ã§Ã§`` (``u"\u00c3\u00a7"``, or
  ``b"\xc3\x83\xc2\xa7"`` encoded in UTF-8), instead of ``çç``
  (``u"\u00e7"``, or ``b"\xc3\xa7"`` encoded in UTF-8). Now it reads
  whole characters based on the terminal encoding.

* Bug fix: the "About..." was broken due to fragmentation, as the
  metadata variables it requires were moved to another file. While
  fixing it, the resulting about box was rebuilt to use the package
  text files themselves instead of some hardcoded text to be
  manually updated. Actually, that would require a direct setuptools_
  installation (i.e., calling ``python2 setup.py install``) instead
  of a pip installation to properly work, as the setuptools ``setup``
  and its ``pkg_resources.resource_string`` don't use the
  ``sys.prefix`` as the shared resources root directory.

* Bug fix: use the watching directory as the working directory for
  running the test command instead of the current working directory
  whereby Dose was called.

* Internal exceptions from the test job runner thread can't be
  handled, but the header was updated to be more informative::

    [Dose] Error while trying to run the test job

  And a traceback is print.

* Rename "Skip pattern" to "Ignore pattern" in the GUI.

* This release isn't natively compatible with Windows due to the lack
  of a ``os.WNOHANG`` constant in the Python standard library,
  required by Dose when it waits for its child process (the test job)
  to be killed before running another one. For running on Windows,
  this release requires Cygwin.


v1.1.0
------

* To avoid several simultaneous triggers for a single action being
  done (e.g. lots of events for each file while creating the source
  distribution to test with ``tox``), only the file modifications
  events trigger a new test job.

* Brand new *killing* feature: the running test subprocess is killed
  when another event is triggered, and there's no delay to start the
  test job subprocess anymore. Cycles are detected to avoid an endless
  killing-spawning loop. To kill the current running process
  purposefully, one just need to double-click dose with the left mouse
  button.

* New test job runner with realtime standard output/error streams.
  Each output/error byte is printed as soon as possible, instead
  of waiting the process to finish.

* New colored output by printing the ANSI escape codes. The different
  colors used are:

  - Testing process standard error (sys.strerr): red.
  - Test job timestamp: yellow.
  - "Killed!" message: magenta/purple.
  - Event header/description: cyan/turquoise.
  - Exceptions: red.

  The messages themselves were modified to be centralized including
  only the timestamp prefixed by ``[Dose]``.

  On Windows releases older than the 10 TH2 (Windows 10 Threshold 2),
  only the Cygwin Terminal supports the ANSI escape codes. This Dose
  release still runs on Windows consoles that doesn't support these
  codes, but the messages appear with the escape codes printed like
  ``←[33m`` instead of changing the color.

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

  The arguments are properly escaped when joining them as a single
  shell command to call ``subprocess.Popen``, unless there's only a
  single argument, which might include pipes and redirection.


v1.0.1
------

* Add compatibility with wxPython 3.0 (classic), it's the first
  release compatible with both wxPython 2.8 and 3.0.

* The event information header for each job is processed to show just
  the file/directory name and whether it was created, modified or
  deleted, e.g.::

    *** File created: mypackage/mymodule.py ***

* The unicode characters in file/directory names appears themselves in
  the event headers instead of an escaped representation, e.g.::

    *** Directory deleted: CAS Proofs/λ Calculus ***

  with ``λ`` instead of the raw event representation escaped with
  ``\xce\xbb``::

    ***<DirDeletedEvent: src_path='./CAS Proofs/\xce\xbb Calculus'>***


v1.0.0
------

* First beta release. From now on, Dose releases comply with the
  semantic versioning conventions. Environments with an alpha version
  installed should remove it and reinstall dose to upgrade it
  properly.

* The CLI arguments (``sys.argv``) are used as the default test
  command, passing the remaining parameters to the test command
  itself. For example, one can call dose with something like this
  directly::

    dose.py py.test -k TestSomething

  When the test command is provided like so, dose already starts
  running the first test job and watching for filesystem events.

* The test command can be any shell command with pipes/redirections,
  e.g. one can call::

    dose.py "cat my_input.txt | my_test_script.sh"

* The default opacity/transparency is slightly more opaque.

* The wxPython package isn't included as a requirement anymore as it
  requires an external installation procedure (e.g. the package
  manager of a Linux distribution or an installer for Windows).

* New logging header for each test job, showing the raw watchdog
  information about the event that triggered the test command, like::

    ***<FileCreatedEvent: src_path='./mypackage/mymodule.py'>***

  and this message for the only event that have nothing to do with
  watchdog::

    *** First call ***

* Bug fix: the "skip"/ignore pattern can be customized. That was
  already an option in the GUI, but it was updating the test command
  instead, rendering it unusable.

* Bug fix: the test command can include quoted arguments if it's
  passed as a single CLI argument or filled using the "call string"
  dialog box.

* Updated the default "skip"/ignore pattern to ignore ``__pycache__``
  directories.

  Intended to address the same issue regarding multiple test jobs for
  a single action, the test command runs one second after the watchdog
  event, instead of a half. This seems like a residual from experiments
  that happened before the event logging header was implemented.

* License fix: consistently using GPLv3 instead of GPLv3+.


alpha-2012.10.04
----------------

* Use setuptools_ instead of just distutils_ in the setup script,
  allowing it to look for and install the watchdog_ requirement and
  its dependencies, recursively. It can be installed using ``pip`` or
  ``easy_install``, as long as the wxPython 2.8 (classic) was
  previously installed.

* Customizable file/directory name "skip"/ignore pattern that
  defaults to ``*.pyc; *.pyo; .git/*``. This was done mainly to deal
  with the "bounce" issue (multiple events for a single action), as
  the ignore pattern "debounces" a new event that would otherwise
  happen after a compilation.

  Another approach used to attenuate that issue was a sleep of half a
  second to trigger the test command. Watchdog drops consecutive
  events that are duplicated, and used to drop non-consecutive
  duplicate events from its internal queue as well (watchdog commit
  2d14857_\ ).

* Force UTF-8 encoding on the watched directory name, this might have
  been an issue when handling non-ascii paths (watchdog issues 104_
  and 157_\ , now fixed in watchdog itself). Taking the opportunity,
  this alpha release switched the string literals to unicode.


alpha-2012.10.02
----------------

* First version!

  It's a language-agnostic borderless "traffic light/signal/semaphore"
  GUI for TDD (Test Driven Development), mainly intended for use in
  Coding Dojos, hence its name: it's a *Dojo Semaphore*\ , a name that
  has the same leading syllables in both English and Portuguese.

* Written in Python 2 using the wxPython 2.8 GUI library.

* Compatibility with both Linux and Windows.

* It recursively watches a working directory (defaults to the current
  directory) for every file/subdirectory creation, modification and
  deletion that happens inside it, triggering a test job.

* Avoids file/directory polling whenever possible, using the watchdog_
  package for that.

* The test command can be any customizable shell command, like
  ``python -m doctest``, ``py.test -k test_my_new_feature``,
  ``tox -e py34,pypy``, ``./run_tests.sh``, etc..

* It's always on top and doesn't show in the taskbar.

* The window is transparent and has a customizable transparency when
  dragging it with the "Shift" key pressed. That requires a
  compositing window manager.

* Fully resizable when dragging it with the "Ctrl" key pressed.

* The window can be flipped and adjusts itself to vertical/horizontal
  when resized.

* Works fine with file/directory names that includes whitespace or
  unicode.


.. _colorama: https://pypi.python.org/pypi/colorama
.. _wheel: http://wheel.readthedocs.io
.. _pip: https://pip.pypa.io
.. _flake8: https://pypi.python.org/pypi/flake8
.. _docutils: https://pypi.python.org/pypi/docutils
.. _setuptools: https://pypi.python.org/pypi/setuptools
.. _distutils: https://docs.python.org/2/library/distutils.html
.. _2d14857: https://github.com/gorakhargosh/watchdog/commit/2d14857c
.. _104: https://github.com/gorakhargosh/watchdog/issues/104
.. _157: https://github.com/gorakhargosh/watchdog/issues/157
.. _watchdog: https://pypi.python.org/pypi/watchdog
