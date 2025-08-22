import json
import os
import random
import threading
import webbrowser
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs, quote
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
import tkinter as tk
from tkinter import messagebox, ttk
from functools import partial, lru_cache

from domain import use_cases
from presentation.widgets.styles import apply_style, get_color, add_button_hover
from presentation.utils.window_utils import WindowUtils
from presentation.utils.config_utils import load_settings, save_settings
from presentation.widgets.simple_entry_dialog import SimpleEntryDialog
from presentation.widgets.toggle_switch import ToggleSwitch
from presentation.utils import i18n




def start_app() -> None:
    """Launch the main HobbyPicker window."""
    root = tk.Tk()
    root.state("zoomed")
    WindowUtils.center_window(root, 1240, 600)
    root.title("HobbyPicker")
    root.minsize(1240, 600)

    settings = load_settings()

    lang_var = tk.StringVar(value=settings["language"])
    theme_var = tk.StringVar(value=settings["theme"])

    include_games_var = tk.BooleanVar(value=True)
    games_only_var = tk.BooleanVar(value=False)

    include_games_switch = None  # switch for including games
    games_only_switch = None  # switch for installed games only
    include_games_label = None
    games_only_label = None
    filter_label = None

    refresh_probabilities = None  # placeholder, defined after table creation

    def save_current_settings() -> None:
        save_settings({"language": lang_var.get(), "theme": theme_var.get()})

    apply_style(root, theme_var.get())

    # --- Soporte de idiomas ---
    def tr(key: str) -> str:
        return i18n.tr(lang_var.get(), key)

    is_steam_game_label = i18n.is_steam_game_label
    is_epic_game_label = i18n.is_epic_game_label

    def login_steam_id() -> str | None:
        result = {"id": None}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                params = parse_qs(urlparse(self.path).query)
                claimed = params.get("openid.claimed_id", [None])[0]
                if claimed:
                    result["id"] = claimed.rsplit("/", 1)[-1]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Login successful. You may close this window.")
                else:
                    self.send_response(400)
                    self.end_headers()
                threading.Thread(target=httpd.shutdown).start()

            def log_message(self, format, *args):
                pass

        httpd = HTTPServer(("localhost", 5000), Handler)
        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()
        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": "http://localhost:5000/",
            "openid.realm": "http://localhost:5000/",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
        webbrowser.open("https://steamcommunity.com/openid/login?" + urlencode(params))
        thread.join(timeout=30)
        if thread.is_alive():
            httpd.shutdown()
            thread.join()
        httpd.server_close()
        return result["id"]

    def import_steam_games() -> None:
        if not messagebox.askyesno("Steam", tr("steam_import_confirm")):
            return
        steam_id = login_steam_id()
        if not steam_id:
            messagebox.showerror("Steam", tr("steam_import_error"))
            return
        try:
            url = f"https://steamcommunity.com/profiles/{steam_id}/games?tab=all&xml=1"
            data = requests.get(url, timeout=10).content
            root_xml = ET.fromstring(data)
            games = []
            for g in root_xml.findall("./games/game"):
                name = g.findtext("name")
                appid = g.findtext("appID")
                if not name or not appid:
                    continue
                if get_steam_app_type(int(appid)) == "dlc":
                    continue
                games.append(name)
            games = list(dict.fromkeys(games))  # eliminate duplicates while preserving order
            if not games:
                raise ValueError
            hobby_id = use_cases.create_hobby(tr("steam_hobby_name"))
            all_existing = {
                s[2]
                for hid, _ in use_cases.get_all_hobbies()
                for s in use_cases.get_subitems_for_hobby(hid)
            }
            new_games = [g for g in games if g not in all_existing]
            for name in new_games:
                use_cases.add_subitem_to_hobby(hobby_id, name)
            build_activity_caches()
            refresh_listbox()
            messagebox.showinfo("Steam", tr("steam_import_success").format(count=len(new_games)))
        except Exception:
            messagebox.showerror(tr("error"), tr("steam_import_error"))

    def import_epic_games() -> None:
        if not messagebox.askyesno("Epic Games", tr("epic_import_confirm")):
            return
        try:
            games: list[str] = []
            games.extend(fetch_epic_library())
            for path in discover_epic_manifests():
                for manifest in path.glob("*.item"):
                    try:
                        data = json.loads(manifest.read_text(encoding="utf-8", errors="ignore"))
                        name = data.get("DisplayName")
                        if name:
                            games.append(name)
                    except Exception:
                        pass
            for path in discover_epic_catalogs():
                for cache in path.glob("*.json"):
                    try:
                        data = json.loads(cache.read_text(encoding="utf-8", errors="ignore"))
                        name = data.get("displayName") or data.get("DisplayName") or data.get("title")
                        if name:
                            games.append(name)
                    except Exception:
                        pass
            games = list(dict.fromkeys(games))
            if not games:
                raise ValueError
            hobby_id = use_cases.create_hobby(tr("epic_hobby_name"))
            all_existing = {
                s[2]
                for hid, _ in use_cases.get_all_hobbies()
                for s in use_cases.get_subitems_for_hobby(hid)
            }
            new_games = [g for g in games if g not in all_existing]
            for name in new_games:
                use_cases.add_subitem_to_hobby(hobby_id, name)
            build_activity_caches()
            refresh_listbox()
            messagebox.showinfo(
                "Epic Games",
                tr("epic_import_success").format(count=len(new_games)),
            )
        except Exception:
            messagebox.showerror(tr("error"), tr("epic_import_error"))

    @lru_cache(maxsize=None)
    def get_steam_appid(game_name: str) -> int | None:
        try:
            resp = requests.get(
                "https://steamcommunity.com/actions/SearchApps/" + quote(game_name),
                timeout=5,
            )
            data = resp.json()
            return int(data[0]["appid"]) if data else None
        except Exception:
            return None

    @lru_cache(maxsize=None)
    def get_steam_app_type(appid: int) -> str | None:
        try:
            resp = requests.get(
                f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic",
                timeout=5,
            )
            data = resp.json()
            info = data.get(str(appid), {})
            if info.get("success"):
                return info.get("data", {}).get("type")
        except Exception:
            pass
        return None

    @lru_cache(maxsize=1)
    def discover_steam_libraries() -> list[Path]:
        paths: list[Path] = []
        candidate_roots: list[Path] = []
        if os.name == "nt":
            pf_x86 = os.environ.get("PROGRAMFILES(X86)")
            pf = os.environ.get("PROGRAMFILES")
            if pf_x86:
                candidate_roots.append(Path(pf_x86) / "Steam")
            if pf:
                candidate_roots.append(Path(pf) / "Steam")
            for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                base = Path(f"{letter}:/")
                candidate_roots.extend(
                    [
                        base / "Steam",
                        base / "SteamLibrary",
                        base / "Program Files/Steam",
                        base / "Program Files (x86)/Steam",
                    ]
                )
        else:
            candidate_roots.extend(
                [
                    Path.home() / ".steam/steam",
                    Path.home() / ".local/share/Steam",
                    Path.home() / "Library/Application Support/Steam",
                ]
            )
        for root in candidate_roots:
            steamapps = root / "steamapps"
            if steamapps.exists():
                paths.append(steamapps)
                vdf = steamapps / "libraryfolders.vdf"
                if vdf.exists():
                    try:
                        text = vdf.read_text(encoding="utf-8", errors="ignore")
                        for folder in re.findall(r'"path"\s*"([^"]+)"', text):
                            lib_path = Path(folder).expanduser()
                            candidate = lib_path / "steamapps"
                            if candidate.exists():
                                paths.append(candidate)
                    except Exception:
                        pass
        unique: list[Path] = []
        for p in paths:
            resolved = p.resolve()
            if resolved not in unique:
                unique.append(resolved)
        return unique

    def _normalize_game_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", name.lower())

    @lru_cache(maxsize=1)
    def load_installed_games() -> dict[str, int]:
        games: dict[str, int] = {}
        for path in discover_steam_libraries():
            for manifest in path.glob("appmanifest_*.acf"):
                try:
                    text = manifest.read_text(encoding="utf-8", errors="ignore")
                    appid_match = re.search(r'"appid"\s*"(\d+)"', text)
                    name_match = re.search(r'"name"\s*"([^\"]+)"', text)
                    if appid_match and name_match:
                        games[_normalize_game_name(name_match.group(1))] = int(
                            appid_match.group(1)
                        )
                except Exception:
                    pass
        return games

    def get_local_appid(game_name: str) -> int | None:
        return load_installed_games().get(_normalize_game_name(game_name))

    @lru_cache(maxsize=1)
    def discover_epic_manifests() -> list[Path]:
        paths: list[Path] = []
        candidate_roots: list[Path] = []
        if os.name == "nt":
            pd = os.environ.get("PROGRAMDATA")
            if pd:
                candidate_roots.append(Path(pd) / "Epic/EpicGamesLauncher/Data/Manifests")
        else:
            candidate_roots.extend(
                [
                    Path.home() / ".local/share/EpicGamesLauncher/Data/Manifests",
                    Path.home() / "Library/Application Support/Epic/EpicGamesLauncher/Data/Manifests",
                ]
            )
        for root in candidate_roots:
            if root.exists():
                paths.append(root)
        return paths

    @lru_cache(maxsize=1)
    def discover_epic_catalogs() -> list[Path]:
        paths: list[Path] = []
        candidate_roots: list[Path] = []
        if os.name == "nt":
            pd = os.environ.get("PROGRAMDATA")
            if pd:
                candidate_roots.append(Path(pd) / "Epic/EpicGamesLauncher/Data/CatalogCache")
        else:
            candidate_roots.extend(
                [
                    Path.home() / ".local/share/EpicGamesLauncher/Data/CatalogCache",
                    Path.home() / "Library/Application Support/Epic/EpicGamesLauncher/Data/CatalogCache",
                ]
            )
        for root in candidate_roots:
            if root.exists():
                paths.append(root)
        return paths

    @lru_cache(maxsize=1)
    def fetch_epic_library() -> list[str]:
        token = os.environ.get("EPIC_AUTH_TOKEN")
        if not token:
            return []
        try:
            resp = requests.get(
                "https://library-launcher-service-prod06.ol.epicgames.com/library/api/public/library",
                headers={"Authorization": f"bearer {token}"},
                timeout=5,
            )
            data = resp.json()
            return [e.get("title") for e in data.get("records", []) if e.get("title")]
        except Exception:
            return []

    @lru_cache(maxsize=1)
    def load_epic_installed_games() -> dict[str, str]:
        games: dict[str, str] = {}
        for path in discover_epic_manifests():
            for manifest in path.glob("*.item"):
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8", errors="ignore"))
                    display = data.get("DisplayName")
                    appname = data.get("AppName")
                    if display and appname:
                        games[_normalize_game_name(display)] = appname
                except Exception:
                    pass
        return games

    def get_epic_appname(game_name: str) -> str | None:
        return load_epic_installed_games().get(_normalize_game_name(game_name))

    def show_epic_game_popup(game_name: str) -> None:
        load_epic_installed_games.cache_clear()
        installed = get_epic_appname(game_name) is not None
        dlg = tk.Toplevel(root)
        apply_style(dlg)
        dlg.title("Epic Games")
        dlg.transient(root)
        dlg.grab_set()
        WindowUtils.center_window(dlg, 600, 130)
        ttk.Label(
            dlg,
            text=tr("epic_action_prompt").format(name=game_name),
            justify="center",
            anchor="center",
            wraplength=560,
        ).pack(padx=20, pady=15)

        def act() -> None:
            local_app = get_epic_appname(game_name)
            if local_app:
                webbrowser.open(
                    f"com.epicgames.launcher://apps/{local_app}?action=launch"
                )
            else:
                webbrowser.open(
                    "https://store.epicgames.com/en-US/browse?q=" + quote(game_name)
                )
            dlg.destroy()

        btn = ttk.Button(
            dlg,
            text=tr("epic_play") if installed else tr("epic_install"),
            command=act,
            width=20,
        )
        btn.pack(pady=(0, 15))
        add_button_hover(btn)

    def show_game_popup(game_name: str) -> None:
        load_installed_games.cache_clear()
        appid = get_local_appid(game_name)
        installed = appid is not None
        if not installed:
            appid = get_steam_appid(game_name)
        if not appid:
            messagebox.showerror("Steam", tr("steam_not_found"))
            return
        dlg = tk.Toplevel(root)
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

        def act() -> None:
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
    activity_lists = {}

    def build_activity_caches() -> None:
        """Cache weighted activity lists for quick toggle switches."""
        discover_steam_libraries.cache_clear()
        load_installed_games.cache_clear()
        discover_epic_manifests.cache_clear()
        load_epic_installed_games.cache_clear()
        discover_steam_libraries()
        load_installed_games()
        discover_epic_manifests()
        load_epic_installed_games()
        def filter_no_games(item):
            _, label, is_sub, _ = item
            return not (
                is_sub
                and (is_steam_game_label(label) or is_epic_game_label(label))
            )

        activity_lists["all"] = use_cases.build_weighted_items()
        activity_lists["no_games"] = use_cases.build_weighted_items(filter_no_games)
        def filter_games(item):
            _, label, is_sub, _ = item
            return is_sub and (
                is_steam_game_label(label) or is_epic_game_label(label)
            )

        activity_lists["games"] = use_cases.build_weighted_items(filter_games)
        if refresh_probabilities:
            refresh_probabilities()

    build_activity_caches()

    def current_items_weights():
        if not include_games_var.get():
            return activity_lists["no_games"]
        if games_only_var.get():
            return activity_lists["games"]
        return activity_lists["all"]

    canvas = None  # se asigna más tarde
    separator = None  # línea divisoria asignada después
    animation_canvas = None  # zona de animación para las sugerencias
    final_canvas = None  # capa final a pantalla completa
    button_container = None  # contenedor de botones inferior
    overlay_buttons = []  # referencias a botones del overlay
    final_timeout_id = None

    # --- Notebook principal ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Menús de tema e idioma ---

    def change_theme_to(value: str) -> None:
        apply_style(root, value)
        if canvas is not None:
            canvas.configure(bg=get_color("surface"))
        if animation_canvas is not None:
            animation_canvas.configure(bg=get_color("surface"))
        if final_canvas is not None:
            final_canvas.configure(bg=get_color("surface"))
            final_canvas.itemconfigure("final_text", fill=get_color("text"))
        if include_games_switch is not None:
            include_games_switch.redraw()
        if games_only_switch is not None:
            games_only_switch.redraw()
        if include_games_label is not None:
            include_games_label.config(foreground=get_color("contrast"))
        if games_only_label is not None:
            games_only_label.config(foreground=get_color("contrast"))
        if refresh_probabilities:
            refresh_probabilities()
        save_current_settings()

    menubar = tk.Menu(root)

    def change_language(code: str) -> None:
        lang_var.set(code)
        update_texts()
        save_current_settings()

    def rebuild_menus() -> None:
        menubar.delete(0, "end")
        theme_menu = tk.Menu(menubar, tearoff=0)
        for key in ("system", "light", "dark"):
            theme_menu.add_radiobutton(
                label=tr(f"theme_{key}"),
                variable=theme_var,
                value=key,
                command=lambda k=key: change_theme_to(k),
            )
        menubar.add_cascade(label=tr("menu_theme"), menu=theme_menu)

        language_menu = tk.Menu(menubar, tearoff=0)
        for code, key in (("system", "lang_system"), ("es", "lang_spanish"), ("en", "lang_english")):
            language_menu.add_radiobutton(
                label=tr(key), value=code, variable=lang_var,
                command=lambda c=code: change_language(c)
            )
        menubar.add_cascade(label=tr("menu_language"), menu=language_menu)
        menubar.add_command(label="Steam", command=import_steam_games)
        menubar.add_command(label="Epic Games", command=import_epic_games)
        root.config(menu=menubar)

    def update_texts() -> None:
        notebook.tab(0, text=tr("tab_today"))
        notebook.tab(1, text=tr("tab_config"))
        suggestion_label.config(text=tr("prompt"))
        suggest_btn.config(text=tr("suggest_button"))
        add_hobby_btn.config(text=tr("add_hobby"))
        prob_table.heading("activity", text=tr("col_activity"))
        prob_table.heading("percent", text=tr("col_percent"))
        prob_table.heading("info", text="ⓘ")
        prob_table.heading("play", text="🎮")
        prob_table.heading("delete", text="🗑")
        rebuild_menus()
        if include_games_label is not None:
            include_games_label.config(
                text=tr("include_games"), foreground=get_color("contrast")
            )
        if games_only_label is not None:
            games_only_label.config(
                text=tr("games_only"), foreground=get_color("contrast")
            )
        if filter_label is not None:
            filter_label.config(text=tr("filter"), foreground=get_color("contrast"))
        if final_canvas is not None and overlay_buttons:
            final_canvas.itemconfigure(
                "final_text", text=tr("what_about").format(current_activity["name"])
            )
            for btn, key in overlay_buttons:
                btn.config(text=tr(key))

    rebuild_menus()
    change_theme_to(theme_var.get())

    # --- Pestaña: ¿Qué hago hoy? ---
    frame_suggest = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame_suggest, text=tr("tab_today"))

    frame_suggest.columnconfigure(0, weight=1)
    frame_suggest.columnconfigure(1, weight=0)
    frame_suggest.columnconfigure(2, weight=0)
    frame_suggest.rowconfigure(0, weight=1)

    content_frame = ttk.Frame(frame_suggest, style="Surface.TFrame")
    content_frame.grid(row=0, column=0, sticky="nsew")

    separator = ttk.Separator(frame_suggest, orient="vertical")
    separator.grid(row=0, column=1, sticky="ns", padx=5)

    table_frame = ttk.Frame(frame_suggest, style="Surface.TFrame", width=740)
    table_frame.grid(row=0, column=2, sticky="nsew", padx=10)
    table_frame.grid_propagate(False)
    table_frame.rowconfigure(1, weight=1)
    table_frame.columnconfigure(0, weight=1)

    filter_row = ttk.Frame(table_frame, style="Surface.TFrame")
    filter_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
    filter_row.columnconfigure(1, weight=1)
    filter_label = ttk.Label(
        filter_row,
        text=tr("filter"),
        style="Surface.TLabel",
        foreground=get_color("contrast"),
    )
    filter_label.grid(row=0, column=0, padx=(0, 5))
    filter_var = tk.StringVar()
    filter_entry = ttk.Entry(filter_row, textvariable=filter_var)
    filter_entry.grid(row=0, column=1, sticky="ew")

    prob_table = ttk.Treeview(
        table_frame,
        columns=("activity", "percent", "info", "play", "delete"),
        show="headings",
        style="Probability.Treeview",
    )
    prob_table.heading("activity", text=tr("col_activity"), anchor="w")
    prob_table.heading("percent", text=tr("col_percent"), anchor="center")
    prob_table.heading("info", text="ⓘ", anchor="center")
    prob_table.heading("play", text="🎮", anchor="center")
    prob_table.heading("delete", text="🗑", anchor="center")
    prob_table.column("activity", width=480, anchor="w")
    prob_table.column("percent", width=120, anchor="center")
    prob_table.column("info", width=40, anchor="center")
    prob_table.column("play", width=40, anchor="center")
    prob_table.column("delete", width=40, anchor="center")

    v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=prob_table.yview)
    prob_table.configure(yscrollcommand=v_scroll.set)

    prob_table.grid(row=1, column=0, sticky="nsew")
    v_scroll.grid(row=1, column=1, sticky="ns")

    def refresh_probabilities():
        for row in prob_table.get_children():
            prob_table.delete(row)
        prob_table.tag_configure(
            "even", background=get_color("surface"), foreground=get_color("text")
        )
        prob_table.tag_configure(
            "odd", background=get_color("light"), foreground=get_color("text")
        )
        items, weights = current_items_weights()
        if not items:
            return
        total_weight = sum(weights)
        filter_text = filter_var.get().lower()
        i = 0
        for (item_id, name, is_sub), weight in zip(items, weights):
            if filter_text and filter_text not in name.lower():
                continue
            tag = "even" if i % 2 == 0 else "odd"
            prob = weight / total_weight
            iid = f"{'s' if is_sub else 'h'}{item_id}"
            game_icon = (
                "🎮"
                if is_sub
                and (is_steam_game_label(name) or is_epic_game_label(name))
                else ""
            )
            prob_table.insert(
                "",
                "end",
                iid=iid,
                values=(name, f"{prob*100:.1f}%", "ⓘ", game_icon, "🗑"),
                tags=(tag,),
            )
            i += 1

    refresh_probabilities()

    filter_var.trace_add("write", lambda *_: refresh_probabilities())

    def on_toggle_update():
        nonlocal games_only_switch
        if games_only_var.get():
            include_games_var.set(True)
        if not include_games_var.get():
            games_only_var.set(False)
            if games_only_switch is not None:
                games_only_switch.state(["disabled"])
        else:
            if games_only_switch is not None:
                games_only_switch.state(["!disabled"])
        refresh_probabilities()

    toggle_container = ttk.Frame(content_frame, style="Surface.TFrame")
    toggle_container.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

    include_row = ttk.Frame(toggle_container, style="Surface.TFrame")
    include_row.pack(anchor="e", pady=2)
    include_games_label = ttk.Label(
        include_row,
        text=tr("include_games"),
        style="Surface.TLabel",
        foreground=get_color("contrast"),
    )
    include_games_label.pack(side="left", padx=(0, 5))
    include_games_switch = ToggleSwitch(
        include_row, variable=include_games_var, command=on_toggle_update
    )
    include_games_switch.pack(side="left")

    only_row = ttk.Frame(toggle_container, style="Surface.TFrame")
    only_row.pack(anchor="e", pady=2)
    games_only_label = ttk.Label(
        only_row,
        text=tr("games_only"),
        style="Surface.TLabel",
        foreground=get_color("contrast"),
    )
    games_only_label.pack(side="left", padx=(0, 5))
    games_only_switch = ToggleSwitch(
        only_row, variable=games_only_var, command=on_toggle_update
    )
    games_only_switch.pack(side="left")

    on_toggle_update()

    suggestion_label = ttk.Label(
        content_frame,
        text=tr("prompt"),
        font=("Segoe UI", 28, "bold"),
        wraplength=500,
        justify="center",
        style="Surface.TLabel",
    )
    suggestion_label.pack(pady=20, expand=True)

    animation_canvas = tk.Canvas(
        content_frame,
        width=1620,
        height=220,
        bg=get_color("surface"),
        highlightthickness=0,
    )

    current_activity = {"id": None, "name": None, "is_subitem": False}

    def revert_to_idle() -> None:
        nonlocal final_canvas, final_timeout_id
        if final_canvas is not None:
            final_canvas.destroy()
            final_canvas = None
            if separator is not None:
                separator.grid()
            if table_frame is not None:
                table_frame.grid()
            button_container.pack(side="bottom", fill="x", pady=20)
        overlay_buttons.clear()
        suggest_btn.state(["!disabled"])
        suggestion_label.config(text=tr("prompt"))
        suggestion_label.pack(pady=20, expand=True)
        toggle_container.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
        final_timeout_id = None

    def show_final_activity(text: str) -> None:
        nonlocal final_canvas, final_timeout_id
        if final_timeout_id is not None:
            root.after_cancel(final_timeout_id)
            final_timeout_id = None
        if final_canvas is not None:
            final_canvas.destroy()

        final_canvas = tk.Canvas(frame_suggest, bg=get_color("surface"), highlightthickness=0)
        final_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        final_canvas.update_idletasks()

        if separator is not None:
            separator.grid_remove()
        if table_frame is not None:
            table_frame.grid_remove()
        # Oculta la botonera base, NO la metas en el canvas
        button_container.pack_forget()

        cx = final_canvas.winfo_width() / 2
        cy = final_canvas.winfo_height() / 2
        max_width = final_canvas.winfo_width() * 0.9

        text_item = final_canvas.create_text(
            cx,
            cy,
            text=text,
            width=max_width,
            fill=get_color("text"),
            font=("Segoe UI", 28, "bold"),
            tags=("final_text",),
            justify="center",
            anchor="center",
        )

        # >>> NUEVO: crear botonera específica de overlay <<<
        overlay_buttons = make_overlay_buttons(final_canvas)
        button_window = final_canvas.create_window(
            cx, final_canvas.winfo_height() - 20, window=overlay_buttons, anchor="s"
        )

        def on_resize(event=None):
            nonlocal max_width
            max_width = final_canvas.winfo_width() * 0.9
            final_canvas.itemconfigure(text_item, width=max_width)
            final_canvas.coords(
                text_item,
                final_canvas.winfo_width() / 2,
                final_canvas.winfo_height() / 2,
            )
            final_canvas.coords(
                button_window,
                final_canvas.winfo_width() / 2,
                final_canvas.winfo_height() - 20,
            )

        final_canvas.bind("<Configure>", on_resize)

        def launch_confetti():
            width = final_canvas.winfo_width()
            height = final_canvas.winfo_height()
            colors = ["#FF5E5E","#FFD700","#5EFF5E","#5E5EFF","#FF5EFF","#FFA500"]

            def create_piece():
                x = random.randint(0, width)
                size = random.randint(5, 12)
                color = random.choice(colors)
                piece = final_canvas.create_rectangle(x, -size, x+size, 0, fill=color, outline="")
                dy = random.uniform(3, 6)
                def fall():
                    final_canvas.move(piece, 0, dy)
                    if final_canvas.coords(piece)[3] < height:
                        final_canvas.after(30, fall)
                    else:
                        final_canvas.delete(piece)
                fall()

            for i in range(80):
                final_canvas.after(i*20, create_piece)

        launch_confetti()
        final_timeout_id = root.after(8000, revert_to_idle)

    def suggest():
        nonlocal final_canvas, final_timeout_id
        for btn, _ in overlay_buttons:
            btn.state(["disabled"])
        suggest_btn.state(["disabled"])
        toggle_container.place_forget()
        if final_timeout_id is not None:
            root.after_cancel(final_timeout_id)
            final_timeout_id = None
        if final_canvas is not None:
            final_canvas.destroy()
            final_canvas = None
            if separator is not None:
                separator.grid()
            if table_frame is not None:
                table_frame.grid()
            button_container.pack(side="bottom", fill="x", pady=20)
        items, weights = current_items_weights()
        result = random.choices(items, weights=weights, k=1)[0] if items else None
        if not result:
            suggestion_label.config(
                text=tr("no_hobbies")
            )
            suggestion_label.pack(pady=20, expand=True)
            toggle_container.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
            return

        final_id, final_text, is_sub = result
        current_activity["id"] = final_id
        current_activity["name"] = final_text
        current_activity["is_subitem"] = is_sub

        options = []
        for _ in range(20):
            if items:
                alt = random.choices(items, weights=weights, k=1)[0]
                options.append(alt[1])
        options += [final_text, ""]

        animation_canvas.delete("all")
        box_w, box_h = 540, 180
        #box_colors = ["#FFEBEE", "#E3F2FD", "#E8F5E9", "#FFF3E0", "#F3E5F5"]
        for i, text in enumerate(options):
            x = i * box_w
            #color = random.choice(box_colors)
            animation_canvas.create_rectangle(
                x,
                0,
                x + box_w,
                box_h,
                fill=get_color("light"),
                outline="",
                tags=("item",),
            )
            animation_canvas.create_text(
                x + box_w / 2,
                box_h / 2,
                text=text,
                width=box_w - 20,
                fill=get_color("text"),
                font=("Segoe UI", 32, "bold"),
                tags=("item",),
            )
        animation_canvas.create_rectangle(
            box_w,
            0,
            box_w * 2,
            box_h,
            outline=get_color("primary"),
            width=3,
        )

        suggestion_label.pack_forget()
        animation_canvas.pack(pady=20, before=button_container)

        total_shift = (len(options) - 3) * box_w

        def roll(step=0, speed=10):
            if step < total_shift:
                animation_canvas.move("item", -speed, 0)
                step += speed
                if step < total_shift * 0.6:
                    speed = min(speed + 2, 80)
                elif total_shift - step < box_w * 2:
                    speed = max(speed - 3, 5)
                root.after(20, lambda: roll(step, speed))
            else:
                animation_canvas.move("item", -(total_shift - step), 0)
                animation_canvas.after(200, finish)

        def finish():
            animation_canvas.pack_forget()
            show_final_activity(tr("what_about").format(final_text))
            # habilitar acciones en la capa final
            for btn, key in overlay_buttons:
                if key in ("like_overlay", "another_button"):
                    btn.state(["!disabled"])
        
        roll()

    def accept():
        nonlocal final_canvas, final_timeout_id
        if current_activity["id"]:
            is_steam_game = (
                current_activity["is_subitem"]
                and current_activity["name"]
                and is_steam_game_label(current_activity["name"])
            )
            is_epic_game = (
                current_activity["is_subitem"]
                and current_activity["name"]
                and is_epic_game_label(current_activity["name"])
            )
            is_game = is_steam_game or is_epic_game
            game_name = (
                current_activity["name"].split(" + ", 1)[1]
                if is_game
                else ""
            )
            use_cases.mark_activity_as_done(
                current_activity["id"], current_activity["is_subitem"]
            )
            build_activity_caches()
            if is_game:
                if is_steam_game:
                    show_game_popup(game_name)
                else:
                    show_epic_game_popup(game_name)
            current_activity["id"] = None
            current_activity["name"] = None
            current_activity["is_subitem"] = False
            suggestion_label.config(text=tr("prompt"))
            suggestion_label.pack(pady=20, expand=True)
            toggle_container.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
            if final_timeout_id is not None:
                root.after_cancel(final_timeout_id)
                final_timeout_id = None
            if final_canvas is not None:
                final_canvas.destroy()
                final_canvas = None
                if separator is not None:
                    separator.grid()
                if table_frame is not None:
                    table_frame.grid()
                button_container.pack(side="bottom", fill="x", pady=20)
            overlay_buttons.clear()
            suggest_btn.state(["!disabled"])
            refresh_probabilities()

    def make_overlay_buttons(parent):
        """Botonera específica para la capa final (parent debe ser final_canvas)."""
        nonlocal overlay_buttons
        overlay_buttons = []
        overlay = ttk.Frame(parent, style="Surface.TFrame")
        btn1 = ttk.Button(
            overlay, text=tr("another_button"), command=suggest, style="Big.TButton", width=20
        )
        btn1.pack(side="left", padx=8, pady=10)
        add_button_hover(btn1)
        btn1.state(["disabled"])  # deshabilitado mientras dura la animación
        overlay_buttons.append((btn1, "another_button"))
        btn2 = ttk.Button(
            overlay, text=tr("like_overlay"), command=accept, style="Big.TButton", width=20
        )
        btn2.pack(side="left", padx=8, pady=10)
        add_button_hover(btn2)
        overlay_buttons.append((btn2, "like_overlay"))
        return overlay

    button_container = ttk.Frame(content_frame, style="Surface.TFrame")
    button_container.pack(side="bottom", fill="x", pady=20)

    suggest_btn = ttk.Button(
        button_container,
        text=tr("suggest_button"),
        command=suggest,
        style="Big.TButton",
        width=20,
    )
    suggest_btn.pack(pady=10)
    add_button_hover(suggest_btn)

    def on_tab_change(event):
        if notebook.index("current") == 0:
            refresh_probabilities()

    notebook.bind("<<NotebookTabChanged>>", on_tab_change)

    # --- Pestaña: Configurar hobbies ---
    frame_config = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame_config, text=tr("tab_config"))

    main_config_layout = ttk.Frame(frame_config, style="Surface.TFrame")
    main_config_layout.pack(fill="both", expand=True)

    canvas = tk.Canvas(
        main_config_layout, bg=get_color("surface"), highlightthickness=0
    )
    scrollbar = ttk.Scrollbar(
        main_config_layout, orient="vertical", command=canvas.yview
    )
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = ttk.Frame(canvas, style="Surface.TFrame")

    def update_scrollregion(e=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig("inner_frame", width=canvas.winfo_width())

    scrollable_frame.bind("<Configure>", update_scrollregion)
    canvas.bind("<Configure>", update_scrollregion)

    canvas.create_window(
        (0, 0), window=scrollable_frame, anchor="nw", tags="inner_frame"
    )

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    add_hobby_btn = ttk.Button(
        main_config_layout,
        text=tr("add_hobby"),
        command=lambda: open_add_hobby_window(),
    )
    add_hobby_btn.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)

    update_texts()

    hobbies_container = scrollable_frame

    def refresh_listbox():
        for widget in hobbies_container.winfo_children():
            widget.destroy()
        for hobby in use_cases.get_all_hobbies():
            row = ttk.Frame(
                hobbies_container, style="Outlined.Surface.TFrame", padding=5
            )
            row.pack(fill="x", pady=4, padx=10)

            row.columnconfigure(0, weight=1)
            row.columnconfigure(1, weight=0)

            label = ttk.Label(
                row, text=hobby[1], anchor="center", style="Heading.Surface.TLabel"
            )
            label.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

            button_frame = ttk.Frame(row, style="Surface.TFrame")
            button_frame.grid(row=0, column=1, sticky="e", padx=10, pady=8)

            ttk.Button(
                button_frame,
                text="ⓘ",
                command=partial(open_edit_hobby_window, hobby[0], hobby[1]),
            ).pack(side="left", padx=2)

            ttk.Button(
                button_frame,
                text="🗑",
                command=partial(confirm_delete_hobby, hobby[0], hobby[1]),
            ).pack(side="left", padx=2)

    def confirm_delete_hobby(hobby_id, hobby_name):
        if messagebox.askyesno(
            tr("delete"), tr("delete_hobby_confirm").format(name=hobby_name)
        ):
            use_cases.delete_hobby(hobby_id)
            refresh_listbox()
            build_activity_caches()
            messagebox.showinfo(tr("deleted"), tr("hobby_deleted").format(name=hobby_name))

    def on_prob_table_click(event):
        region = prob_table.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = prob_table.identify_column(event.x)
        row_id = prob_table.identify_row(event.y)
        if not row_id:
            return
        name = prob_table.item(row_id, "values")[0]
        if column == "#5":
            if row_id.startswith("h"):
                confirm_delete_hobby(int(row_id[1:]), name)
            elif row_id.startswith("s"):
                if messagebox.askyesno(
                    tr("delete"), tr("delete_subitem_confirm").format(name=name)
                ):
                    use_cases.delete_subitem(int(row_id[1:]))
                    build_activity_caches()
                    refresh_probabilities()
        elif column == "#3":
            if row_id.startswith("h"):
                open_edit_hobby_window(int(row_id[1:]), name)
            elif row_id.startswith("s"):
                new_name = SimpleEntryDialog.ask(
                    parent=root,
                    title=tr("edit_subitem_title"),
                    prompt=tr("new_name_prompt").format(name=name),
                    initial_value=name,
                )
                if new_name:
                    use_cases.update_subitem(int(row_id[1:]), new_name.strip())
                    build_activity_caches()
                    refresh_probabilities()
        elif column == "#4":
            if row_id.startswith("s"):
                game_name = name.split(" + ", 1)[1]
                if is_steam_game_label(name):
                    show_game_popup(game_name)
                elif is_epic_game_label(name):
                    show_epic_game_popup(game_name)

    prob_table.bind("<Button-1>", on_prob_table_click)

    def on_prob_table_double_click(event):
        region = prob_table.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = prob_table.identify_column(event.x)
        if column != "#1":
            return
        row_id = prob_table.identify_row(event.y)
        if not row_id:
            return
        name = prob_table.item(row_id, "values")[0]
        if row_id.startswith("s") and is_steam_game_label(name):
            game_name = name.split(" + ", 1)[1]
            appid = get_local_appid(game_name)
            if appid is None:
                appid = get_steam_appid(game_name)
            if appid:
                webbrowser.open(f"https://store.steampowered.com/app/{appid}/")
            else:
                messagebox.showerror("Steam", tr("steam_not_found"))
        elif row_id.startswith("s") and is_epic_game_label(name):
            game_name = name.split(" + ", 1)[1]
            webbrowser.open(
                "https://store.epicgames.com/en-US/browse?q=" + quote(game_name)
            )

    prob_table.bind("<Double-1>", on_prob_table_double_click)

    def open_edit_hobby_window(hobby_id, hobby_name):
        edit_window = tk.Toplevel()
        apply_style(edit_window)
        edit_window.title(tr("edit_subitems_title").format(name=hobby_name))
        WindowUtils.center_window(edit_window, 600, 600)
        edit_window.minsize(600, 600)
        items_canvas = tk.Canvas(
            edit_window, bg=get_color("surface"), highlightthickness=0
        )
        items_scroll = ttk.Scrollbar(
            edit_window, orient="vertical", command=items_canvas.yview
        )
        items_canvas.configure(yscrollcommand=items_scroll.set)
        items_canvas.pack(side="left", fill="both", expand=True, pady=5)
        items_scroll.pack(side="right", fill="y")
        items_frame = ttk.Frame(items_canvas, style="Surface.TFrame")
        items_canvas.create_window((0, 0), window=items_frame, anchor="nw", tags="inner_frame")

        def update_items_scroll(e=None):
            items_canvas.configure(scrollregion=items_canvas.bbox("all"))
            items_canvas.itemconfig("inner_frame", width=items_canvas.winfo_width())

        items_frame.bind("<Configure>", update_items_scroll)
        items_canvas.bind("<Configure>", update_items_scroll)

        def refresh_items():
            for w in items_frame.winfo_children():
                w.destroy()
            for item in use_cases.get_subitems_for_hobby(hobby_id):
                row = ttk.Frame(
                    items_frame, style="Outlined.Surface.TFrame", padding=5
                )
                row.pack(fill="x", pady=2, padx=10)

                label = ttk.Label(row, text=item[2], anchor="w", style="Surface.TLabel")
                label.pack(side="left", expand=True)

                def edit_subitem(subitem_id=item[0], current_name=item[2]):
                    new_name = SimpleEntryDialog.ask(
                        parent=edit_window,
                        title=tr("edit_subitem_title"),
                        prompt=tr("new_name_prompt").format(name=current_name),
                        initial_value=current_name,
                    )
                    if new_name and new_name.strip() != current_name:
                        use_cases.update_subitem(subitem_id, new_name.strip())
                        refresh_items()
                        build_activity_caches()

                ttk.Button(
                    row,
                    text="🗑",
                    width=3,
                    command=lambda: delete_item(item[0], item[2]),
                ).pack(side="right", padx=2)
                ttk.Button(
                    row, text="ⓘ", width=3, command=edit_subitem
                ).pack(side="right")

        def delete_item(item_id, name):
            if messagebox.askyesno(
                tr("delete"), tr("delete_subitem_confirm").format(name=name)
            ):
                use_cases.delete_subitem(item_id)
                refresh_items()
                build_activity_caches()

        def add_subitem():
            new_item = SimpleEntryDialog.ask(
                parent=edit_window,
                title=tr("new_subitem_title"),
                prompt=tr("new_subitem_prompt"),
            )
            if new_item:
                use_cases.add_subitem_to_hobby(hobby_id, new_item.strip())
                refresh_items()
                build_activity_caches()

        btn_add_sub = ttk.Button(
            edit_window, text=tr("add_subitem_btn"), command=add_subitem
        )
        btn_add_sub.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)
        refresh_items()

    def open_add_hobby_window():
        add_window = tk.Toplevel(root)
        apply_style(add_window)
        add_window.title(tr("add_hobby_window_title"))

        ttk.Label(add_window, text=tr("hobby_title_label")).pack(pady=5)
        hobby_entry = ttk.Entry(add_window, width=40)
        hobby_entry.pack(pady=5)
        hobby_entry.focus()

        ttk.Label(add_window, text=tr("subitems_label")).pack(pady=(10, 0))
        subitems_container = ttk.Frame(add_window)
        subitems_container.pack(fill="both", expand=False)

        subitems_canvas = tk.Canvas(
            subitems_container, bg=get_color("surface"), highlightthickness=0
        )
        subitems_scroll = ttk.Scrollbar(
            subitems_container, orient="vertical", command=subitems_canvas.yview
        )
        subitems_canvas.configure(yscrollcommand=subitems_scroll.set, height=150)
        subitems_canvas.pack(side="left", fill="both", expand=True)
        subitems_scroll.pack(side="right", fill="y")
        subitems_frame = ttk.Frame(subitems_canvas, style="Surface.TFrame")
        subitems_canvas.create_window(
            (0, 0), window=subitems_frame, anchor="nw", tags="inner_frame"
        )

        def update_subitems_scroll(e=None):
            subitems_canvas.configure(scrollregion=subitems_canvas.bbox("all"))
            subitems_canvas.itemconfig(
                "inner_frame", width=subitems_canvas.winfo_width()
            )

        subitems_frame.bind("<Configure>", update_subitems_scroll)
        subitems_canvas.bind("<Configure>", update_subitems_scroll)

        subitem_entries: list[ttk.Entry] = []

        def add_subitem_field() -> None:
            container = ttk.Frame(subitems_frame)
            entry = ttk.Entry(container, width=40)

            def remove_entry() -> None:
                container.destroy()
                subitem_entries.remove(entry)
                update_subitems_scroll()

            ttk.Button(container, text="🗑", width=3, command=remove_entry).pack(
                side="right", padx=5
            )
            entry.pack(side="left", fill="x", expand=True, pady=2)
            container.pack(fill="x", pady=2)
            subitem_entries.append(entry)
            update_subitems_scroll()

        add_subitem_field()

        def save_hobby() -> None:
            name = hobby_entry.get().strip()
            if not name:
                messagebox.showerror(tr("error"), tr("need_title"))
                return
            hobby_id = use_cases.create_hobby(name)
            for entry in subitem_entries:
                sub = entry.get().strip()
                if sub:
                    use_cases.add_subitem_to_hobby(hobby_id, sub)
            build_activity_caches()
            add_window.destroy()
            refresh_listbox()

        ttk.Button(
            add_window, text=tr("add_subitem_btn"), command=add_subitem_field
        ).pack(pady=(0, 10))
        ttk.Button(add_window, text=tr("save"), command=save_hobby).pack(pady=10)

        WindowUtils.center_window(add_window, 500, 400)
        add_window.resizable(False, False)
        add_window.minsize(500, 400)
        add_window.maxsize(500, 400)

    refresh_listbox()
    root.mainloop()
