"""UI construction for HobbyPicker tabs."""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk

from domain import use_cases
from presentation.widgets.simple_entry_dialog import SimpleEntryDialog
from ..translations import tr
from .animations import launch_confetti


def build_tabs(root: tk.Tk, lang_var: tk.StringVar):
    """Build main notebook and return a refresh function."""
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    frame_today = ttk.Frame(notebook)
    frame_config = ttk.Frame(notebook)
    notebook.add(frame_today, text=tr("tab_today", lang_var.get()))
    notebook.add(frame_config, text=tr("tab_config", lang_var.get()))

    # --- Suggestion tab ---
    suggestion_lbl = ttk.Label(
        frame_today, text=tr("prompt", lang_var.get()), font=("Segoe UI", 16)
    )
    suggestion_lbl.pack(pady=20)

    # Canvas used to render celebration confetti after accepting a suggestion.
    confetti_canvas = tk.Canvas(frame_today, highlightthickness=0, bg="")
    confetti_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
    confetti_canvas.lower()  # Hidden until needed

    current = {"id": None, "is_sub": False, "label": None}

    def refresh_probabilities() -> None:
        table.delete(*table.get_children())
        for label, prob in use_cases.get_activity_probabilities():
            table.insert("", "end", values=(label, f"{prob*100:.1f}"))
        notebook.tab(0, text=tr("tab_today", lang_var.get()))
        notebook.tab(1, text=tr("tab_config", lang_var.get()))
        suggestion_lbl.config(text=tr("prompt", lang_var.get()))
        suggest_btn.config(text=tr("suggest_button", lang_var.get()))
        accept_btn.config(text=tr("accept_button", lang_var.get()))
        add_btn.config(text=tr("add_hobby", lang_var.get()))
        del_btn.config(text=tr("delete", lang_var.get()))
        table.heading("activity", text=tr("col_activity", lang_var.get()))
        table.heading("percent", text=tr("col_percent", lang_var.get()))

    def suggest() -> None:
        items, weights = use_cases.build_weighted_items()
        if not items:
            suggestion_lbl.config(text=tr("no_hobbies", lang_var.get()))
            accept_btn.state(["disabled"])
            return
        item_id, label, is_sub = random.choices(items, weights=weights, k=1)[0]
        current.update(id=item_id, is_sub=is_sub, label=label)
        suggestion_lbl.config(
            text=tr("what_about", lang_var.get()).format(label)
        )
        accept_btn.state(["!disabled"])

    def accept() -> None:
        if current["id"] is None:
            return
        use_cases.mark_activity_as_done(current["id"], current["is_sub"])
        suggestion_lbl.config(text=tr("like_overlay", lang_var.get()))
        accept_btn.state(["disabled"])
        current.update(id=None, label=None, is_sub=False)
        refresh_probabilities()

        # Celebrate the accepted suggestion with a brief confetti animation.
        confetti_canvas.lift()

        def _animate():
            confetti_canvas.delete("all")
            w = confetti_canvas.winfo_width()
            h = confetti_canvas.winfo_height()
            confetti_canvas.create_text(
                w / 2,
                h / 2,
                text=tr("like_overlay", lang_var.get()),
                font=("Segoe UI", 24, "bold"),
                fill="white",
                tag="label",
            )
            launch_confetti(confetti_canvas)
            confetti_canvas.after(1500, confetti_canvas.lower)

        # Defer drawing until geometry is computed
        confetti_canvas.after(0, _animate)

    suggest_btn = ttk.Button(
        frame_today, text=tr("suggest_button", lang_var.get()), command=suggest
    )
    suggest_btn.pack(pady=(0, 10))

    accept_btn = ttk.Button(
        frame_today, text=tr("accept_button", lang_var.get()), command=accept
    )
    accept_btn.pack()
    accept_btn.state(["disabled"])

    # --- Config tab ---
    table = ttk.Treeview(
        frame_config,
        columns=("activity", "percent"),
        show="headings",
        height=12,
    )
    table.heading("activity", text=tr("col_activity", lang_var.get()))
    table.heading("percent", text=tr("col_percent", lang_var.get()))
    table.column("activity", width=240)
    table.column("percent", width=80, anchor="e")
    table.pack(fill="both", expand=True, padx=10, pady=10)

    def add_hobby() -> None:
        dlg = SimpleEntryDialog(
            root,
            tr("add_hobby_window_title", lang_var.get()),
            tr("hobby_title_label", lang_var.get()),
        )
        if dlg.result:
            use_cases.create_hobby(dlg.result)
            refresh_probabilities()

    def delete_selected() -> None:
        item = table.selection()
        if not item:
            return
        label = table.item(item[0], "values")[0]
        if not messagebox.askyesno(
            tr("deleted", lang_var.get()),
            tr("delete_hobby_confirm", lang_var.get()).format(name=label),
        ):
            return
        all_hobbies = use_cases.get_all_hobbies()
        hobby_id = all_hobbies[table.index(item[0])][0]
        use_cases.delete_hobby(hobby_id)
        refresh_probabilities()

    add_btn = ttk.Button(
        frame_config, text=tr("add_hobby", lang_var.get()), command=add_hobby
    )
    add_btn.pack(pady=(0, 5))

    del_btn = ttk.Button(
        frame_config, text=tr("delete", lang_var.get()), command=delete_selected
    )
    del_btn.pack(pady=(0, 10))

    refresh_probabilities()
    return refresh_probabilities

