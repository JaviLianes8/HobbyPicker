import webbrowser
from tkinter import messagebox, ttk
from presentation.steam_utils import (
    login_steam_id,
    fetch_steam_games,
    get_steam_appid,
    discover_steam_libraries,
    load_installed_games,
    get_local_appid,
)
from domain import use_cases
from presentation.widgets.styles import apply_style, add_button_hover
from presentation.utils.window_utils import WindowUtils
from presentation.i18n import STEAM_HOBBY_NAMES


def import_steam_games(root, tr, build_caches, refresh_list):
    if not messagebox.askyesno("Steam", tr("steam_import_confirm")):
        return
    steam_id = login_steam_id()
    if not steam_id:
        return
    try:
        games = fetch_steam_games(steam_id)
        if not games:
            raise ValueError
        hobby_id = use_cases.create_hobby(tr("steam_hobby_name"))
        existing = {s[2] for hid, _ in use_cases.get_all_hobbies() for s in use_cases.get_subitems_for_hobby(hid)}
        new_games = [g for g in games if g not in existing]
        for name in new_games:
            use_cases.add_subitem_to_hobby(hobby_id, name)
        build_caches()
        refresh_list()
        messagebox.showinfo("Steam", tr("steam_import_success").format(count=len(new_games)))
    except Exception:
        messagebox.showerror(tr("error"), tr("steam_import_error"))


def show_game_popup(root, tr, game_name):
    load_installed_games.cache_clear()
    appid = get_local_appid(game_name)
    installed = appid is not None
    if not installed:
        appid = get_steam_appid(game_name)
    if not appid:
        messagebox.showerror("Steam", tr("steam_not_found"))
        return
    dlg = ttk.Toplevel(root)
    apply_style(dlg)
    dlg.title("Steam")
    dlg.transient(root)
    dlg.grab_set()
    WindowUtils.center_window(dlg, 600, 130)
    ttk.Label(
        dlg,
        text=tr("steam_action_prompt").format(name=game_name),
        justify="center",
        anchor="center",
        wraplength=560,
    ).pack(padx=20, pady=15)

    def act():
        local_id = get_local_appid(game_name)
        if local_id:
            webbrowser.open(f"steam://rungameid/{local_id}")
        else:
            webbrowser.open(f"steam://rungameid/{appid}")
            webbrowser.open(f"steam://install/{appid}")
        dlg.destroy()

    btn = ttk.Button(
        dlg,
        text=tr("steam_play") if installed else tr("steam_install"),
        command=act,
        width=20,
    )
    btn.pack(pady=(0, 15))
    add_button_hover(btn)
