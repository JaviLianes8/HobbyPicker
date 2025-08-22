import tkinter as tk
from tkinter import ttk
from presentation.widgets.styles import get_color, add_button_hover
from presentation.widgets.toggle_switch import ToggleSwitch
from .suggest_logic import SuggestLogic


def create_suggest_tab(root, notebook, tr, include_games_var, games_only_var,
                       current_items_weights, is_steam_game_label, show_game_popup,
                       build_activity_caches):
    frame = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame, text=tr("tab_today"))
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.rowconfigure(0, weight=1)

    content = ttk.Frame(frame, style="Surface.TFrame")
    content.grid(row=0, column=0, sticky="nsew")
    separator = ttk.Separator(frame, orient="vertical")
    separator.grid(row=0, column=1, sticky="ns", padx=5)
    table_frame = ttk.Frame(frame, style="Surface.TFrame", width=740)
    table_frame.grid(row=0, column=2, sticky="nsew", padx=10)
    table_frame.grid_propagate(False)
    table_frame.rowconfigure(1, weight=1)
    table_frame.columnconfigure(0, weight=1)

    filter_row = ttk.Frame(table_frame, style="Surface.TFrame")
    filter_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
    filter_row.columnconfigure(1, weight=1)
    filter_label = ttk.Label(filter_row, text=tr("filter"), style="Surface.TLabel",
                             foreground=get_color("contrast"))
    filter_label.grid(row=0, column=0, padx=(0, 5))
    filter_var = tk.StringVar()
    ttk.Entry(filter_row, textvariable=filter_var).grid(row=0, column=1, sticky="ew")

    prob_table = ttk.Treeview(
        table_frame,
        columns=("activity", "percent", "info", "steam", "delete"),
        show="headings",
        style="Probability.Treeview",
    )
    for col, text, width in (
        ("activity", tr("col_activity"), 480),
        ("percent", tr("col_percent"), 120),
        ("info", "ⓘ", 40),
        ("steam", "🎮", 40),
        ("delete", "🗑", 40),
    ):
        prob_table.heading(col, text=text, anchor="w" if col == "activity" else "center")
        prob_table.column(col, width=width, anchor="w" if col == "activity" else "center")
    v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=prob_table.yview)
    prob_table.configure(yscrollcommand=v_scroll.set)
    prob_table.grid(row=1, column=0, sticky="nsew")
    v_scroll.grid(row=1, column=1, sticky="ns")

    toggle_container = ttk.Frame(content, style="Surface.TFrame")
    toggle_container.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
    include_row = ttk.Frame(toggle_container, style="Surface.TFrame")
    include_row.pack(anchor="e", pady=2)
    include_label = ttk.Label(include_row, text=tr("include_games"),
                              style="Surface.TLabel", foreground=get_color("contrast"))
    include_label.pack(side="left", padx=(0, 5))
    include_switch = ToggleSwitch(include_row, variable=include_games_var)
    include_switch.pack(side="left")

    only_row = ttk.Frame(toggle_container, style="Surface.TFrame")
    only_row.pack(anchor="e", pady=2)
    only_label = ttk.Label(only_row, text=tr("games_only"),
                           style="Surface.TLabel", foreground=get_color("contrast"))
    only_label.pack(side="left", padx=(0, 5))
    games_only_switch = ToggleSwitch(only_row, variable=games_only_var)
    games_only_switch.pack(side="left")

    suggestion_label = ttk.Label(
        content,
        text=tr("prompt"),
        font=("Segoe UI", 28, "bold"),
        wraplength=500,
        justify="center",
        style="Surface.TLabel",
    )
    suggestion_label.pack(pady=20, expand=True)

    animation_canvas = tk.Canvas(
        content,
        width=1620,
        height=220,
        bg=get_color("surface"),
        highlightthickness=0,
    )

    button_container = ttk.Frame(content, style="Surface.TFrame")
    button_container.pack(side="bottom", fill="x", pady=20)
    suggest_btn = ttk.Button(
        button_container,
        text=tr("suggest_button"),
        style="Big.TButton",
        width=20,
    )
    suggest_btn.pack(pady=10)
    add_button_hover(suggest_btn)

    widgets = {
        'frame': frame,
        'prob_table': prob_table,
        'filter_var': filter_var,
        'filter_label': filter_label,
        'toggle_container': toggle_container,
        'include_label': include_label,
        'games_only_label': only_label,
        'include_switch': include_switch,
        'games_only_switch': games_only_switch,
        'suggestion_label': suggestion_label,
        'animation_canvas': animation_canvas,
        'button_container': button_container,
        'suggest_btn': suggest_btn,
        'separator': separator,
        'table_frame': table_frame,
        'build_activity_caches': build_activity_caches,
    }

    logic = SuggestLogic(
        root,
        tr,
        include_games_var,
        games_only_var,
        current_items_weights,
        is_steam_game_label,
        show_game_popup,
        widgets,
    )
    return logic
