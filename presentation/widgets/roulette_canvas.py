import tkinter as tk
from tkinter import ttk, font
import math


class RouletteCanvas(tk.Canvas):
    """Canvas that draws a roulette-style pie chart."""

    def __init__(self, master, width=300, height=300, **kwargs):
        # Match the surrounding surface color to avoid a gray square background
        style = ttk.Style(master)
        default_bg = style.lookup("Surface.TFrame", "background") or "#FFFFFF"
        bg = kwargs.pop("bg", default_bg)
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0,
            bg=bg,
            **kwargs,
        )
        self.center = (width / 2, height / 2)
        self.radius = min(width, height) / 2 - 20
        self._arcs = {}
        self._order = []
        self._names = {}

    def draw(self, items):
        """Draw roulette slices.

        Args:
            items: Iterable of dicts with keys 'id', 'name', 'weight', 'percentage'.
        """
        self.delete("all")
        self._arcs.clear()
        self._order.clear()
        self._names.clear()
        if not items:
            return
        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        self.center = (w / 2, h / 2)
        self.radius = min(w, h) / 2 - 20

        total = sum(item['weight'] for item in items)
        start = 0
        colors = [
            "#264653", "#2a9d8f", "#e9c46a", "#f4a261",
            "#e76f51", "#6a4c93", "#8ac926", "#1982c4",
        ]
        base_font = font.Font(family="Helvetica", size=14, weight="bold")
        for idx, item in enumerate(items):
            extent = item['weight'] / total * 360
            color = colors[idx % len(colors)]
            arc = self.create_arc(
                10,
                10,
                self.center[0] * 2 - 10,
                self.center[1] * 2 - 10,
                start=start,
                extent=extent,
                fill=color,
                outline="white",
            )
            self._arcs[item['id']] = arc
            self._order.append(item['id'])
            name = item['name']
            text_font = font.Font(font=base_font)
            effective_radius = self.radius * 0.7
            max_text_width = max(
                20, 2 * effective_radius * math.sin(math.radians(extent / 2)) * 0.9
            )
            while text_font.cget("size") > 8 and text_font.measure(name) > max_text_width:
                text_font.configure(size=text_font.cget("size") - 1)
            self._names[item['id']] = name
            mid = start + extent / 2
            x = self.center[0] + effective_radius * math.cos(math.radians(mid))
            y = self.center[1] - effective_radius * math.sin(math.radians(mid))
            self.create_text(
                x,
                y,
                text=f"{name}\n{item['percentage']:.1f}%",
                fill="white",
                font=text_font,
                justify="center",
                width=max_text_width,
            )
            start += extent

    def highlight(self, activity_id):
        """Emphasize a slice for the given activity id."""
        for arc in self._arcs.values():
            self.itemconfig(arc, width=2, outline="white")
        arc_id = self._arcs.get(activity_id)
        if arc_id:
            self.itemconfig(arc_id, width=6, outline="yellow")

    def spin_to(
        self,
        activity_id,
        cycles=3,
        base_delay=20,
        extra_delay=300,
        on_step=None,
        on_complete=None,
    ):
        """Animate a spin highlighting slices with easing until reaching the target.

        Args:
            activity_id: Identifier of the slice to stop on.
            cycles: How many full cycles to make before stopping.
            base_delay: Minimum delay between highlights in ms.
            extra_delay: Extra delay added near the end to simulate deceleration.
            on_step: Optional callback receiving ``(id, name)`` per highlight.
            on_complete: Callback executed once the animation finishes.
        """
        if activity_id not in self._arcs:
            return

        rev_order = list(reversed(self._order))
        path = rev_order * cycles
        target_index = rev_order.index(activity_id)
        path += rev_order[: target_index + 1]
        total_steps = len(path)
        total_duration = 5000  # ms
        avg_delay = base_delay + extra_delay / 3
        expected = total_steps * avg_delay
        scale = total_duration / expected
        base_delay *= scale
        extra_delay *= scale

        def step(i=0):
            current_id = path[i]
            self.highlight(current_id)
            if on_step:
                on_step(current_id, self._names.get(current_id, ""))
            if i + 1 < total_steps:
                progress = i / total_steps
                delay = base_delay + (progress ** 2) * extra_delay
                self.after(int(delay), lambda: step(i + 1))
            elif on_complete:
                on_complete()

        step()
