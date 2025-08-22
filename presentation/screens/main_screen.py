import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial

from domain import use_cases
from presentation.widgets.styles import apply_style, get_color
from presentation.utils.window_utils import WindowUtils
from presentation.i18n import LANG_TEXT, get_system_language, STEAM_HOBBY_NAMES
from .steam_actions import import_steam_games, show_game_popup
from .suggest_tab import create_suggest_tab
from .config_tab import create_config_tab


def start_app() -> None:
    root = tk.Tk()
    root.state("zoomed")
    WindowUtils.center_window(root, 1240, 600)
    root.title("HobbyPicker")
    root.minsize(1240, 600)

    config_path = Path.home() / ".hobbypicker.json"

    def load_settings():
        data = {"language": "system", "theme": "system"}
        try:
            if config_path.exists():
                with config_path.open("r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                data.update({k: stored.get(k, v) for k, v in data.items()})
        except Exception:
            pass
        return data

    def save_settings():
        try:
            with config_path.open("w", encoding="utf-8") as fh:
                json.dump({"language": lang_var.get(), "theme": theme_var.get()}, fh)
        except Exception:
            pass

    settings = load_settings()
    lang_var = tk.StringVar(value=settings["language"])
    theme_var = tk.StringVar(value=settings["theme"])
    include_games_var = tk.BooleanVar(value=True)
    games_only_var = tk.BooleanVar(value=False)

    apply_style(root, theme_var.get())

    def get_effective_language() -> str:
        return lang_var.get() if lang_var.get() != "system" else get_system_language()

    def tr(key: str) -> str:
        return LANG_TEXT[get_effective_language()][key]

    def is_steam_game_label(label: str) -> bool:
        return any(label.startswith(name + " + ") for name in STEAM_HOBBY_NAMES)

    activity_lists = {}
    refresh_probabilities = lambda: None

    def build_activity_caches():
        from presentation.steam_utils import discover_steam_libraries, load_installed_games
        discover_steam_libraries.cache_clear()
        load_installed_games.cache_clear()
        discover_steam_libraries(); load_installed_games()
        def filter_no_games(item):
            _, label, is_sub, _ = item
            return not (is_sub and is_steam_game_label(label))
        activity_lists["all"] = use_cases.build_weighted_items()
        activity_lists["no_games"] = use_cases.build_weighted_items(filter_no_games)
        def filter_games(item):
            _, label, is_sub, _ = item
            return is_sub and is_steam_game_label(label)
        activity_lists["games"] = use_cases.build_weighted_items(filter_games)
        refresh_probabilities()

    build_activity_caches()

    def current_items_weights():
        if not include_games_var.get():
            return activity_lists["no_games"]
        if games_only_var.get():
            return activity_lists["games"]
        return activity_lists["all"]

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    suggest_logic = create_suggest_tab(
        root,
        notebook,
        tr,
        include_games_var,
        games_only_var,
        current_items_weights,
        is_steam_game_label,
        lambda name: show_game_popup(root, tr, name),
        build_activity_caches,
    )
    refresh_probabilities = suggest_logic.refresh_probabilities

    config_refresh = create_config_tab(
        root,
        notebook,
        tr,
        suggest_logic.w['prob_table'],
        is_steam_game_label,
        refresh_probabilities,
        lambda name: show_game_popup(root, tr, name),
        build_activity_caches,
    )

    def change_theme(value: str):
        apply_style(root, value)
        if suggest_logic.w['animation_canvas'] is not None:
            suggest_logic.w['animation_canvas'].configure(bg=get_color("surface"))
        if suggest_logic.final_canvas is not None:
            suggest_logic.final_canvas.configure(bg=get_color("surface"))
            suggest_logic.final_canvas.itemconfigure("final_text", fill=get_color("text"))
        suggest_logic.w['include_label'].config(foreground=get_color("contrast"))
        suggest_logic.w['games_only_label'].config(foreground=get_color("contrast"))
        suggest_logic.w['filter_label'].config(foreground=get_color("contrast"))
        refresh_probabilities()
        save_settings()

    def change_language(code: str):
        lang_var.set(code)
        rebuild_menus()
        refresh_probabilities()
        config_refresh()
        save_settings()

    menubar = tk.Menu(root)

    def rebuild_menus():
        menubar.delete(0, "end")
        theme_menu = tk.Menu(menubar, tearoff=0)
        for key in ("system", "light", "dark"):
            theme_menu.add_radiobutton(label=tr(f"theme_{key}"), variable=theme_var,
                                       value=key, command=lambda k=key: change_theme(k))
        menubar.add_cascade(label=tr("menu_theme"), menu=theme_menu)
        language_menu = tk.Menu(menubar, tearoff=0)
        for code, key in (("system", "lang_system"), ("es", "lang_spanish"), ("en", "lang_english")):
            language_menu.add_radiobutton(label=tr(key), value=code, variable=lang_var,
                                          command=lambda c=code: change_language(c))
        menubar.add_cascade(label=tr("menu_language"), menu=language_menu)
        menubar.add_command(label="Steam", command=lambda: import_steam_games(root, tr, build_activity_caches, config_refresh))
        root.config(menu=menubar)

    rebuild_menus()
    root.mainloop()
