# -*- coding: utf-8 -*-
"""
Dose - Automated semaphore GUI showing the state in test driven development
Copyright (C) 2012 Danilo de Jesus da Silva Bellini

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Created on Sat Sep 29 2012
danilo [dot] bellini [at] gmail [dot] com
"""

from __future__ import division, print_function, unicode_literals
import wx, os, json, threading
from datetime import datetime
from fnmatch import fnmatch
from functools import wraps

from . import terminal

# Thresholds and other constants
PI = 3.141592653589793
MIN_WIDTH = 9 # Pixels
MIN_HEIGHT = 9
FIRST_WIDTH = 100 # FIRST_* are starting values
FIRST_HEIGHT = 300
MIN_OPACITY = 0x10 # Color intensity in byte range
MAX_OPACITY = 0xff
FIRST_OPACITY = 0x9f
MOUSE_TIMER_WATCH = 20 # ms
CONFIG_SAVE_LAG = 200 # ms
LED_OFF = 0x3f3f3f # Color
LED_RED = 0xff0000
LED_YELLOW = 0xffff00
LED_GREEN = 0x00ff00
FIRST_LEDS = (LED_RED, LED_YELLOW, LED_GREEN) # Standby colors
LEDS_RED = (LED_RED, LED_OFF, LED_OFF)
LEDS_YELLOW = (LED_OFF, LED_YELLOW, LED_OFF)
LEDS_GREEN = (LED_OFF, LED_OFF, LED_GREEN)
BACKGROUND_COLOR = 0x000000
BACKGROUND_BORDER_COLOR = 0x7f7f7f7f
FILENAME_PATTERN_TO_IGNORE = "; ".join(["*.pyc",
                                        "*.pyo",
                                        ".git/*",
                                        "__pycache__/*",
                                        "*__pycache__/*",
                                        "__pycache__",
                                        ".*",
                                        "*~",
                                        "qt_temp.*", # Kate
                                       ])
CONFIG_FILE_NAME = ".dose.conf"
CONFIG_DEFAULT_OPTIONS = {
  "position": (-1, -1), # by default let the win system decide
  "size": (FIRST_WIDTH, FIRST_HEIGHT),
  "opacity": FIRST_OPACITY,
  "flipped": False
}

def rounded_rectangle_region(width, height, radius):
  """
  Returns a rounded rectangle wx.Region
  """
  bmp = wx.EmptyBitmapRGBA(width, height) # Mask color is #000000
  dc = wx.MemoryDC(bmp)
  dc.Brush = wx.Brush((255,) * 3) # Any non-black would do
  dc.DrawRoundedRectangle(0, 0, width, height, radius)
  dc.SelectObject(wx.NullBitmap)
  bmp.SetMaskColour((0,) * 3)
  return wx.RegionFromBitmap(bmp)

def int_to_color(color_int):
  """
  Returns a color string from a 24bits integer
  """
  return "#{0:06x}".format(color_int)# + "7f"

def int_to_darkened_color(color_int):
  """
  Returns a color string from a 24bits integer with all components halved
  """
  return int_to_color((color_int >> 1) & 0x7f7f7f) # Divide by 2 every color


class DoseGraphicalSemaphore(wx.Frame):
  """
  Graphical semaphore frame widget (window)
  Property "leds" contains the colors that should be seen (a 3-tuple with
  24bit integers but can receive any sequence that quacks alike).
  Property "opacity" controls transparency alpha factor from 0x00 (fully
  transparency) to 0xff (no transparency)
  Property "flip" is a boolean that can reverse the led order
  This class knows nothing about the led color meaning, and just print them
  at the screen.
  """
  def __init__(self, parent, leds=FIRST_LEDS):
    self._config = config = DoseConfig()
    frame_style = (wx.FRAME_SHAPED |     # Allows wx.SetShape
                   wx.FRAME_NO_TASKBAR |
                   wx.STAY_ON_TOP |
                   wx.NO_BORDER
                  )
    super(DoseGraphicalSemaphore, self).__init__(parent, style=frame_style,
                                                 pos=config["position"])
    #self.BackgroundStyle = wx.BG_STYLE_CUSTOM # Avoids flicker
    self.Bind(wx.EVT_ERASE_BACKGROUND, lambda evt: None)
    self.Bind(wx.EVT_WINDOW_CREATE,
              lambda evt: self.SetTransparent(FIRST_OPACITY)
             ) # Needed to at least have transparency on wxGTK
    self._paint_width, self._paint_height = 0, 0 # Ensure update_sizes at
                                                 # first on_paint
    # Uses configuration (without changing the config dictionary)
    self.ClientSize = config["size"]
    self._flip = config["flipped"]
    self._opacity = config["opacity"]
    self.SetTransparent(config["opacity"])

    self.Bind(wx.EVT_PAINT, self.on_paint)
    self.leds = leds # Refresh!

  @property
  def leds(self):
    return self._leds

  @leds.setter
  def leds(self, values):
    if len(values) != 3:
      raise ValueError("There should be 3 leds")
    self._leds = tuple(values)
    self.Refresh()

  @property
  def size(self):
    return self.ClientSize

  @size.setter
  def size(self, pair):
    self.ClientSize = self._config["size"] = pair
    self.SendSizeEvent() # Needed for wxGTK

  @property
  def pos(self):
    return self.Position

  @pos.setter
  def pos(self, pair):
    self.Position = self._config["position"] = pair
    self.Refresh()

  @property
  def opacity(self):
    return self._config["opacity"]

  @opacity.setter
  def opacity(self, value):
    self._config["opacity"] = value
    self.SetTransparent(value)

  @property
  def flip(self):
    return self._config["flipped"]

  @flip.setter
  def flip(self, value):
    if self._config["flipped"] != value:
      self._config["flipped"] = value
      self.Refresh()

  def on_paint(self, evt):
    if self.size != (self._paint_width, self._paint_height):
      self._update_sizes()
    self._draw()

  def _update_sizes(self):
    self._paint_width, self._paint_height = self.size
    self._rotation = -PI/2 if self._paint_width > self._paint_height else 0
    self._tile_size = min(max(self._paint_width, self._paint_height),
                          min(self._paint_width, self._paint_height) * 3
                         ) / 3
    self._border = self._tile_size * .15
    self._frame_pen_width = self._border / 3 # Half clipped (frame shape)
    self._pen_width = self._border / 4
    dist_circles = self._border / 5
    self._radius = (self._tile_size - 2 * self._pen_width - dist_circles) / 2
    self.SetShape(rounded_rectangle_region(self._paint_width,
                                           self._paint_height,
                                           self._border)
                 )

  def _draw(self):
    dc = wx.AutoBufferedPaintDCFactory(self)
    gc = wx.GraphicsContext.Create(dc) # Anti-aliasing
    gc.Translate(self._paint_width / 2,
                 self._paint_height / 2) # Center

    # Draw the background
    gc.SetBrush(wx.Brush(int_to_color(BACKGROUND_COLOR)))
    gc.SetPen(wx.Pen(int_to_color(BACKGROUND_BORDER_COLOR),
                     width=self._frame_pen_width)
             )
    gc.DrawRoundedRectangle(-self._paint_width / 2,
                            -self._paint_height / 2,
                            self._paint_width,
                            self._paint_height,
                            self._border)

    # Draw the LEDs
    gc.Rotate(self._rotation)
    if self.flip:
      gc.Rotate(PI)
    gc.Translate(0, -self._tile_size)

    for led in self.leds: # The led is an integer with the color
      gc.SetBrush(wx.Brush(int_to_color(led)))
      gc.SetPen(wx.Pen(int_to_darkened_color(led),
                       width=self._pen_width)
               )
      gc.DrawEllipse(-self._radius,
                     -self._radius,
                     2 * self._radius,
                     2 * self._radius)
      gc.Translate(0, self._tile_size)


class DoseInteractiveSemaphore(DoseGraphicalSemaphore):
  """
  Just a DojoGraphicalSemaphore, but now responsive to left click
  """
  def __init__(self, parent):
    super(DoseInteractiveSemaphore, self).__init__(parent)
    self._timer = wx.Timer(self)
    self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
    self.Bind(wx.EVT_TIMER, self.on_timer, self._timer)

  def on_left_down(self, evt):
    self._key_state = None # Ensures initialization
    self.on_timer(evt)

  def on_timer(self, evt):
    """
    Keep watching the mouse displacement via timer
    Needed since EVT_MOVE doesn't happen once the mouse gets outside the
    frame
    """
    ctrl_is_down = wx.GetKeyState(wx.WXK_CONTROL)
    shift_is_down = wx.GetKeyState(wx.WXK_SHIFT)
    ms = wx.GetMouseState()
    new_pos = None

    # New initialization when keys pressed change
    if self._key_state != (ctrl_is_down, shift_is_down):
      self._key_state = (ctrl_is_down, shift_is_down)

      # Keep state at click
      self._click_ms_x, self._click_ms_y = ms.x, ms.y
      self._click_frame_x, self._click_frame_y = self.pos
      self._click_frame_width, self._click_frame_height = self.size
      self._click_opacity = self.opacity

      # Avoids refresh when there's no move (stores last mouse state)
      self._last_ms = ms.x, ms.y

      # Quadrant at click (need to know how to resize)
      width, height = self.size
      self._quad_signal_x = 1 if (self._click_ms_x -
                                  self._click_frame_x) / width > .5 else -1
      self._quad_signal_y = 1 if (self._click_ms_y -
                                  self._click_frame_y) / height > .5 else -1

    # "Polling watcher" for mouse left button while it's kept down
    if (wx.__version__ >= "3" and ms.leftIsDown) or \
       (wx.__version__ <  "3" and ms.leftDown):
      if self._last_ms != (ms.x, ms.y): # Moved?
        self._last_ms = (ms.x, ms.y)
        delta_x = ms.x - self._click_ms_x
        delta_y = ms.y - self._click_ms_y

        # Change transparency / opacity
        if shift_is_down:
          self.opacity = max(MIN_OPACITY,
                             min(MAX_OPACITY, self._click_opacity - delta_y)
                            )

        # Resize
        if ctrl_is_down:
          # New size
          new_w = max(MIN_WIDTH, self._click_frame_width +
                                 2 * delta_x * self._quad_signal_x
                     )
          new_h = max(MIN_HEIGHT, self._click_frame_height +
                                  2 * delta_y * self._quad_signal_y
                     )
          self.size = new_w, new_h

          # Center should be kept
          center_x = self._click_frame_x + self._click_frame_width / 2
          center_y = self._click_frame_y + self._click_frame_height / 2
          new_pos = (center_x - new_w / 2,
                     center_y - new_h / 2)

        # Move the window
        if not (ctrl_is_down or shift_is_down):
          new_pos = (self._click_frame_x + delta_x,
                     self._click_frame_y + delta_y)

      if new_pos is not None:
        self.pos = new_pos

      # Since left button is kept down, there should be another one shot
      # timer event again, without creating many timers like wx.CallLater
      self._timer.Start(MOUSE_TIMER_WATCH, True)


class DosePopupMenu(wx.Menu):

  def __init__(self, hc, watching):
    """
    Dose pop-up menu widget constructor
    The "hc" (handler class) parameter should be a class with all the needed
    callback methods.
    """
    super(DosePopupMenu, self).__init__()

    # Define menu data
    menu_items = [("Flip", hc.on_flip),
                  (None, None),
                 ]
    if watching:
      menu_items.extend([("Stop!\tDouble Click", hc.on_stop),
                         (None, None),
                         ("Red", hc.on_red),
                         ("Yellow", hc.on_yellow),
                         ("Green", hc.on_green),
                        ])
    else:
      menu_items.extend([("Start!\tDouble Click", hc.on_start),
                         (None, None),
                         ("Directory to watch...", hc.on_directory_to_watch),
                         ("Define call string...", hc.on_define_call_string),
                         ("Ignore pattern...", hc.on_skip_pattern),
                        ])
    menu_items.extend([(None, None),
                       ("Close\tAlt+F4", hc.on_close),
                       (None, None),
                       ("About...", hc.on_about),
                      ])

    # Create the menu items
    for txt, callback in menu_items:
      if txt is None:
        self.AppendSeparator()
      else:
        item = wx.MenuItem(self, wx.ID_ANY, txt)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, callback, item)


class DoseWatcher(object):
  """
  A class to watch
  """
  def __init__(self):
    self.directory = os.path.curdir # Default directory
    self.call_string = ""
    self.skip_pattern = FILENAME_PATTERN_TO_IGNORE
    self._watching = False

  @property
  def watching(self):
    return self._watching

  def has_call_string(self):
    return len(self.call_string.strip()) > 0

  def _end_callback(self, result):
    if self._runner.killed:
      if self._runner.spawned:
        terminal.clog.magenta("*** Killed! ***")
    elif result == 0:
      self.on_green()
      self._last_fnames = []
    else:
      self.on_red()
      self._last_fnames = []

  def _exc_callback(self, exc_type, exc_value, traceback):
    from traceback import format_exception
    self.stop() # Watching no more
    terminal.hr.red("=")
    terminal.clog.red("[Dose] Error while trying to run the test job")
    terminal.hr.red("=")
    for line in format_exception(exc_type, exc_value, traceback):
      terminal.log.magenta(line.rstrip())
    terminal.hr.red("=")
    self.on_stop(exc_value)

  def _emit_end(self, result):
    wx.CallAfter(self._end_callback, result)

  def _emit_exc(self, exc_type, exc_value, traceback):
    wx.CallAfter(self._exc_callback, exc_type, exc_value, traceback)

  def _print_timestamp(self):
    timestamp = datetime.now()
    terminal.hr.yellow("=")
    terminal.clog.yellow("[Dose] {0}".format(timestamp))
    terminal.hr.yellow("=")

  def _print_header(self, evt=None):
    if evt is None:
      terminal.clog.cyan("*** First call ***")
    else:
      terminal.clog.cyan("*** {item} {event}: {path} ***".format(
        item = "Directory" if evt.is_directory else "File",
        event = evt.event_type,
        path = os.path.relpath(evt.src_path, self.directory),
      ))

  def _run_subprocess(self):
    if self.watching:
      from .runner import RunnerThreadCallback
      self._print_header(self._evts.pop())
      if not self._evts: # Multiple events at once, only the last should run
        self.on_yellow() # State changed: "waiting" for a subprocess to finish
        self._runner = RunnerThreadCallback(test_command=self.call_string,
                                            work_dir=self.directory,
                                            before=self._print_timestamp,
                                            after=self._emit_end,
                                            exception=self._emit_exc)

  def _watchdog_handler(self, evt):
    self._last_fnames.append(os.path.relpath(evt.src_path, self.directory))
    self._runner.kill() # Triggers end/exception callback
    self._evts.append(evt)
    wx.CallAfter(self._run_subprocess) # After the runner callbacks

  def start(self):
    """Starts watching the path and running the test jobs."""
    assert not self.watching

    def selector(evt):
      if evt.is_directory:
        return False
      path = os.path.relpath(evt.src_path, self.directory)
      if path in self._last_fnames: # Detected a "killing cycle"
        return False
      for pattern in self.skip_pattern.split(";"):
        if fnmatch(path, pattern.strip()):
          return False
      return True

    def watchdog_handler(evt):
      wx.CallAfter(self._watchdog_handler, evt)

    # Force a first event
    self._watching = True
    self._last_fnames = []
    self._evts = [None]
    self._run_subprocess()

    # Starts the watchdog observer
    from .watcher import watcher
    self._watcher = watcher(path=self.directory.encode("utf-8"),
                            selector=selector, handler=watchdog_handler)
    self._watcher.__enter__() # Returns a started watchdog.observers.Observer

  def stop(self):
    if self.watching:
      self._watcher.__exit__(None, None, None)
      self._runner.kill()
      self._watching = False


def call_after(lag):
  """
  Parametrized decorator for calling a function after a time ``lag`` given
  in milliseconds. This cancels simultaneous calls.
  """
  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      wrapper.timer.cancel() # Debounce
      wrapper.timer = threading.Timer(lag, func, args=args, kwargs=kwargs)
      wrapper.timer.start()
    wrapper.timer = threading.Timer(0, lambda: None) # timer.cancel now exists
    return wrapper
  return decorator


class DoseConfig(dict):
  """
  Handle load and storage of configuration options.

  When dose starts, try to load configurations from
  a file named ".dose.conf" in the following locations:

  1) Working directory
  2) User home

  If none of these files are present, dose fallback to default values.
  Configuration changes automatically schedules its storage/saving process to
  the configuration file after a few milliseconds.
  """
  path = os.path.join(os.path.expanduser("~"), CONFIG_FILE_NAME)

  def __missing__(self, key): # This allows saving ONLY what changes
    return CONFIG_DEFAULT_OPTIONS[key]

  def __setitem__(self, k, v):
    super(DoseConfig, self).__setitem__(k, v)
    self.store_options()

  @call_after(CONFIG_SAVE_LAG * 1e-3)
  def store_options(self):
    with open(self.path, "w") as config_file:
      json.dump(self, config_file, indent=4, separators=(',',': '))

  def __init__(self):
    if os.path.exists(DoseConfig.path):
      with open(DoseConfig.path, "r") as config_file:
        self.update(json.load(config_file))
    if os.path.exists(CONFIG_FILE_NAME):
      self.path = os.path.abspath(CONFIG_FILE_NAME)
      with open(self.path, "r") as config_file:
        self.update(json.load(config_file))


class DoseMainWindow(DoseInteractiveSemaphore, DoseWatcher):

  def __init__(self, parent):
    DoseInteractiveSemaphore.__init__(self, parent)
    DoseWatcher.__init__(self)
    self.SetTitle("Disabled - dose") # Seen by the window manager
    self.popmenu = {k:DosePopupMenu(self, k) for k in (True, False)}

    self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
    self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
    self.Bind(wx.EVT_CLOSE, self.on_close)

  def auto_start(self, test_command):
    self.call_string = test_command
    self.on_start()

  def on_right_down(self, evt):
    self.PopupMenu(self.popmenu[self.watching], evt.Position)

  def on_left_dclick(self, evt):
    if self.watching:
      self.on_stop()
    else:
      self.on_start()

  def on_flip(self, evt):
    self.flip = not self.flip

  def on_red(self, evt=None):
    self.leds = LEDS_RED

  def on_yellow(self, evt=None):
    self.leds = LEDS_YELLOW

  def on_green(self, evt=None):
    self.leds = LEDS_GREEN

  def on_start(self, evt=None):
    if not self.has_call_string():
      self.on_define_call_string()

    if self.has_call_string():
      self.start()

  def on_stop(self, evt=None):
    self.stop()
    self.leds = FIRST_LEDS
    if isinstance(evt, Exception):
      msg = "Exception '{0}' raised"
      wx.MessageDialog(self, str(evt),
                       msg.format(repr(evt).split("(")[0]),
                       wx.ICON_INFORMATION | wx.OK
                      ).ShowModal()

  def on_directory_to_watch(self, evt):
    dd = wx.DirDialog(self, message="Directory to watch...",
                      defaultPath=self.directory)
    if dd.ShowModal() == wx.ID_OK:
      self.directory = dd.Path

  def on_define_call_string(self, evt=None):
    msg = "Executable to be called and its arguments:"
    title = "Dose call string"
    ted = wx.TextEntryDialog(self, message=msg, caption=title,
                             defaultValue=self.call_string)
    if ted.ShowModal() == wx.ID_OK:
      self.call_string = ted.Value

  def on_skip_pattern(self, evt):
    msg = "File names, separated by ';', to have their changes neglected:"
    title = "Skip pattern"
    ted = wx.TextEntryDialog(self, message=msg, caption=title,
                             defaultValue=self.skip_pattern)
    if ted.ShowModal() == wx.ID_OK:
      self.skip_pattern = ted.Value

  def on_close(self, evt):
    """
    Pop-up menu and "Alt+F4" closing event
    """
    self.stop() # DoseWatcher
    if evt.EventObject is not self: # Avoid deadlocks
      self.Close() # wx.Frame
    evt.Skip()

  def on_about(self, evt):
    from .about import about_box
    about_box()
