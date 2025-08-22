import random
import tkinter as tk
from tkinter import ttk
from presentation.widgets.styles import get_color, add_button_hover
from domain import use_cases


class SuggestLogic:
    def __init__(self, root, tr, include_games_var, games_only_var,
                 current_items_weights, is_steam_game_label, show_game_popup,
                 widgets):
        self.root = root
        self.tr = tr
        self.include_games_var = include_games_var
        self.games_only_var = games_only_var
        self.current_items_weights = current_items_weights
        self.is_steam_game_label = is_steam_game_label
        self.show_game_popup = show_game_popup
        self.w = widgets
        self.current = {"id": None, "name": None, "is_sub": False}
        self.overlay_buttons = []
        self.final_canvas = None
        self.final_timeout = None
        self._setup()

    def _setup(self):
        self.refresh_probabilities()
        self.w['filter_var'].trace_add("write", lambda *_: self.refresh_probabilities())
        self.w['suggest_btn'].configure(command=self.suggest)
        self.w['include_switch'].configure(command=self.on_toggle_update)
        self.w['games_only_switch'].configure(command=self.on_toggle_update)
        self.on_toggle_update()

    def refresh_probabilities(self):
        table = self.w['prob_table']
        for row in table.get_children():
            table.delete(row)
        table.tag_configure("even", background=get_color("surface"), foreground=get_color("text"))
        table.tag_configure("odd", background=get_color("light"), foreground=get_color("text"))
        items, weights = self.current_items_weights()
        if not items:
            return
        total = sum(weights)
        ftxt = self.w['filter_var'].get().lower()
        for i, ((item_id, name, is_sub), weight) in enumerate(zip(items, weights)):
            if ftxt and ftxt not in name.lower():
                continue
            tag = "even" if i % 2 == 0 else "odd"
            iid = f"{'s' if is_sub else 'h'}{item_id}"
            icon = "🎮" if is_sub and self.is_steam_game_label(name) else ""
            table.insert("", "end", iid=iid,
                         values=(name, f"{weight*100/total:.1f}%", "ⓘ", icon, "🗑"),
                         tags=(tag,))

    def on_toggle_update(self):
        sw = self.w['games_only_switch']
        if self.games_only_var.get():
            self.include_games_var.set(True)
        if not self.include_games_var.get():
            self.games_only_var.set(False)
            sw.state(["disabled"])
        else:
            sw.state(["!disabled"])
        self.refresh_probabilities()

    def revert_to_idle(self):
        if self.final_canvas is not None:
            self.final_canvas.destroy(); self.final_canvas = None
            self.w['separator'].grid(); self.w['table_frame'].grid()
            self.w['button_container'].pack(side="bottom", fill="x", pady=20)
        self.overlay_buttons.clear()
        self.w['suggest_btn'].state(["!disabled"])
        self.w['suggestion_label'].config(text=self.tr("prompt"))
        self.w['suggestion_label'].pack(pady=20, expand=True)
        self.w['toggle_container'].place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
        self.final_timeout = None

    def make_overlay_buttons(self, parent):
        self.overlay_buttons.clear()
        overlay = ttk.Frame(parent, style="Surface.TFrame")
        b1 = ttk.Button(overlay, text=self.tr("another_button"),
                        command=self.suggest, style="Big.TButton", width=20)
        b1.pack(side="left", padx=8, pady=10)
        add_button_hover(b1)
        b1.state(["disabled"])
        self.overlay_buttons.append((b1, "another_button"))
        b2 = ttk.Button(overlay, text=self.tr("like_overlay"),
                        command=self.accept, style="Big.TButton", width=20)
        b2.pack(side="left", padx=8, pady=10)
        add_button_hover(b2)
        self.overlay_buttons.append((b2, "like_overlay"))
        return overlay

    def show_final_activity(self, text):
        if self.final_timeout is not None:
            self.root.after_cancel(self.final_timeout); self.final_timeout = None
        if self.final_canvas is not None:
            self.final_canvas.destroy()
        fc = tk.Canvas(self.w['frame'], bg=get_color("surface"), highlightthickness=0)
        fc.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.final_canvas = fc
        self.w['separator'].grid_remove(); self.w['table_frame'].grid_remove()
        self.w['button_container'].pack_forget()
        cx, cy = fc.winfo_width() / 2, fc.winfo_height() / 2
        mw = fc.winfo_width() * 0.9
        text_item = fc.create_text(cx, cy, text=text, width=mw,
                                   fill=get_color("text"), font=("Segoe UI", 28, "bold"),
                                   tags=("final_text",), justify="center", anchor="center")
        overlay = self.make_overlay_buttons(fc)
        btn_win = fc.create_window(cx, fc.winfo_height() - 20, window=overlay, anchor="s")

        def on_resize(_=None):
            nonlocal mw
            mw = fc.winfo_width() * 0.9
            fc.itemconfigure(text_item, width=mw)
            fc.coords(text_item, fc.winfo_width()/2, fc.winfo_height()/2)
            fc.coords(btn_win, fc.winfo_width()/2, fc.winfo_height()-20)
        fc.bind("<Configure>", on_resize)
        self.final_timeout = self.root.after(8000, self.revert_to_idle)

    def suggest(self):
        for b, _ in self.overlay_buttons: b.state(["disabled"])
        self.w['suggest_btn'].state(["disabled"])
        self.w['toggle_container'].place_forget()
        if self.final_timeout is not None:
            self.root.after_cancel(self.final_timeout); self.final_timeout=None
        if self.final_canvas is not None:
            self.final_canvas.destroy(); self.final_canvas=None
            self.w['separator'].grid(); self.w['table_frame'].grid()
            self.w['button_container'].pack(side="bottom", fill="x", pady=20)
        items, weights = self.current_items_weights()
        result = random.choices(items, weights=weights, k=1)[0] if items else None
        if not result:
            self.w['suggestion_label'].config(text=self.tr("no_hobbies"))
            self.w['suggestion_label'].pack(pady=20, expand=True)
            self.w['toggle_container'].place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
            return
        fid, ftxt, is_sub = result
        self.current.update({"id": fid, "name": ftxt, "is_sub": is_sub})
        opts = [random.choices(items, weights=weights, k=1)[0][1] for _ in range(20)] + [ftxt, ""]
        c = self.w['animation_canvas']; c.delete("all")
        bw, bh = 540, 180
        for i, text in enumerate(opts):
            x = i * bw
            c.create_rectangle(x, 0, x + bw, bh, fill=get_color("light"), outline="", tags=("item",))
            c.create_text(x + bw / 2, bh / 2, text=text, width=bw - 20,
                          fill=get_color("text"), font=("Segoe UI", 32, "bold"), tags=("item",))
        c.create_rectangle(bw, 0, bw * 2, bh, outline=get_color("primary"), width=3)
        self.w['suggestion_label'].pack_forget(); c.pack(pady=20, before=self.w['button_container'])
        total = (len(opts) - 3) * bw

        def roll(step=0, speed=10):
            if step < total:
                c.move("item", -speed, 0); step += speed
                if step < total * 0.6: speed = min(speed + 2, 80)
                elif total - step < bw * 2: speed = max(speed - 3, 5)
                self.root.after(20, lambda: roll(step, speed))
            else:
                c.move("item", -(total - step), 0); c.after(200, finish)

        def finish():
            c.pack_forget()
            self.show_final_activity(self.tr("what_about").format(ftxt))
            for b, k in self.overlay_buttons:
                if k in ("like_overlay", "another_button"): b.state(["!disabled"])
        roll()

    def accept(self):
        if self.current["id"]:
            is_game = self.current["is_sub"] and self.current["name"] and self.is_steam_game_label(self.current["name"])
            game_name = self.current["name"].split(" + ", 1)[1] if is_game else ""
            use_cases.mark_activity_as_done(self.current["id"], self.current["is_sub"])
            self.w['build_activity_caches']()
            if is_game:
                self.show_game_popup(game_name)
            self.current.update({"id": None, "name": None, "is_sub": False})
            self.w['suggestion_label'].config(text=self.tr("prompt"))
            self.w['suggestion_label'].pack(pady=20, expand=True)
            self.w['toggle_container'].place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
            self.refresh_probabilities()
