Dose
====

An automated semaphore GUI showing the state in
test driven development (TDD), mainly written for dojos.

Directory and watching
----------------------

**Dose** watches one directory for any kind of change
new file, file modified, file removed, subdirectory renamed,
etc., including its subdirectories, by using the Python
watchdog package. For example, changes on files ending on
'.pyc' and '.pyo' are neglect by default, as well as git
internals, but these skip patterns are *customizable*.

What happens when something changes?
------------------------------------

A *customized* subprocess is called, all its output/error
data is left on the shell used to call Dose, and its return
value is stored. If the value is zero, the semaphore turns
green, else it it turns red. It stays yellow while waiting
the subprocess to finish.

Is it easy to use or should I spend hours to set it up?
-------------------------------------------------------

The default directory path to watch is the one used to call
Dose. There's no default calling string, but 'nosetests' and
'py.test' would be hints for Python developers. It should
work even with other languages TDD tools. To be fast, just
open Dose and double click on it, there's no need to lose
time with settings.

And the GUI?
------------

The GUI toolkit used in this project is wxPython. You can
move the semaphore by dragging it around. Doing so with
Ctrl pressed would resize it. With Shift you change its
transparency (not available on Linux, for now). The
semaphore window always stays on top. A right click would
show all options available.

----

Copyright (C) 2012 Danilo de Jesus da Silva Bellini
- danilo [dot] bellini [at] gmail [dot] com

License is GPLv3. See COPYING.txt for more details.
