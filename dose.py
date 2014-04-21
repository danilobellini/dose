#!/usr/bin/env python
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
import wx
import wx.lib.masked
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from subprocess import Popen, PIPE
from datetime import datetime
import os
import time
from fnmatch import fnmatch
import json

# Metadata (see setup.py for more information about these)
__version__ = "1.0.1"
__author__ = "Danilo de Jesus da Silva Bellini"
__author_email__  = "danilo [dot] bellini [at] gmail [dot] com"
__url__ = "http://github.com/danilobellini/dose"

# Thresholds and other constants
PI = 3.141592653589793
MIN_WIDTH = 9 # Pixels
MIN_HEIGHT = 9
TIMER_HORIZONTAL_SPACERS = 80
TIMER_VERTICAL_SPACERS = 20
FIRST_WIDTH = 100 # FIRST_* are starting values
FIRST_HEIGHT = 300
FIRST_TIMER_WIDTH = 300 # FIRST_* are starting values
FIRST_TIMER_HEIGHT = 50
FIRST_FRAME_X = 50
FIRST_FRAME_Y = 50
FIRST_FRAME_GAP = 10
MIN_OPACITY = 0x10 # Color intensity in byte range
MAX_OPACITY = 0xff
FIRST_OPACITY = 0x9f
FIRST_TIMER_OPACITY = 0x9f
MOUSE_TIMER_WATCH = 20 # ms
LED_OFF = 0x3f3f3f # Color
LED_RED = 0xff0000
LED_YELLOW = 0xffff00
LED_GREEN = 0x00ff00
FIRST_LEDS = (LED_RED, LED_YELLOW, LED_GREEN) # Standby colors
LEDS_RED = (LED_RED, LED_OFF, LED_OFF)
LEDS_YELLOW = (LED_OFF, LED_YELLOW, LED_OFF)
LEDS_GREEN = (LED_OFF, LED_OFF, LED_GREEN)
BACKGROUND_COLOR = 0x000000
FOREGROUND_COLOR = 0xffffff
BACKGROUND_BORDER_COLOR = 0x7f7f7f7f
TERMINAL_WIDTH = 79
FILENAME_PATTERN_TO_IGNORE = "; ".join(["*.pyc",
                                        "*.pyo",
                                        ".git/*",
                                        "__pycache__/*",
                                        "*__pycache__/*",
                                        "__pycache__",
                                        ".*"
                                       ])
TIME_BEFORE_CALL = 1.0 # seconds between event and the call action
CONFIG_FILE_NAME = ".dose.conf"
CONFIG_DEFAULT_OPTIONS = {
  "semaphore_position": (FIRST_FRAME_X, FIRST_FRAME_Y),
  "semaphore_size": (FIRST_WIDTH, FIRST_HEIGHT),
  "semaphore_opacity": FIRST_OPACITY,
  "semaphore_flipped": False,
  "timer_position": (FIRST_FRAME_X, 
                     FIRST_FRAME_Y + FIRST_HEIGHT + FIRST_FRAME_GAP),
  "timer_size": (FIRST_TIMER_WIDTH, FIRST_TIMER_HEIGHT),
  "timer_opacity": FIRST_TIMER_OPACITY
}
DEFAULT_FRAME_STYLE = (wx.FRAME_SHAPED |     # Allows wx.SetShape
                       wx.FRAME_NO_TASKBAR |
                       wx.STAY_ON_TOP |
                       wx.NO_BORDER
                      )

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


class DoseGraphicalBaseFrame(wx.Frame):

  def __init__(self, parent, pos, size,
               opacity, frame_style=DEFAULT_FRAME_STYLE):
    super(DoseGraphicalBaseFrame, self).__init__(parent, style=frame_style,
                                        pos=pos)
    #self.BackgroundStyle = wx.BG_STYLE_CUSTOM # Avoids flicker
    self.Bind(wx.EVT_ERASE_BACKGROUND, lambda evt: None)
    self.Bind(wx.EVT_WINDOW_CREATE,
              lambda evt: self.SetTransparent(FIRST_OPACITY)
             ) # Needed to at least have transparency on wxGTK
    self._paint_width, self._paint_height = 0, 0 # Ensure update_sizes at
                                                 # first on_paint
    self.ClientSize = size
    self.opacity = opacity
    self.Bind(wx.EVT_PAINT, self.on_paint)

  @property
  def opacity(self):
    return self._opacity

  @opacity.setter
  def opacity(self, value):
    self._opacity = value
    self.SetTransparent(self.opacity)

  def on_paint(self, evt):
    if self.ClientSize != (self._paint_width, self._paint_height):
      self._update_sizes()
    dc = wx.AutoBufferedPaintDCFactory(self)
    gc = wx.GraphicsContext.Create(dc) # Anti-aliasing
    self._draw(dc, gc)

  def _update_sizes(self):
    self._paint_width, self._paint_height = self.ClientSize
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

  def _draw(self, dc, gc):
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


class DoseGraphicalSemaphore(DoseGraphicalBaseFrame):
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
  def __init__(self, parent, config, leds=FIRST_LEDS):
    self._config = config
    pos = config.get_option("semaphore_position")
    size = config.get_option("semaphore_size")
    opacity = config.get_option("semaphore_opacity")
    flip = config.get_option("semaphore_flipped")
    super(DoseGraphicalSemaphore, self).__init__(parent,
                                                 pos=pos, size=size,
                                                 opacity=opacity)
    self._flip = flip
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

  def opacity(self, value):
    super(DoseGraphicalSemaphore, self).opacity(value)
    self._config.set_option("semaphore_opacity", value)

  @property
  def flip(self):
    return self._flip

  @flip.setter
  def flip(self, value):
    if self._flip != value:
      self._flip = value
      self._config.set_option("semaphore_flipped", value)
      self.Refresh()

  def _draw(self, dc, gc):
    super(DoseGraphicalSemaphore, self)._draw(dc, gc)

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


class DoseInteractiveBaseFrame(DoseGraphicalBaseFrame):
  """
  Just a DoseGraphicalBaseFrame, but now responsive to left click
  """
  def __init__(self, parent, config):
    super(DoseInteractiveBaseFrame, self).__init__(parent, config)
    self._config = config
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
      self._click_frame_x, self._click_frame_y = self.Position
      self._click_frame_width, self._click_frame_height = self.ClientSize
      self._click_opacity = self.opacity

      # Avoids refresh when there's no move (stores last mouse state)
      self._last_ms = ms.x, ms.y

      # Quadrant at click (need to know how to resize)
      width, height = self.ClientSize
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
          new_size = new_w, new_h
          self.ClientSize = new_size
          self.on_new_size(new_size)
          self.SendSizeEvent() # Needed for wxGTK

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
        self.on_new_pos(new_pos)
        self.Position = new_pos
        self.Refresh()

      # Since left button is kept down, there should be another one shot
      # timer event again, without creating many timers like wx.CallLater
      self._timer.Start(MOUSE_TIMER_WATCH, True)

    def on_new_size(self, new_size):
      pass

    def on_new_pos(self, new_pos):
      pass


class DoseInteractiveSemaphore(DoseInteractiveBaseFrame, 
                               DoseGraphicalSemaphore):
  """
  Just a DojoGraphicalSemaphore, but now responsive to left click
  """
  def __init__(self, parent, config):
    super(DoseInteractiveSemaphore, self).__init__(parent, config)
    self._config = config

  def on_new_size(self, new_size):
    self._config.set_option("semaphore_size", new_size)

  def on_new_pos(self, new_pos):
    self._config.set_option("semaphore_position", new_pos)


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
                         ("Skip pattern...", hc.on_skip_pattern),
                        ])
    menu_items.extend([(None, None),
                       ("Close\tAlt+F4", hc.on_close),
                       (None, None),
                       ("Help and about...", hc.on_help_and_about),
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
  def __init__(self, printer=print):
    self.directory = os.path.curdir # Default directory
    self.call_string = ""
    self.skip_pattern = FILENAME_PATTERN_TO_IGNORE
    self._watching = False
    self.printer = printer

  @property
  def watching(self):
    return self._watching

  def has_call_string(self):
    return len(self.call_string.strip()) > 0

  def start(self, func_err, func_wait, func_ok, func_stop):
    """
    Starts watching. The three args are loggers or aesthetical functions to be
    called when the state changes (e.g., there's something being handled).
    """
    assert not self.watching

    class DoseSomethingChangedEventHandler(FileSystemEventHandler):

      def on_any_event(handler, evt=None):
        """
        Handle the event "directory has changed its contents somehow"
        Using "handler" instead of "self" for class instance, so "self" is a
        DoseWatcher instance, and self.printer may change while watching.
        That's also useful to store "self.last_mtime", since there's a new
        handler instance for each event.
        """
        # ---------------------------------------
        # Event filters (to avoid unuseful calls)
        # ---------------------------------------
        event_time = time.time()
        if evt is not None: # If not the first event

          # Neglect calls from compiled or otherwise ignorable files
          path = os.path.relpath(evt.src_path, self.directory)
          for pattern in self.skip_pattern.split(";"):
            if fnmatch(path, pattern.strip()):
              return

          # Logs
          if not self.logged_blankline:
            self.logged_blankline = True
            self.printer() # Skip one line
          self.printer(" ".join(["***",
            "Directory" if evt.is_directory else "File",
            evt.event_type + ":",
            path.decode("utf-8"),
            "***"
          ]))

          # Neglect calls that happens too fast (bounce) with a time lag
          time.sleep(TIME_BEFORE_CALL)
          if event_time < self.last_etime:
            return

        # First call logging
        else:
          self.printer() # Skip one line
          self.logged_blankline = True
          self.printer("*** First call ***")

        self.last_etime = event_time

        # ------------------
        # Subprocess calling
        # ------------------
        # State changed: "waiting" for a subprocess (still not called)
        func_wait()

        # Logging
        timestamp = datetime.now()
        self.printer("=" * TERMINAL_WIDTH)
        self.printer("Dose call at {0}".format(timestamp)
                                       .center(TERMINAL_WIDTH)
                    )

        # Subprocess calling
        try:
          process = Popen(self.call_string,
                          stdout=PIPE, stderr=PIPE, shell=True)
          out, err = process.communicate()
          returned_value = process.wait()
        except Exception, e:
          self.stop() # Watching no more
          self.printer("Error while calling".center(TERMINAL_WIDTH))
          self.printer("=" * TERMINAL_WIDTH)
          func_stop(e)
          return

        # Get the data from the process
        for data, name in [(out, "Output data"), (err, "Error data")]:
          if len(data) > 0:
            self.printer(name.center(TERMINAL_WIDTH))
            self.printer("=" * TERMINAL_WIDTH)
            self.printer(data)
            self.printer("=" * TERMINAL_WIDTH)

        # Informative message when there's no output data
        if (len(out) == 0) and (len(err) == 0):
          self.printer("No data".center(TERMINAL_WIDTH))
          self.printer("=" * TERMINAL_WIDTH)

        # Updates the state
        self.logged_blankline = False # Now it'll skip a line next time
        if returned_value == 0:
          func_ok()
        else:
          func_err()

    # Starts the watchdog observer
    self._observer = Observer()
    def p(x): print(x, type(x))
    self._observer.schedule(DoseSomethingChangedEventHandler(),
                            path=self.directory.encode("utf-8"),
                            recursive=True)
    DoseSomethingChangedEventHandler().on_any_event()
    self._observer.start()
    self._watching = True

  def stop(self):
    if self.watching:
      self._observer.stop()
      self._observer.join()
      self._watching = False


class DoseConfig:
  """
  Handle load and storage of configuration options.

  When dose starts, try to load configurations from
  a file named ".dose.conf" in the following 
  locations:

  1) Working directory (TODO!)
  2) User home

  If none of these files are present, dose 
  fallback to default values.
  """

  def get_option(self, key):
    return self._config.get(key, CONFIG_DEFAULT_OPTIONS[key])

  def set_option(self, key, value):
    self._config[key] = value

  def _user_home_config_file_path(self):
    user_home = os.path.expanduser("~")
    path = os.path.join(user_home, CONFIG_FILE_NAME)
    return path

  def store_options(self):
    """
    Store options in the user's home, only if 
    dose has not been launched with working 
    directory configs (TODO!).
    """
    path = self._user_home_config_file_path()
    config_file = open(path, "w")
    json.dump(self._config, config_file, indent=4, separators=(',',': '))

  def __init__(self):
    path = self._user_home_config_file_path()
    if os.path.exists(path):
      config_file = open(path, "r")
      self._config = json.load(config_file)
    else:
      self._config = CONFIG_DEFAULT_OPTIONS


class DoseGraphicalTimer(DoseGraphicalBaseFrame):
  """
  """
  def __init__(self, parent, config):
    self._config = config
    pos = config.get_option("timer_position")
    size = config.get_option("timer_size")
    opacity = config.get_option("timer_opacity")
    super(DoseGraphicalTimer, self).__init__(parent, 
                                                 pos=pos, size=size,
                                                 opacity=opacity)

    self.sizer = wx.FlexGridSizer(3)
    
    self.sizer.AddGrowableCol(1)
    self.sizer.AddGrowableRow(2)

    self.SetSizer(self.sizer)

    back_color = int_to_color(BACKGROUND_COLOR)
    fore_color = int_to_color(FOREGROUND_COLOR)

    self._text_control = wx.lib.masked.TextCtrl(self, mask="##:##",
                                                      style=wx.NO_BORDER,
                                                      emptyBackgroundColour=back_color,
                                                      validBackgroundColour=back_color,
                                                      foregroundColour=fore_color)
    self._text_control.SetBackgroundColour(back_color)
    self._text_control.SetForegroundColour(fore_color)

    self._text_label = wx.lib.masked.TextCtrl(self, mask="##:##",
                                                    style=wx.NO_BORDER,
                                                    emptyBackgroundColour=back_color,
                                                    validBackgroundColour=back_color,
                                                    foregroundColour=fore_color)
    self._text_label.SetBackgroundColour(back_color)
    self._text_label.SetForegroundColour(fore_color)
    self._text_label.SetEditable(False)
    self._text_label.Hide()
    
    self.sizer.AddSpacer(20)
    self.sizer.AddSpacer(20)
    self.sizer.AddSpacer(20)

    self.sizer.AddSpacer(20)
    self.sizer.Add(self._text_control)
    self.sizer.AddSpacer(20)

    self.sizer.AddSpacer(20)
    self.sizer.AddSpacer(20)
    self.sizer.AddSpacer(20)
    
    self.update_text_size()

  def opacity(self, value):
    super(DoseGraphicalTimer, self).opacity(value)
    self._config.set_option("timer_opacity", value)

  def _draw(self, dc, gc):
    super(DoseGraphicalTimer, self)._draw(dc, gc)
    self.update_text_size()

  def update_text_size(self):
    
    client_size = self.ClientSize
    client_width, client_height = client_size

    character_count = 5 # 00:00

    text_margin = 40
    max_width = client_width - text_margin
    char_width = max_width / character_count
    max_height = client_height - text_margin

    text_font = wx.FontFromPixelSize((char_width, max_height),
                         family = wx.FONTFAMILY_MODERN,
                         style = wx.FONTSTYLE_NORMAL,
                         weight = wx.FONTWEIGHT_NORMAL)

    self._text_control.SetFont(text_font)
    self._text_label.SetFont(text_font)
    self._text_control.SetSize((max_width, max_height))
    self._text_label.SetSize((max_width, max_height))


class DoseInteractiveTimer(DoseInteractiveBaseFrame, 
                           DoseGraphicalTimer):
  """
  Just a DoseGraphicalTimer, but now responsive to left click
  """
  def __init__(self, parent, config):
    super(DoseInteractiveTimer, self).__init__(parent, config)
    self._config = config
    self._text_control.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
    self._text_control.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick_control)
    self._text_control.Bind(wx.EVT_KEY_DOWN, self.on_key_down_control)
    self._text_label.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
    self._text_label.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick_label)

  def on_new_size(self, new_size):
    self._config.set_option("timer_size", new_size)

  def on_new_pos(self, new_pos):
    self._config.set_option("timer_position", new_pos)

  def on_left_dclick_control(self, evt):
    self._text_control.SetFocus()

  def on_key_down_control(self, evt):
    key_code = evt.KeyCode
    if key_code in {wx.WXK_ESCAPE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER}:
      self._text_label.SetValue(self._text_control.GetValue())
      self._text_control.Hide()
      self._text_label.Show()
      self.sizer.Replace(self._text_control, self._text_label)
      self.sizer.Layout()
    else:
      evt.Skip()

  def on_left_dclick_label(self, evt):
    self._text_label.Hide()
    self._text_control.Show()
    self.sizer.Replace(self._text_label, self._text_control)
    self.sizer.Layout()
    self._text_control.SetFocus()
    
class DoseTimerWindow(DoseInteractiveTimer):

  def __init__(self, parent, config):
    super(DoseTimerWindow, self).__init__(parent, config)


class DoseMainWindow(DoseInteractiveSemaphore, DoseWatcher):

  def __init__(self, parent, config):
    DoseInteractiveSemaphore.__init__(self, parent, config)
    DoseWatcher.__init__(self)
    self._config = config
    self.SetTitle("Disabled - dose") # Seen by the window manager
    self.popmenu = {k:DosePopupMenu(self, k) for k in (True, False)}

    self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
    self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
    self.Bind(wx.EVT_CLOSE, self.on_close)

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
      self.start(func_err=self.on_red,
                 func_wait=self.on_yellow,
                 func_ok=self.on_green,
                 func_stop=self.on_stop)

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
    self._config.store_options()

  def on_help_and_about(self, evt):
    abinfo = wx.AboutDialogInfo()
    abinfo.Artists = abinfo.Developers = [" ".join([__author__, "-",
                                                    __author_email__])
                                         ]
    abinfo.Copyright = "Copyright (C) 2012 " + __author__
    abinfo.Description = (
      "Automated semaphore GUI showing the state in test driven development."
      "\n\n"
      "Dose watches one directory for any kind of change\n"
      "new file, file modified, file removed, subdirectory renamed,\n"
      "etc., including its subdirectories, by using the Python\n"
      "watchdog package. For example, changes on files ending on\n"
      "'.pyc' and '.pyo' are neglect by default, as well as git\n"
      "internals, but these skip patterns are *customizable*."
      "\n\n"
      "A *customized* subprocess is called, all its output/error\n"
      "data is left on the shell used to call Dose, and its return\n"
      "value is stored. If the value is zero, the semaphore turns\n"
      "green, else it it turns red. It stays yellow while waiting\n"
      "the subprocess to finish."
      "\n\n"
      "The default directory path to watch is the one used to call\n"
      "Dose. There's no default calling string, but 'nosetests' and\n"
      "'py.test' would be hints for Python developers. It should\n"
      "work even with other languages TDD tools. To be fast, just\n"
      "open Dose and double click on it, there's no need to lose\n"
      "time with settings."
      "\n\n"
      "The GUI toolkit used in this project is wxPython. You can\n"
      "move the semaphore by dragging it around. Doing so with\n"
      "Ctrl pressed would resize it. With Shift you change its\n"
      "transparency (not available on Linux, for now). The\n"
      "semaphore window always stays on top. A right click would\n"
      "show all options available."
    )
    abinfo.Version = __version__
    abinfo.Name = "Dose"
    abinfo.License = (
      "This program is free software: you can redistribute it and/or modify\n"
      "it under the terms of the GNU General Public License as published by\n"
      "the Free Software Foundation, version 3 of the License."
      "\n\n"
      "This program is distributed in the hope that it will be useful,\n"
      "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
      "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\n"
      "GNU General Public License for more details."
      "\n\n"
      "You should have received a copy of the GNU General Public License\n"
      "along with this program. If not, see <http://www.gnu.org/licenses/>."
    )
    abinfo.WebSite = __url__
    wx.AboutBox(abinfo)


class DoseApp(wx.App):

  def OnInit(self):
    config = DoseConfig()
    self.SetAppName("dose")
    wnd = DoseMainWindow(None, config)
    wnd.Show()
    timer_wnd = DoseTimerWindow(wnd, config)
    timer_wnd.Show()
    self.SetTopWindow(wnd)
    return True # Needed by wxPython

if __name__ == "__main__":
  import sys
  app = DoseApp(False)
  if len(sys.argv) > 1:
    wnd = app.GetTopWindow()
    wnd.call_string = " ".join(sys.argv[1:])
    wnd.on_start()
  app.MainLoop()
