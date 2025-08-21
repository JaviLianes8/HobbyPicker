import tkinter as tk
from tkinter import ttk

from .styles import get_color


class ToggleSwitch(ttk.Frame):
    """A small on/off switch drawn on a canvas."""

    def __init__(self, master=None, variable=None, command=None, **kwargs):
        super().__init__(master, style="Surface.TFrame", **kwargs)
        self.variable = variable or tk.BooleanVar(value=False)
        self.command = command
        self._disabled = False
        self.canvas = tk.Canvas(
            self, width=40, height=24, highlightthickness=0, bg=get_color("surface")
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *_: self.redraw())
        self.redraw()

    def _toggle(self, _event=None):
        if self._disabled:
            return
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def state(self, states=None):  # minimal ttk-like interface
        if states is None:
            return ["disabled"] if self._disabled else ["!disabled"]
        if "disabled" in states:
            self._disabled = True
        if "!disabled" in states:
            self._disabled = False
        self.redraw()

    def redraw(self):
        c = self.canvas
        c.delete("all")
        c.configure(bg=get_color("surface"))
        track = get_color("light")
        if self.variable.get():
            track = get_color("primary")
        if self._disabled:
            track = get_color("light")
        # draw track (rounded rectangle)
        c.create_rectangle(12, 6, 28, 18, fill=track, outline=track)
        c.create_oval(4, 6, 20, 22, fill=track, outline=track)
        c.create_oval(20, 6, 36, 22, fill=track, outline=track)
        # knob
        knob_color = get_color("surface") if not self._disabled else get_color("subtle")
        knob_x = 20 if self.variable.get() else 4
        c.create_oval(knob_x, 6, knob_x + 16, 22, fill=knob_color, outline=knob_color)
